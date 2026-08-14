#!/usr/bin/env python3
"""Export a deterministic, public-safe snapshot of the live Canvas course.

Canvas remains the instructional delivery system. This snapshot is the release
record used by the public GitHub Pages mirror and the parity verifier.
"""

from __future__ import annotations

import concurrent.futures
import datetime as dt
import hashlib
import html
import json
import re
import shutil
import unicodedata
from pathlib import Path

from canvas_api import Canvas, env_course_id, stable_json


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
ASSETS = ROOT / "assets" / "canvas"
SNAPSHOT = DATA / "course-snapshot.json"
POLICY_PATH = DATA / "publication-policy.json"
COURSE_ID = env_course_id()
FILE_ID_RE = re.compile(
    r"(?:/files/|files%2[fF]|/api/v1/courses/\d+/files/|/media_attachments_iframe/)(\d+)", re.I
)


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_text(value: str) -> str:
    return sha256_bytes(value.encode("utf-8"))


def canonical_hash(value) -> str:
    return sha256_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def public_filename(file_id: int, name: str) -> str:
    normalized = unicodedata.normalize("NFKD", name or f"file-{file_id}")
    ascii_name = normalized.encode("ascii", "ignore").decode("ascii")
    safe = re.sub(r"[^A-Za-z0-9._-]+", "-", ascii_name).strip(".-")
    return f"{file_id}-{safe or 'resource'}"


def exact_projection(row: dict, keys: tuple[str, ...]) -> dict:
    return {key: row.get(key) for key in keys}


def referenced_file_ids(body: str) -> list[int]:
    decoded = html.unescape(body or "")
    return sorted({int(value) for value in FILE_ID_RE.findall(decoded)})


def assignment_projection(row: dict) -> dict:
    route = row.get("external_tool_tag_attributes") or {}
    rubric = row.get("rubric") or []
    rubric_settings = row.get("rubric_settings") or {}
    return {
        **exact_projection(
            row,
            (
                "id",
                "name",
                "published",
                "points_possible",
                "assignment_group_id",
                "grading_type",
                "submission_types",
                "omit_from_final_grade",
                "allowed_extensions",
                "allowed_attempts",
                "peer_reviews",
                "automatic_peer_reviews",
                "anonymous_peer_reviews",
                "due_at",
                "unlock_at",
                "lock_at",
            ),
        ),
        "external_tool": {
            "domain": re.sub(r"^https?://([^/]+).*$", r"\1", route.get("url") or ""),
            "url_sha256": sha256_text(route.get("url") or "") if route else None,
            "new_tab": route.get("new_tab") if route else None,
        },
        "rubric_settings": rubric_settings,
        "rubric": rubric,
    }


def page_projection(row: dict) -> dict:
    return exact_projection(
        row,
        (
            "page_id",
            "url",
            "title",
            "published",
            "hide_from_students",
            "editing_roles",
            "front_page",
            "todo_date",
            "publish_at",
            "locked_for_user",
        ),
    )


def discussion_projection(row: dict) -> dict:
    return exact_projection(
        row,
        (
            "id",
            "title",
            "published",
            "discussion_type",
            "require_initial_post",
            "pinned",
            "locked",
            "locked_for_user",
            "assignment_id",
        ),
    )


def quiz_projection(row: dict) -> dict:
    return exact_projection(
        row,
        (
            "id",
            "title",
            "published",
            "quiz_type",
            "points_possible",
            "question_count",
            "allowed_attempts",
            "time_limit",
            "shuffle_answers",
            "one_question_at_a_time",
            "cant_go_back",
            "due_at",
            "unlock_at",
            "lock_at",
        ),
    )


def question_projection(row: dict) -> dict:
    answers = row.get("answers") or []
    answer_contract = [
        {
            "id": str(answer.get("id")) if answer.get("id") is not None else None,
            "weight": answer.get("weight"),
            "text_sha256": sha256_text(answer.get("text") or ""),
            "html_sha256": sha256_text(answer.get("html") or ""),
        }
        for answer in answers
    ]
    return {
        "id": row.get("id"),
        "position": row.get("position"),
        "question_type": row.get("question_type"),
        "points_possible": row.get("points_possible"),
        "question_name": row.get("question_name"),
        "question_text_sha256": sha256_text(row.get("question_text") or ""),
        "answers_sha256": canonical_hash(answer_contract),
        "answer_count": len(answer_contract),
    }


