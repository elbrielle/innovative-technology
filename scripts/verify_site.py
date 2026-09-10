#!/usr/bin/env python3
"""Fail closed when the generated public mirror diverges from its Canvas snapshot."""

from __future__ import annotations

import hashlib
import html
import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

from build_site import build_maps, canonical_hash, sha256_text
from export_canvas import PageLinks, canvas_page_slug, referenced_file_ids


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "course-snapshot.json"
MANIFEST = ROOT / "data" / "site-manifest.json"
POLICY = ROOT / "data" / "publication-policy.json"
PUBLIC_LINKS = ROOT / "data" / "public-links.json"
LEGACY_ALIASES = ROOT / "data" / "legacy-route-aliases.json"
DAILY_CONTRACTS = ROOT / "data" / "daily-learning-contracts.json"
CANONICAL_TEKS = ROOT / "docs" / "standards" / "texas-technology-applications-grade-8-teks-2022.md"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


class LinkParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.links: list[tuple[str, str]] = []
        self.ids: set[str] = set()

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        values = dict(attrs)
        if values.get("id"):
            self.ids.add(values["id"] or "")
        for attr in ("href", "src"):
            if values.get(attr):
                self.links.append((attr, values[attr] or ""))


def semantic_snapshot_hash(snapshot: dict) -> str:
    semantic = {key: value for key, value in snapshot.items() if key not in {"generated_at", "semantic_sha256"}}
    return canonical_hash(semantic)


