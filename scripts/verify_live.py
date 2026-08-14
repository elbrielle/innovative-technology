#!/usr/bin/env python3
"""Read-only verification that live Canvas still matches the committed release snapshot."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
from pathlib import Path

from canvas_api import Canvas, env_course_id
from export_canvas import (
    COURSE_ID,
    assignment_projection,
    discussion_projection,
    file_metadata,
    item_projection,
    module_projection,
    page_projection,
    question_projection,
    quiz_projection,
    referenced_file_ids,
    sha256_text,
)


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data" / "course-snapshot.json"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    if env_course_id() != snapshot["source"]["course_id"] or COURSE_ID != snapshot["source"]["course_id"]:
        raise SystemExit("Snapshot and VILS_CANVAS_COURSE_ID do not match")
    canvas = Canvas()
    failures: list[str] = []

    live_modules = sorted(canvas.paged(f"/courses/{COURSE_ID}/modules?per_page=100"), key=lambda row: (row.get("position") or 0, row["id"]))
    if [module_projection(row) for row in live_modules] != [{key: module.get(key) for key in module_projection({}).keys()} for module in snapshot["modules"]]:
        failures.append("Live Canvas module projection differs from the snapshot")

    snapshot_items = {item["id"]: item for module in snapshot["modules"] for item in module["items"]}
    live_items: dict[int, dict] = {}
    for module in live_modules:
        rows = sorted(canvas.paged(f"/courses/{COURSE_ID}/modules/{module['id']}/items?per_page=100"), key=lambda row: (row.get("position") or 0, row["id"]))
        for row in rows:
            live_items[row["id"]] = row
    if set(live_items) != set(snapshot_items):
        failures.append("Live Canvas item ID set differs from the snapshot")
    else:
        for item_id, row in live_items.items():
            expected = {key: snapshot_items[item_id].get(key) for key in item_projection({}).keys()}
            if item_projection(row) != expected:
                failures.append(f"Live Canvas module item differs: {item_id}")

    def fetch_resource(item_id: int):
        item = snapshot_items[item_id]
        kind = item["type"]
        if kind == "Page":
            row = canvas.get(f"/courses/{COURSE_ID}/pages/{item['page_url']}")
            return item_id, page_projection(row), row.get("body") or "", None
        if kind == "Assignment":
            row = canvas.get(f"/courses/{COURSE_ID}/assignments/{item['content_id']}?include[]=rubric&include[]=rubric_settings")
            return item_id, assignment_projection(row), row.get("description") or "", None
        if kind == "Discussion":
            row = canvas.get(f"/courses/{COURSE_ID}/discussion_topics/{item['content_id']}")
            return item_id, discussion_projection(row), row.get("message") or "", None
        if kind == "Quiz":
            row = canvas.get(f"/courses/{COURSE_ID}/quizzes/{item['content_id']}")
            questions = canvas.paged(f"/courses/{COURSE_ID}/quizzes/{item['content_id']}/questions?per_page=100")
            return item_id, quiz_projection(row), row.get("description") or "", [question_projection(question) for question in questions]
        raise AssertionError(kind)

    body_ids = [item_id for item_id, item in snapshot_items.items() if item["type"] in {"Page", "Assignment", "Discussion", "Quiz"}]
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures = [pool.submit(fetch_resource, item_id) for item_id in body_ids]
        for future in concurrent.futures.as_completed(futures):
            item_id, metadata, body, questions = future.result()
            expected = snapshot_items[item_id]["resource"]
            if metadata != expected["metadata"]:
                failures.append(f"Live resource metadata differs: item {item_id}")
            if snapshot_items[item_id].get("public_state") == "protected":
                if sha256_text(body) != expected["private_body_sha256"] or len(body) != expected["private_body_length"]:
                    failures.append("Protected About Me Phone body changed; review publication policy before syncing")
            else:
                if sha256_text(body) != expected["body_sha256"]:
                    failures.append(f"Live instructional body differs: item {item_id}")
                if referenced_file_ids(body) != expected.get("referenced_file_ids", []):
                    failures.append(f"Live referenced file set differs: item {item_id}")
            if questions is not None and questions != expected.get("question_contract", []):
                failures.append(f"Live quiz question contract differs: item {item_id}")

    file_ids = sorted(int(file_id) for file_id in snapshot["files"])
    raw_files: dict[int, dict] = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=12) as pool:
        futures = {pool.submit(canvas.get, f"/files/{file_id}"): file_id for file_id in file_ids}
        for future in concurrent.futures.as_completed(futures):
            raw_files[futures[future]] = future.result()
    folder_ids = sorted({row.get("folder_id") for row in raw_files.values() if row.get("folder_id")})
    folders = {folder_id: canvas.get(f"/folders/{folder_id}") for folder_id in folder_ids}
    for file_id in file_ids:
        expected = snapshot["files"][str(file_id)]
        if file_metadata(raw_files[file_id], folders.get(raw_files[file_id].get("folder_id"))) != expected["metadata"]:
            failures.append(f"Live Canvas file metadata differs: {file_id}")
        path = ROOT / expected["public_path"]
        if not path.is_file() or sha256_file(path) != expected["sha256"]:
            failures.append(f"Local public file bytes differ: {file_id}")

    if failures:
        print(json.dumps({"status": "FAIL", "failure_count": len(failures), "failures": failures}, indent=2))
        raise SystemExit(1)
    print(json.dumps({"status": "PASS", "course_id": COURSE_ID, "modules": len(live_modules), "items": len(live_items), "resources": len(body_ids), "public_files": len(file_ids)}, indent=2))


if __name__ == "__main__":
    main()