def resource_for(canvas: Canvas, item: dict) -> dict:
    kind = item.get("type")
    if kind == "Page":
        row = canvas.get(f"/courses/{COURSE_ID}/pages/{item['page_url']}")
        return {"kind": "page", "metadata": page_projection(row), "body": row.get("body") or ""}
    if kind == "Assignment":
        row = canvas.get(
            f"/courses/{COURSE_ID}/assignments/{item['content_id']}?include[]=rubric&include[]=rubric_settings"
        )
        return {
            "kind": "assignment",
            "metadata": assignment_projection(row),
            "body": row.get("description") or "",
        }
    if kind == "Discussion":
        row = canvas.get(f"/courses/{COURSE_ID}/discussion_topics/{item['content_id']}")
        return {
            "kind": "discussion",
            "metadata": discussion_projection(row),
            "body": row.get("message") or "",
        }
    if kind == "Quiz":
        row = canvas.get(f"/courses/{COURSE_ID}/quizzes/{item['content_id']}")
        questions = canvas.paged(
            f"/courses/{COURSE_ID}/quizzes/{item['content_id']}/questions?per_page=100"
        )
        return {
            "kind": "quiz",
            "metadata": quiz_projection(row),
            "body": row.get("description") or "",
            "question_contract": [question_projection(question) for question in questions],
        }
    return {"kind": kind.lower() if kind else "unknown", "metadata": {}, "body": ""}


def module_projection(row: dict) -> dict:
    return exact_projection(
        row,
        (
            "id",
            "name",
            "position",
            "published",
            "require_sequential_progress",
            "prerequisite_module_ids",
            "unlock_at",
        ),
    )


def item_projection(row: dict) -> dict:
    return exact_projection(
        row,
        (
            "id",
            "position",
            "indent",
            "type",
            "title",
            "published",
            "content_id",
            "page_url",
            "external_url",
            "new_tab",
            "completion_requirement",
        ),
    )


def file_metadata(row: dict, folder: dict | None) -> dict:
    return {
        **exact_projection(
            row,
            (
                "id",
                "display_name",
                "filename",
                "content-type",
                "size",
                "folder_id",
                "hidden",
                "locked",
                "modified_at",
                "created_at",
            ),
        ),
        "folder_full_name": (folder or {}).get("full_name"),
    }