def plain_text(value: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def check_linked_pages(snapshot: dict, manifest: dict, public_links: dict, failures: list[str]) -> None:
    linked = snapshot.get("linked_pages", [])
    page_ids = [page["page_id"] for page in linked]
    module_items = [item for module in snapshot["modules"] for item in module["items"]]
    module_page_ids = {(item.get("resource") or {}).get("metadata", {}).get("page_id")
                       for item in module_items if item.get("type") == "Page"}
    if len(page_ids) != len(set(page_ids)) or set(page_ids) & module_page_ids:
        failures.append("Linked Canvas pages duplicate a page ID or a module page")
    public_files = {int(file_id) for file_id in snapshot["files"]}
    protected_files = set(snapshot.get("protected_file_ids", []))
    for page in linked:
        page_id = page["page_id"]
        resource = page["resource"]
        if not isinstance(page_id, int) or page_id <= 0 or resource["metadata"]["page_id"] != page_id:
            failures.append(f"Linked page has an invalid Canvas page identity: {page_id}")
        if page.get("public_state") != "public" or "private_body_sha256" in resource:
            failures.append(f"Protected content was included as a public linked page: {page_id}")
        if sha256_text(resource["body"]) != resource.get("body_sha256"):
            failures.append(f"Linked page body hash differs: {page_id}")
        ids = set(referenced_file_ids(resource["body"]))
        if sorted(ids) != resource.get("referenced_file_ids") or not ids <= public_files or ids & protected_files:
            failures.append(f"Linked page has missing or protected file dependencies: {page_id}")
        row = manifest.get("pages", {}).get(f"pages/{page_id}.html", {})
        if row.get("kind") != "linked_page" or row.get("canvas_id") != page_id or row.get("canvas_body_sha256") != resource.get("body_sha256"):
            failures.append(f"Linked page manifest does not match the snapshot: {page_id}")
    links = public_links.get("linked_pages", [])
    if len(links) != len(linked) or {row.get("page_id") for row in links} != set(page_ids):
        failures.append("Stable public-links.json does not account for all linked Canvas pages")
    for row in links:
        if not row.get("url", "").endswith(f"pages/{row['page_id']}.html"):
            failures.append(f"Linked page URL is not based on its Canvas page ID: {row['page_id']}")

    maps = build_maps(snapshot, snapshot["publication_policy"])
    known = set(maps["page"]) | set(maps["route_aliases"]) | set(maps["missing_route_notices"])
    for item in module_items + linked:
        if item.get("public_state") == "protected":
            continue
        parser = PageLinks()
        parser.feed((item.get("resource") or {}).get("body", ""))
        for url in parser.urls:
            slug = canvas_page_slug(url, maps["course_id"], maps["canvas_host"])
            if slug and slug not in known:
                failures.append(f"Snapshot is missing a referenced Canvas page: {slug}")


def check_local_link(source: Path, value: str, ids: set[str], failures: list[str]) -> None:
    parsed = urlparse(value)
    if parsed.scheme in {"http", "https", "mailto", "tel", "data", "blob"} or value.startswith("javascript:"):
        return
    if value == "#":
        failures.append(f"{source.relative_to(ROOT)} has an empty # link")
        return
    if value.startswith("#"):
        if unquote(value[1:]) not in ids:
            failures.append(f"{source.relative_to(ROOT)} points to missing fragment {value}")
        return
    target = (source.parent / unquote(parsed.path)).resolve()
    try:
        target.relative_to(ROOT)
    except ValueError:
        failures.append(f"{source.relative_to(ROOT)} escapes the site root: {value}")
        return
    if not target.exists():
        failures.append(f"{source.relative_to(ROOT)} points to missing local resource {value}")


def main() -> None:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    policy = json.loads(POLICY.read_text(encoding="utf-8"))
    public_links = json.loads(PUBLIC_LINKS.read_text(encoding="utf-8"))
    legacy_aliases = json.loads(LEGACY_ALIASES.read_text(encoding="utf-8"))
    daily_contracts = json.loads(DAILY_CONTRACTS.read_text(encoding="utf-8"))
    failures: list[str] = []

    expected_snapshot_hash = semantic_snapshot_hash(snapshot)
    if snapshot.get("semantic_sha256") != expected_snapshot_hash:
        failures.append("Canvas snapshot semantic hash is invalid")
    if snapshot.get("publication_policy") != policy:
        failures.append("Canvas snapshot was not exported with the current publication policy")
    if manifest.get("snapshot_sha256") != snapshot.get("semantic_sha256"):
        failures.append("Site manifest was not built from the current Canvas snapshot")
    if public_links.get("canvas_snapshot_sha256") != snapshot.get("semantic_sha256"):
        failures.append("Stable public-links.json was not built from the current Canvas snapshot")

    modules = snapshot["modules"]
    items = [item for module in modules for item in module["items"]]
    check_linked_pages(snapshot, manifest, public_links, failures)
    facilitator_guides = [
        item
        for item in items
        if re.match(r"^Facilitator(?:'s)? Guide:", item.get("title", ""), re.I)
    ]
    contract_rows = {
        int(row["module_item_id"]): row for row in daily_contracts.get("records", [])
    }
    guide_ids = {int(guide["id"]) for guide in facilitator_guides}
    if set(contract_rows) != guide_ids:
        failures.append("Daily learning contract ledger does not account for every facilitator guide")
    if daily_contracts.get("canonical_teks_sha256") != sha256_file(CANONICAL_TEKS):
        failures.append("Daily learning contract ledger was not audited against the current canonical TEKS record")
    contract_patterns = {
        "Topic": r"<strong>\s*Topic\s*:",
        "Objective": r"<strong>\s*(?:Student )?Objective\s*:",
        "TEKS": r"<strong>\s*(?:TEKS|Essential TEKS)\s*:",
        "Demonstration of learning": r"<strong>\s*(?:Demonstration of learning|Show Your Learning)\s*:",
    }
    for guide in facilitator_guides:
        body = (guide.get("resource") or {}).get("body") or ""
        text = plain_text(body)
        missing_fields = [
            name
            for name, pattern in contract_patterns.items()
            if not re.search(pattern, body, re.I)
        ]
        if missing_fields:
            failures.append(
                f"Facilitator guide {guide['id']} is missing its daily learning contract fields: "
                + ", ".join(missing_fields)
            )
        if body.count("Daily Learning Contract") != 1:
            failures.append(f"Facilitator guide {guide['id']} must contain exactly one daily learning contract")
        if 'data-vils-daily-learning-contract="2026-08-21-semantic-audit-v1"' not in body:
            failures.append(f"Facilitator guide {guide['id']} is not using the audited semantic contract version")
        if 'data-vils-teks-alignment="2026-08-19"' in body:
            failures.append(f"Facilitator guide {guide['id']} still contains a duplicate module-level alignment block")
        record = contract_rows.get(int(guide["id"]))
        if record:
            required_phrases = [
                record["topic"],
                record["objective"],
                record["demonstration_of_learning"],
                *record["teks"],
            ]
            for phrase in required_phrases:
                if phrase not in text:
                    failures.append(
                        f"Facilitator guide {guide['id']} differs from the audited contract ledger: {phrase}"
                    )
    stale_teks_guides = [
        guide["id"]
        for guide in facilitator_guides
        if "§127.2" in ((guide.get("resource") or {}).get("body") or "")
    ]
    if stale_teks_guides:
        failures.append(
            "Facilitator guides contain noncanonical legacy TEKS §127.2: "
            + ", ".join(map(str, stale_teks_guides))
        )
    expected_counts = {
        "modules": len(modules),
        "items": len(items),
        "item_pages": sum(item["type"] != "SubHeader" for item in items),
        "linked_pages": len(snapshot.get("linked_pages", [])),
        "public_files": len(snapshot["files"]),
        "protected_items": sum(item.get("public_state") == "protected" for item in items),
    }
    if manifest.get("counts") != expected_counts:
        failures.append(f"Manifest counts differ: {manifest.get('counts')} != {expected_counts}")
    protected_policy = policy.get("protected_items", [])
    if expected_counts["protected_items"] != 1 or len(protected_policy) != 1:
        failures.append("Publication policy must contain exactly one protected item")
    if protected_policy and int(protected_policy[0]["module_item_id"]) != 2633987:
        failures.append("The only protected item must be About Me Smartphone (2633987)")
    link_rows = public_links.get("items", [])
    if len(link_rows) != len(items) or {row.get("module_item_id") for row in link_rows} != {item["id"] for item in items}:
        failures.append("Stable public-links.json does not account for every Canvas module item")
    for row in link_rows:
        expected_suffix = f"lessons/{row['module_item_id']}.html" if row["type"] != "SubHeader" else f"modules/{row['module_id']}.html"
        if not row.get("url", "").endswith(expected_suffix):
            failures.append(f"Stable URL is not ID-based for item {row.get('module_item_id')}")

    expected_module_files = {f"modules/{module['id']}.html" for module in modules}
    expected_item_files = {f"lessons/{item['id']}.html" for item in items if item["type"] != "SubHeader"}
    expected_item_files.update(f"lessons/{filename}" for filename in legacy_aliases)
    actual_module_files = {path.relative_to(ROOT).as_posix() for path in (ROOT / "modules").glob("*.html")}
    actual_item_files = {path.relative_to(ROOT).as_posix() for path in (ROOT / "lessons").glob("*.html")}
    expected_linked_files = {f"pages/{page['page_id']}.html" for page in snapshot.get("linked_pages", [])}
    actual_linked_files = {path.relative_to(ROOT).as_posix() for path in (ROOT / "pages").glob("*.html")}
    if expected_linked_files != actual_linked_files:
        failures.append("Generated linked page set differs from Canvas")
    if expected_module_files != actual_module_files:
        failures.append("Generated module page set differs from Canvas")
    if expected_item_files != actual_item_files:
        failures.append("Generated lesson page set differs from Canvas")
    item_ids = {int(item["id"]) for item in items if item["type"] != "SubHeader"}
    for filename, target_item_id in legacy_aliases.items():
        if int(target_item_id) not in item_ids:
            failures.append(f"Legacy redirect {filename} targets missing lesson {target_item_id}")
        redirect = ROOT / "lessons" / filename
        if redirect.is_file() and f'href="{target_item_id}.html"' not in redirect.read_text(encoding="utf-8"):
            failures.append(f"Legacy redirect {filename} does not point to {target_item_id}.html")

    for relative, row in manifest.get("pages", {}).items():
        path = ROOT / relative
        if not path.is_file():
            failures.append(f"Missing generated page {relative}")
        elif sha256_file(path) != row["sha256"]:
            failures.append(f"Generated page hash differs for {relative}")

    for file_id, row in snapshot["files"].items():
        path = ROOT / row["public_path"]
        if not path.is_file():
            failures.append(f"Missing public Canvas file {file_id}: {row['public_path']}")
            continue
        if path.stat().st_size != row["metadata"]["size"]:
            failures.append(f"Public Canvas file size differs for {file_id}")
        if sha256_file(path) != row["sha256"]:
            failures.append(f"Public Canvas file hash differs for {file_id}")

    expected_assets = {row["public_path"] for row in snapshot["files"].values()}
    actual_assets = {
        path.relative_to(ROOT).as_posix()
        for path in (ROOT / "assets" / "canvas").iterdir()
        if path.is_file()
    }
    if expected_assets != actual_assets:
        failures.append("Generated Canvas asset set contains a missing or stale file")

    html_paths = [ROOT / "index.html", ROOT / "about.html", ROOT / "parity.html"] + sorted((ROOT / "modules").glob("*.html")) + sorted((ROOT / "lessons").glob("*.html")) + sorted((ROOT / "pages").glob("*.html"))
    canvas_route = re.compile(r"https?://verizoninnovativelearning\.instructure\.com/(?:api/v1/)?courses/23402/")
    forbidden_tokens = ["YOUR_BG_IMAGE_URL", "Link.Placeholder"]
    forbidden_editorial_phrases = [
        "Scope boundary:",
        "Download the reviewed",
        "outside the required sequence",
        "inherited sustainability",
        "points as shipped",
        "Publish states are mixed as shipped",
        "inherited from the source curriculum",
        "source lesson was",
        "(Elisha, Aug 2026)",
        "stock interactive version",
        "stock Articulate RISE interactive",
        "original Lesson 1",
        "parked as optional enrichment",
        "leave it parked",
        "Reconnect the imported Edpuzzle assignments",
        "belong to the source Canvas class",
        "ships unpublished",
        "ship unpublished",
        "owner scoring decision",
        "author’s placeholder",
        "public mirror",
        "pacing reality",
        "teacher craft",
        "public enough",
        "where it matters",
        "designed to empower",
        "meaningful journey",
        "not just a curriculum",
        "more than just a curriculum",
    ]
    for path in html_paths:
        text = path.read_text(encoding="utf-8")
        parser = LinkParser()
        parser.feed(text)
        for _, value in parser.links:
            check_local_link(path, value, parser.ids, failures)
        if canvas_route.search(text):
            failures.append(f"{path.relative_to(ROOT)} still contains a course-authenticated Canvas route")
        for token in forbidden_tokens:
            if token in text:
                failures.append(f"{path.relative_to(ROOT)} contains unresolved token {token}")
        for phrase in forbidden_editorial_phrases:
            if phrase.lower() in text.lower():
                failures.append(
                    f"{path.relative_to(ROOT)} contains internal editorial language: {phrase}"
                )

    protected_ids = {str(value) for value in snapshot.get("protected_file_ids", [])}
    asset_names = "\n".join(actual_assets)
    for protected_id in protected_ids:
        if protected_id in asset_names:
            failures.append(f"Protected file {protected_id} leaked into assets/canvas")
    protected_page = (ROOT / "lessons" / "2633987.html").read_text(encoding="utf-8")
    if "not available on the public site" not in protected_page or "canvas-content" in protected_page:
        failures.append("Protected About Me Phone page does not use the district-only public notice")

    if manifest.get("unresolved"):
        failures.append(f"Site manifest has unresolved routes: {manifest['unresolved']}")
    if failures:
        print(json.dumps({"status": "FAIL", "failures": failures}, indent=2))
        raise SystemExit(1)
    print(json.dumps({"status": "PASS", "checks": {**expected_counts, "facilitator_guides_with_daily_contracts": len(facilitator_guides), "html_pages": len(html_paths), "public_file_bytes": sum(row['metadata']['size'] for row in snapshot['files'].values()), "unresolved": 0}}, indent=2))


if __name__ == "__main__":
    main()
