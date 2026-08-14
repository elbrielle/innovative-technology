#!/usr/bin/env python3
"""Read-only inventory used to size and classify the Canvas mirror."""

from __future__ import annotations

import collections
import html
import json
import re
from pathlib import Path

from canvas_api import Canvas, env_course_id, stable_json


ROOT = Path(__file__).resolve().parents[1]
COURSE_ID = env_course_id()
FILE_ID_RE = re.compile(
    r"(?:/files/|files%2[fF]|/api/v1/courses/\d+/files/|/media_attachments_iframe/)(\d+)", re.I
)


def body_for(canvas: Canvas, item: dict) -> tuple[dict | None, str]:
    kind = item.get("type")
    if kind == "Page":
        resource = canvas.get(f"/courses/{COURSE_ID}/pages/{item['page_url']}")
        return resource, resource.get("body") or ""
    if kind == "Assignment":
        resource = canvas.get(
            f"/courses/{COURSE_ID}/assignments/{item['content_id']}?include[]=rubric&include[]=rubric_settings"
        )
        return resource, resource.get("description") or ""
    if kind == "Discussion":
        resource = canvas.get(f"/courses/{COURSE_ID}/discussion_topics/{item['content_id']}")
        return resource, resource.get("message") or ""
    if kind == "Quiz":
        resource = canvas.get(f"/courses/{COURSE_ID}/quizzes/{item['content_id']}")
        return resource, resource.get("description") or ""
    return None, ""


def main() -> None:
    canvas = Canvas()
    modules = canvas.paged(f"/courses/{COURSE_ID}/modules?per_page=100")
    counts = collections.Counter()
    file_refs: collections.Counter[int] = collections.Counter()
    module_rows = []
    for module in modules:
        items = canvas.paged(f"/courses/{COURSE_ID}/modules/{module['id']}/items?per_page=100")
        counts["modules"] += 1
        counts["items"] += len(items)
        module_rows.append(
            {
                "id": module["id"],
                "position": module["position"],
                "name": module["name"],
                "published": module["published"],
                "item_count": len(items),
            }
        )
        for item in items:
            resource, body = body_for(canvas, item)
            if body:
                counts["bodies"] += 1
                counts["body_chars"] += len(body)
                decoded = html.unescape(body)
                for file_id in FILE_ID_RE.findall(decoded):
                    file_refs[int(file_id)] += 1
    files = []
    for file_id, references in sorted(file_refs.items()):
        metadata = canvas.get(f"/files/{file_id}")
        files.append(
            {
                "id": file_id,
                "display_name": metadata.get("display_name"),
                "filename": metadata.get("filename"),
                "content_type": metadata.get("content-type") or metadata.get("content_type"),
                "size": metadata.get("size") or 0,
                "hidden": metadata.get("hidden"),
                "locked": metadata.get("locked"),
                "folder_id": metadata.get("folder_id"),
                "references": references,
            }
        )
    report = {
        "course_id": COURSE_ID,
        "counts": dict(counts),
        "modules": module_rows,
        "files": files,
        "referenced_file_bytes": sum(row["size"] for row in files),
    }
    out = ROOT / "data" / "canvas-inventory.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(stable_json(report), encoding="utf-8")
    print(stable_json(report))


if __name__ == "__main__":
    main()