def main() -> None:
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    if policy.get("course_id") != COURSE_ID:
        raise RuntimeError("publication-policy.json targets a different Canvas course")
    protected = {int(row["module_item_id"]): row for row in policy.get("protected_items", [])}
    file_aliases = {
        int(file_id): int(value["source_file_id"])
        for file_id, value in policy.get("file_download_aliases", {}).items()
    }

    canvas = Canvas()
    course = canvas.get(f"/courses/{COURSE_ID}")
    raw_modules = sorted(
        canvas.paged(f"/courses/{COURSE_ID}/modules?per_page=100"),
        key=lambda row: (row.get("position") or 0, row["id"]),
    )
    module_items: dict[int, list[dict]] = {}
    all_items: list[dict] = []
    for module in raw_modules:
        rows = sorted(
            canvas.paged(f"/courses/{COURSE_ID}/modules/{module['id']}/items?per_page=100"),
            key=lambda row: (row.get("position") or 0, row["id"]),
        )
        module_items[module["id"]] = rows
        all_items.extend(rows)

    body_items = [
        item for item in all_items if item.get("type") in {"Page", "Assignment", "Discussion", "Quiz"}
    ]
    resources: dict[int, dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(resource_for, canvas, item): item for item in body_items}
        for future in concurrent.futures.as_completed(futures):
            item = futures[future]
            resources[item["id"]] = future.result()

    protected_file_ids: set[int] = set()
    all_file_ids: set[int] = set()
    for item in body_items:
        resource = resources[item["id"]]
        body = resource.get("body") or ""
        ids = set(referenced_file_ids(body))
        all_file_ids.update(ids)
        if item["id"] in protected:
            expected = set(int(value) for value in protected[item["id"]].get("expected_file_ids", []))
            if ids != expected:
                raise RuntimeError(
                    f"Protected item {item['id']} references {sorted(ids)}, expected {sorted(expected)}. "
                    "Update publication-policy.json before exporting so no protected asset leaks."
                )
            protected_file_ids.update(ids)
            resource["private_body_sha256"] = sha256_text(body)
            resource["private_body_length"] = len(body)
            resource["body"] = ""
            resource["public_notice"] = protected[item["id"]]["public_notice"]
            resource["protection_reason"] = protected[item["id"]]["reason"]
        else:
            resource["body_sha256"] = sha256_text(body)
            resource["referenced_file_ids"] = sorted(ids)

    public_file_ids = sorted(all_file_ids - protected_file_ids)
    previous = {}
    if SNAPSHOT.exists():
        previous = json.loads(SNAPSHOT.read_text(encoding="utf-8")).get("files", {})

    metadata_rows: dict[int, dict] = {}
    raw_file_rows: dict[int, dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(canvas.get, f"/files/{file_id}"): file_id for file_id in public_file_ids}
        for future in concurrent.futures.as_completed(futures):
            file_id = futures[future]
            raw_file_rows[file_id] = future.result()

    alias_source_rows: dict[int, dict] = {}
    for target_id, source_id in file_aliases.items():
        if target_id not in raw_file_rows:
            raise RuntimeError(f"Download alias target {target_id} is not referenced by public content")
        source = canvas.get(f"/files/{source_id}")
        target = raw_file_rows[target_id]
        identity_keys = ("filename", "size", "content-type")
        if any(source.get(key) != target.get(key) for key in identity_keys):
            raise RuntimeError(
                f"Download alias {target_id}->{source_id} does not match filename, size, and MIME type"
            )
        alias_source_rows[target_id] = source

    folder_ids = sorted({row.get("folder_id") for row in raw_file_rows.values() if row.get("folder_id")})
    folders: dict[int, dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        futures = {pool.submit(canvas.get, f"/folders/{folder_id}"): folder_id for folder_id in folder_ids}
        for future in concurrent.futures.as_completed(futures):
            folders[futures[future]] = future.result()

    ASSETS.mkdir(parents=True, exist_ok=True)
    expected_asset_paths: set[Path] = set()

    def download_one(file_id: int) -> tuple[int, dict]:
        row = raw_file_rows[file_id]
        download_row = alias_source_rows.get(file_id, row)
        name = row.get("display_name") or row.get("filename") or f"file-{file_id}"
        relative = Path("assets") / "canvas" / public_filename(file_id, name)
        target = ROOT / relative
        expected_asset_paths.add(target)
        prior = previous.get(str(file_id)) or {}
        same_remote_identity = (
            target.exists()
            and target.stat().st_size == (row.get("size") or 0)
            and prior.get("metadata", {}).get("modified_at") == row.get("modified_at")
            and prior.get("sha256")
        )
        if same_remote_identity:
            digest = sha256_bytes(target.read_bytes())
            if digest != prior["sha256"]:
                same_remote_identity = False
        if not same_remote_identity:
            payload = canvas.download(download_row["url"])
            if len(payload) != (row.get("size") or len(payload)):
                raise RuntimeError(f"File {file_id} size mismatch after download")
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(payload)
        digest = sha256_bytes(target.read_bytes())
        metadata = file_metadata(row, folders.get(row.get("folder_id")))
        return file_id, {
            "metadata": metadata,
            "sha256": digest,
            "public_path": relative.as_posix(),
            "download_source_file_id": download_row["id"],
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=6) as pool:
        futures = {pool.submit(download_one, file_id): file_id for file_id in public_file_ids}
        for future in concurrent.futures.as_completed(futures):
            file_id, result = future.result()
            metadata_rows[file_id] = result
            print(f"asset {len(metadata_rows):3}/{len(public_file_ids)}  {file_id}  {result['public_path']}")

    # Remove only stale generated Canvas assets. Hand-authored site assets live elsewhere.
    for path in ASSETS.iterdir():
        if path.is_file() and path not in expected_asset_paths:
            path.unlink()

    modules = []
    for module in raw_modules:
        items = []
        for raw_item in module_items[module["id"]]:
            item = item_projection(raw_item)
            item["public_state"] = "protected" if raw_item["id"] in protected else "public"
            if raw_item["id"] in resources:
                item["resource"] = resources[raw_item["id"]]
            items.append(item)
        modules.append({**module_projection(module), "items": items})

    snapshot = {
        "schema_version": 1,
        "generated_at": dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat(),
        "source": {
            "canvas_host": "https://verizoninnovativelearning.instructure.com",
            "course_id": COURSE_ID,
        },
        "course": exact_projection(
            course,
            ("id", "name", "course_code", "workflow_state", "start_at", "end_at"),
        ),
        "publication_policy": policy,
        "modules": modules,
        "files": {str(file_id): metadata_rows[file_id] for file_id in sorted(metadata_rows)},
        "protected_file_ids": sorted(protected_file_ids),
    }
    semantic = {key: value for key, value in snapshot.items() if key != "generated_at"}
    snapshot["semantic_sha256"] = canonical_hash(semantic)
    DATA.mkdir(parents=True, exist_ok=True)
    SNAPSHOT.write_text(stable_json(snapshot), encoding="utf-8")
    print(
        stable_json(
            {
                "snapshot": str(SNAPSHOT),
                "semantic_sha256": snapshot["semantic_sha256"],
                "modules": len(modules),
                "items": sum(len(module["items"]) for module in modules),
                "public_files": len(metadata_rows),
                "protected_files": sorted(protected_file_ids),
                "public_file_bytes": sum(row["metadata"]["size"] or 0 for row in metadata_rows.values()),
            }
        )
    )


if __name__ == "__main__":
    main()
