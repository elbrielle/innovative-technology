#!/usr/bin/env python3
"""Fail closed when the generated public mirror diverges from its Canvas snapshot."""

from __future__ import annotations

import hashlib
import json
import os
import re
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlparse

from build_site import canonical_hash, sha256_text


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "course-snapshot.json"
MANIFEST = ROOT / "data" / "site-manifest.json"
POLICY = ROOT / "data" / "publication-policy.json"
PUBLIC_LINKS = ROOT / "data" / "public-links.json"
LEGACY_ALIASES = ROOT / "data" / "legacy-route-aliases.json"


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
    expected_counts = {
        "modules": len(modules),
        "items": len(items),
        "item_pages": sum(item["type"] != "SubHeader" for item in items),
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

    html_paths = [ROOT / "index.html", ROOT / "parity.html"] + sorted((ROOT / "modules").glob("*.html")) + sorted((ROOT / "lessons").glob("*.html"))
    canvas_route = re.compile(r"https?://verizoninnovativelearning\.instructure\.com/(?:api/v1/)?courses/23402/")
    forbidden_tokens = ["YOUR_BG_IMAGE_URL", "Link.Placeholder"]
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

    protected_ids = {str(value) for value in snapshot.get("protected_file_ids", [])}
    asset_names = "\n".join(actual_assets)
    for protected_id in protected_ids:
        if protected_id in asset_names:
            failures.append(f"Protected file {protected_id} leaked into assets/canvas")
    protected_page = (ROOT / "lessons" / "2633987.html").read_text(encoding="utf-8")
    if "intentionally not published here" not in protected_page or "canvas-content" in protected_page:
        failures.append("Protected About Me Phone page does not use the district-only public notice")

    if manifest.get("unresolved"):
        failures.append(f"Site manifest has unresolved routes: {manifest['unresolved']}")
    if failures:
        print(json.dumps({"status": "FAIL", "failures": failures}, indent=2))
        raise SystemExit(1)
    print(json.dumps({"status": "PASS", "checks": {**expected_counts, "html_pages": len(html_paths), "public_file_bytes": sum(row['metadata']['size'] for row in snapshot['files'].values()), "unresolved": 0}}, indent=2))


if __name__ == "__main__":
    main()
