#!/usr/bin/env python3
"""Install the August 19 VILS release into a current Irving template lineage.

The existing 391 imported objects keep their Irving IDs.  The 112 new lesson
guides are marked as manual bridge objects because Canvas's public API cannot
assign Commons migration identifiers. Defaults target Duncan; CLI arguments
allow another audited course and an explicit local-content manifest.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import re
import subprocess
from collections import defaultdict
from pathlib import Path

import requests

from canvas_api import Canvas, stable_json


IRVING_API = "https://learn.irvingisd.net/api/v1"
IRVING_WEB = "https://learn.irvingisd.net/courses/97806"
VERIZON_API = "https://verizoninnovativelearning.instructure.com/api/v1/courses/23402"
VERIZON_WEB = "https://verizoninnovativelearning.instructure.com/courses/23402"
COURSE_ID = 97806
CURRENT_IMPORT_MIN = 545000
MAP_PATH = Path("artifacts/duncan-current-release-map-2026-08-19.json")
LOCAL_MANIFEST: dict | None = None


def is_local_item(item: dict) -> bool:
    if not LOCAL_MANIFEST:
        return False
    return bool(
        (item["type"] == "SubHeader" and item["title"].startswith("ROSS · LOCAL"))
        or (item["type"] == "Page" and item["title"].startswith("ROSS COPY ·"))
        or item.get("content_id") in set(LOCAL_MANIFEST.get("protected_assignment_ids", []))
        or item.get("page_url") in set(LOCAL_MANIFEST.get("protected_page_urls", []))
    )


def snapshot_at(revision: str) -> dict:
    return json.loads(
        subprocess.check_output(
            ["git", "show", f"{revision}:data/course-snapshot.json"], text=True
        )
    )


def item_signature(items: list[dict]) -> list[tuple[str, str]]:
    return [(item["type"], item["title"]) for item in items]


def live_current(canvas: Canvas) -> tuple[dict[str, dict], dict[int, list[dict]]]:
    modules = [
        module
        for module in canvas.paged(f"/courses/{COURSE_ID}/modules?per_page=100")
        if module["id"] >= CURRENT_IMPORT_MIN
    ]
    assert len(modules) == 34, (
        "Expected one 34-module current lineage; "
        f"found {len(modules)}. Refusing to write into a partial or duplicate import."
    )
    items = {
        module["id"]: canvas.paged(
            f"/courses/{COURSE_ID}/modules/{module['id']}/items?per_page=100"
        )
        for module in modules
    }
    return {module["name"]: module for module in modules}, items


def baseline_mapping(
    baseline: dict, modules: dict[str, dict], items: dict[int, list[dict]]
) -> dict[int, dict]:
    mapping: dict[int, dict] = {}
    assert set(modules) == {module["name"] for module in baseline["modules"]}
    for source_module in baseline["modules"]:
        dest_module = modules[source_module["name"]]
        source_items = source_module["items"]
        dest_items = [
            item for item in items[dest_module["id"]] if not is_local_item(item)
        ]
        assert item_signature(source_items) == item_signature(dest_items), (
            f"Baseline drift in {source_module['name']}; refusing to infer item identity."
        )
        for source_item, dest_item in zip(source_items, dest_items):
            mapping[source_item["id"]] = dest_item
    assert len(mapping) == 391
    return mapping


def changed_shared_items(current: dict, baseline_by_id: dict[int, dict]) -> list[dict]:
    changed = []
    for module in current["modules"]:
        for item in module["items"]:
            old = baseline_by_id.get(item["id"])
            if not old:
                continue
            old_hash = (old.get("resource") or {}).get("body_sha256")
            new_hash = (item.get("resource") or {}).get("body_sha256")
            if item["title"] != old["title"] or old_hash != new_hash:
                changed.append(item)
    return changed


def required_files(items: list[dict]) -> set[int]:
    result: set[int] = set()
    for item in items:
        result.update((item.get("resource") or {}).get("referenced_file_ids") or [])
    return result


def upload_file(
    canvas: Canvas, source_file: dict, folder_id: int, local_path: Path
) -> dict:
    content_type = source_file.get("content-type") or mimetypes.guess_type(
        source_file["filename"]
    )[0] or "application/octet-stream"
    init, _ = canvas.request(
        "POST",
        f"/courses/{COURSE_ID}/files",
        {
            "name": source_file["filename"],
            "size": local_path.stat().st_size,
            "content_type": content_type,
            "parent_folder_id": folder_id,
            "on_duplicate": "overwrite",
        },
    )
    with local_path.open("rb") as handle:
        response = requests.post(
            init["upload_url"],
            data=init["upload_params"],
            files={"file": (source_file["filename"], handle, content_type)},
            timeout=300,
            allow_redirects=True,
        )
    response.raise_for_status()
    payload = response.json()
    if isinstance(payload, list):
        payload = payload[0]
    assert payload.get("id"), f"Canvas upload did not return a file id: {payload}"
    return payload


def file_mapping(canvas: Canvas, current: dict, source_file_ids: set[int], apply: bool) -> dict[int, int]:
    source_files = {
        int(source_id): entry
        for source_id, entry in current["files"].items()
        if int(source_id) in source_file_ids
    }
    dest_files = canvas.paged(f"/courses/{COURSE_ID}/files?per_page=100")
    folders = canvas.paged(f"/courses/{COURSE_ID}/folders?per_page=100")
    folder_names = {folder["id"]: folder.get("full_name") for folder in folders}
    folder_ids = {folder.get("full_name"): folder["id"] for folder in folders}
    candidates: dict[tuple[str, int, str], list[dict]] = defaultdict(list)
    for dest in dest_files:
        if (dest.get("created_at") or "") < "2026-08-10":
            continue
        key = (
            dest.get("filename"),
            dest.get("size"),
            folder_names.get(dest.get("folder_id")),
        )
        candidates[key].append(dest)

    result: dict[int, int] = {}
    pending_by_asset: dict[tuple[str, int, str], list[int]] = defaultdict(list)
    for source_id, entry in source_files.items():
        metadata = entry["metadata"]
        key = (
            metadata.get("filename"),
            metadata.get("size"),
            metadata.get("folder_full_name"),
        )
        matches = candidates.get(key, [])
        if matches:
            result[source_id] = max(
                matches, key=lambda value: value.get("created_at") or ""
            )["id"]
        else:
            pending_by_asset[key].append(source_id)

    for key, source_ids in pending_by_asset.items():
        first = source_files[source_ids[0]]
        metadata = first["metadata"]
        local_path = Path(first["public_path"])
        assert local_path.exists() and local_path.stat().st_size == metadata["size"]
        folder_id = folder_ids.get(metadata.get("folder_full_name"))
        assert folder_id, f"Missing destination folder {metadata.get('folder_full_name')}"
        if not apply:
            print(
                "DRY upload",
                metadata["filename"],
                metadata["size"],
                "to",
                metadata.get("folder_full_name"),
            )
            continue
        uploaded = upload_file(canvas, metadata, folder_id, local_path)
        for source_id in source_ids:
            result[source_id] = uploaded["id"]
    if apply:
        assert set(result) == source_file_ids
    return result


def replace_content_links(
    body: str, source_items: dict[int, dict], dest_items: dict[int, dict], files: dict[int, int]
) -> str:
    rewritten = body
    for source_id, dest in dest_items.items():
        rewritten = rewritten.replace(
            f"{VERIZON_WEB}/modules/items/{source_id}",
            f"{IRVING_WEB}/modules/items/{dest['id']}",
        )
        source = source_items[source_id]
        if source["type"] == "Page" and source.get("page_url") and dest.get("page_url"):
            rewritten = rewritten.replace(
                f"{VERIZON_WEB}/pages/{source['page_url']}",
                f"{IRVING_WEB}/pages/{dest['page_url']}",
            )
            rewritten = rewritten.replace(
                f"{VERIZON_API}/pages/{source['page_url']}",
                f"{IRVING_API}/courses/{COURSE_ID}/pages/{dest['page_url']}",
            )
        elif source.get("content_id") and dest.get("content_id"):
            segment = {
                "Assignment": "assignments",
                "Quiz": "quizzes",
                "Discussion": "discussion_topics",
            }.get(source["type"])
            if segment:
                rewritten = rewritten.replace(
                    f"{VERIZON_WEB}/{segment}/{source['content_id']}",
                    f"{IRVING_WEB}/{segment}/{dest['content_id']}",
                )
                rewritten = rewritten.replace(
                    f"{VERIZON_API}/{segment}/{source['content_id']}",
                    f"{IRVING_API}/courses/{COURSE_ID}/{segment}/{dest['content_id']}",
                )
    for source_id, dest_id in files.items():
        rewritten = re.sub(
            rf"{re.escape(VERIZON_WEB)}/files/{source_id}(?:/download)?(?:\?[^\"']*)?",
            f"{IRVING_WEB}/files/{dest_id}?wrap=1",
            rewritten,
        )
        rewritten = rewritten.replace(
            f"{VERIZON_API}/files/{source_id}",
            f"{IRVING_API}/courses/{COURSE_ID}/files/{dest_id}",
        )
    rewritten = rewritten.replace(VERIZON_WEB, IRVING_WEB)
    rewritten = rewritten.replace(
        VERIZON_API, f"{IRVING_API}/courses/{COURSE_ID}"
    )
    assert "verizoninnovativelearning.instructure.com/courses/23402" not in rewritten
    return rewritten


def manual_bridge_body(source_item: dict, body: str) -> str:
    marker = (
        f'<div data-vils-manual-bridge="2026-08-19" '
        f'data-vils-source-module-item="{source_item["id"]}" '
        'style="display:none;" aria-hidden="true"></div>'
    )
    return marker + body


def source_index(snapshot: dict) -> tuple[dict[int, dict], dict[str, dict]]:
    by_id = {}
    modules = {}
    for module in snapshot["modules"]:
        modules[module["name"]] = module
        for item in module["items"]:
            by_id[item["id"]] = item
    return by_id, modules


def main() -> None:
    global COURSE_ID, CURRENT_IMPORT_MIN, IRVING_WEB, MAP_PATH, LOCAL_MANIFEST
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--course-id", type=int, default=COURSE_ID)
    parser.add_argument("--current-import-min", type=int, default=CURRENT_IMPORT_MIN)
    parser.add_argument("--map-path", default=str(MAP_PATH))
    parser.add_argument("--local-manifest")
    args = parser.parse_args()

    COURSE_ID = args.course_id
    CURRENT_IMPORT_MIN = args.current_import_min
    IRVING_WEB = f"https://learn.irvingisd.net/courses/{COURSE_ID}"
    MAP_PATH = Path(args.map_path)
    LOCAL_MANIFEST = (
        json.loads(Path(args.local_manifest).read_text(encoding="utf-8"))
        if args.local_manifest
        else None
    )

    current = json.loads(Path("data/course-snapshot.json").read_text(encoding="utf-8"))
    baseline = snapshot_at("6df20ff^")
    current_by_id, current_modules = source_index(current)
    baseline_by_id, _ = source_index(baseline)
    new_items = [
        item
        for module in current["modules"]
        for item in module["items"]
        if item["id"] not in baseline_by_id
    ]
    changed = changed_shared_items(current, baseline_by_id)
    assert len(new_items) == 112 and all(item["type"] == "Page" for item in new_items)
    assert len(changed) == 72 and all(item["type"] == "Page" for item in changed)

    canvas = Canvas(base=IRVING_API)
    modules, live_items = live_current(canvas)
    dest_by_source = baseline_mapping(baseline, modules, live_items)
    target_body_items = new_items + [
        item
        for item in changed
        if (item.get("resource") or {}).get("body_sha256")
        != (baseline_by_id[item["id"]].get("resource") or {}).get("body_sha256")
    ]
    file_ids = required_files(target_body_items)
    files = file_mapping(canvas, current, file_ids, args.apply)

    print("verified current lineage: 34 modules / 391 imported items")
    print("new manual bridge guides:", len(new_items))
    print("existing pages to rename/update:", len(changed))
    print("file links required:", sorted(file_ids))
    if not args.apply:
        print("DRY RUN complete; no Canvas changes made")
        return

    MAP_PATH.parent.mkdir(parents=True, exist_ok=True)
    manifest = {
        "course_id": COURSE_ID,
        "source_release": current["generated_at"],
        "commons_linkage_note": (
            "391 objects retain the August 10 Commons lineage. The 112 added guides "
            "are manual bridge objects and may need reconciliation after a future Commons update."
        ),
        "source_to_irving_module_items": {
            str(source_id): dest["id"] for source_id, dest in dest_by_source.items()
        },
        "source_to_irving_files": {str(source_id): dest_id for source_id, dest_id in files.items()},
    }
    MAP_PATH.write_text(stable_json(manifest), encoding="utf-8")

    # Insert guides in source order.  Each position is the final one-based position;
    # inserting in ascending order lets Canvas shift the remaining imported items.
    for source_module in current["modules"]:
        dest_module = modules[source_module["name"]]
        for source_item in source_module["items"]:
            if source_item["id"] in baseline_by_id:
                continue
            body = manual_bridge_body(
                source_item,
                replace_content_links(
                    source_item["resource"]["body"], current_by_id, dest_by_source, files
                ),
            )
            page, _ = canvas.request(
                "POST",
                f"/courses/{COURSE_ID}/pages",
                {
                    "wiki_page[title]": source_item["title"],
                    "wiki_page[body]": body,
                    "wiki_page[editing_roles]": "teachers",
                    "wiki_page[published]": False,
                },
            )
            module_item, _ = canvas.request(
                "POST",
                f"/courses/{COURSE_ID}/modules/{dest_module['id']}/items",
                {
                    "module_item[type]": "Page",
                    "module_item[page_url]": page["url"],
                    "module_item[position]": source_item["position"],
                    "module_item[published]": False,
                },
            )
            dest_by_source[source_item["id"]] = module_item
            manifest["source_to_irving_module_items"][str(source_item["id"])] = module_item["id"]
            MAP_PATH.write_text(stable_json(manifest), encoding="utf-8")

    # Rename the existing guide layer first. Canvas can update a page URL after
    # a title change, so body links must be rewritten in a second pass.
    for source_item in changed:
        dest = dest_by_source[source_item["id"]]
        canvas.request(
            "PUT",
            f"/courses/{COURSE_ID}/pages/{dest['page_url']}",
            {"wiki_page[title]": source_item["title"]},
        )

    refreshed_modules, refreshed_items = live_current(canvas)
    refreshed_by_id = {
        item["id"]: item for module_items in refreshed_items.values() for item in module_items
    }
    for source_id, previous_dest in list(dest_by_source.items()):
        dest_by_source[source_id] = refreshed_by_id[previous_dest["id"]]

    # Only eleven bodies changed after the August 17 Commons update. Title-only
    # changes retain their already translated Irving bodies.
    for source_item in changed:
        old = baseline_by_id[source_item["id"]]
        old_hash = (old.get("resource") or {}).get("body_sha256")
        new_hash = (source_item.get("resource") or {}).get("body_sha256")
        if old_hash != new_hash:
            dest = dest_by_source[source_item["id"]]
            body = replace_content_links(
                source_item["resource"]["body"], current_by_id, dest_by_source, files
            )
            canvas.request(
                "PUT",
                f"/courses/{COURSE_ID}/pages/{dest['page_url']}",
                {"wiki_page[body]": body},
            )

    # Existing items can also move between source releases. Reapply the exact
    # current sequence by immutable module-item identity before verification.
    for source_module in current["modules"]:
        dest_module = modules[source_module["name"]]
        expected_ids = [dest_by_source[item["id"]]["id"] for item in source_module["items"]]
        actual = canvas.paged(
            f"/courses/{COURSE_ID}/modules/{dest_module['id']}/items?per_page=100"
        )
        canonical_actual = [item for item in actual if not is_local_item(item)]
        assert set(expected_ids) == {item["id"] for item in canonical_actual}
        if expected_ids != [item["id"] for item in canonical_actual]:
            for position, item_id in enumerate(expected_ids, start=1):
                canvas.request(
                    "PUT",
                    f"/courses/{COURSE_ID}/modules/{dest_module['id']}/items/{item_id}",
                    {"module_item[position]": position},
                )

    # Verify exact current module order and all manual bridge markers.
    verify_modules, verify_items = live_current(canvas)
    assert set(verify_modules) == set(current_modules)
    for source_module in current["modules"]:
        dest_module = verify_modules[source_module["name"]]
        actual = [
            item for item in verify_items[dest_module["id"]] if not is_local_item(item)
        ]
        assert item_signature(actual) == item_signature(source_module["items"]), (
            f"Final signature mismatch in {source_module['name']}"
        )
    marker_count = 0
    for source_item in new_items:
        dest_item = dest_by_source[source_item["id"]]
        page = canvas.get(f"/courses/{COURSE_ID}/pages/{dest_item['page_url']}")
        assert page.get("published") is False
        assert 'data-vils-manual-bridge="2026-08-19"' in (page.get("body") or "")
        assert f'data-vils-source-module-item="{source_item["id"]}"' in page["body"]
        marker_count += 1
    assert marker_count == 112
    print("APPLIED: 112 guides added, 72 existing pages updated")
    print("VERIFIED: 34 current modules / 503 items / 112 manual guide markers")


if __name__ == "__main__":
    main()
