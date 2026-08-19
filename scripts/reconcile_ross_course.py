#!/usr/bin/env python3
"""Remove Ross's archived template while preserving confirmed local work."""

from __future__ import annotations

import argparse
import json
import urllib.error
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from canvas_api import Canvas, stable_json


API = "https://learn.irvingisd.net/api/v1"
COURSE_ID = 97926
CURRENT_IMPORT_MIN = 548000
FRONT_PAGE_URL = "welcome-2"
PROTECTED_ASSIGNMENTS = {3098868, 3109581, 3098899, 3098931}
PROTECTED_PAGES = {1116656, 1116640}
OLD_PAGE_START = "2026-08-10T14:28:11Z"
OLD_PAGE_END = "2026-08-10T14:35:25Z"
ORPHAN_WELCOME_PAGE_ID = 1086218
BACKUP_PATH = Path("artifacts/ross-old-template-backup-2026-08-19.json")


def delete_if_present(canvas: Canvas, path: str) -> None:
    try:
        canvas.request("DELETE", path)
    except urllib.error.HTTPError as error:
        if error.code != 404:
            raise


def is_local(item: dict) -> bool:
    return bool(
        (item["type"] == "SubHeader" and item["title"].startswith("ROSS · LOCAL"))
        or (item["type"] == "Page" and item["title"].startswith("ROSS COPY ·"))
        or item.get("content_id") in PROTECTED_ASSIGNMENTS
    )


def source_modules() -> dict[str, dict]:
    snapshot = json.loads(Path("data/course-snapshot.json").read_text(encoding="utf-8"))
    assert len(snapshot["modules"]) == 34
    assert sum(len(module["items"]) for module in snapshot["modules"]) == 503
    return {module["name"]: module for module in snapshot["modules"]}


def inventory(canvas: Canvas) -> tuple[list[dict], dict[int, list[dict]]]:
    modules = canvas.paged(f"/courses/{COURSE_ID}/modules?per_page=100")
    items = {
        module["id"]: canvas.paged(
            f"/courses/{COURSE_ID}/modules/{module['id']}/items?per_page=100"
        )
        for module in modules
    }
    return modules, items


def verify_current(current: list[dict], items: dict[int, list[dict]]) -> None:
    source = source_modules()
    live = {module["name"]: module for module in current}
    assert len(current) == 34 and set(live) == set(source)
    local_count = 0
    canonical_count = 0
    for name, source_module in source.items():
        actual = items[live[name]["id"]]
        local_count += sum(is_local(item) for item in actual)
        canonical = [item for item in actual if not is_local(item)]
        canonical_count += len(canonical)
        assert [(item["type"], item["title"]) for item in canonical] == [
            (item["type"], item["title"]) for item in source_module["items"]
        ], name
    assert canonical_count == 503 and local_count == 8


def resource_sets(old: list[dict], items: dict[int, list[dict]]) -> dict[str, set]:
    result = {"pages": set(), "assignments": set(), "quizzes": set(), "discussions": set()}
    for module in old:
        for item in items[module["id"]]:
            if item["type"] == "Page" and item.get("page_url"):
                result["pages"].add(item["page_url"])
            elif item["type"] == "Assignment" and item.get("content_id"):
                result["assignments"].add(item["content_id"])
            elif item["type"] == "Quiz" and item.get("content_id"):
                result["quizzes"].add(item["content_id"])
            elif item["type"] == "Discussion" and item.get("content_id"):
                result["discussions"].add(item["content_id"])
    return result


def old_pages(canvas: Canvas) -> list[dict]:
    pages = canvas.paged(f"/courses/{COURSE_ID}/pages?per_page=100")
    selected = [
        page
        for page in pages
        if OLD_PAGE_START <= (page.get("created_at") or "") <= OLD_PAGE_END
        and page["page_id"] not in PROTECTED_PAGES
    ]
    orphan = next(page for page in pages if page["page_id"] == ORPHAN_WELCOME_PAGE_ID)
    selected.append(orphan)
    assert len(selected) == 88
    assert not any(page.get("front_page") for page in selected)
    return selected


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    canvas = Canvas(base=API)
    modules, items = inventory(canvas)
    old = [module for module in modules if module["id"] < CURRENT_IMPORT_MIN]
    current = [module for module in modules if module["id"] >= CURRENT_IMPORT_MIN]
    assert len(old) == 34 and len(current) == 34
    verify_current(current, items)
    resources = resource_sets(old, items)
    pages = old_pages(canvas)

    assignments = {
        assignment["id"]: assignment
        for assignment in canvas.paged(f"/courses/{COURSE_ID}/assignments?per_page=100")
    }
    quiz_assignment: dict[int, int | None] = {}
    for quiz_id in resources["quizzes"]:
        quiz = canvas.get(f"/courses/{COURSE_ID}/quizzes/{quiz_id}")
        quiz_assignment[quiz_id] = quiz.get("assignment_id")
    submitted = {
        assignment_id
        for assignment_id, assignment in assignments.items()
        if assignment.get("has_submitted_submissions")
        and (
            assignment_id in resources["assignments"]
            or assignment_id in set(quiz_assignment.values())
        )
    }
    assert submitted == {3109581}
    assert submitted <= PROTECTED_ASSIGNMENTS
    for discussion_id in resources["discussions"]:
        discussion = canvas.get(
            f"/courses/{COURSE_ID}/discussion_topics/{discussion_id}"
        )
        assert not discussion.get("discussion_subentry_count")

    front = next(
        page
        for page in canvas.paged(f"/courses/{COURSE_ID}/pages?per_page=100")
        if page.get("front_page")
    )
    assert front["url"] == FRONT_PAGE_URL and front["title"] == "Welcome!"
    print("verified current release: 34 modules / 503 canonical items / 8 local items")
    print("old modules to remove:", len(old))
    print("old pages to remove:", len(pages))
    print("protected assignments:", sorted(PROTECTED_ASSIGNMENTS))
    print("protected submitted assignments:", sorted(submitted))
    print("protected pages:", sorted(PROTECTED_PAGES))
    print("front page preserved:", front["title"], front["url"])
    if not args.apply:
        print("DRY RUN complete; no Canvas changes made")
        return

    backup = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "course_id": COURSE_ID,
        "front_page": front,
        "protected_assignments": [assignments[item_id] for item_id in sorted(PROTECTED_ASSIGNMENTS)],
        "protected_pages": [
            canvas.get(f"/courses/{COURSE_ID}/pages/{page_url}")
            for page_url in (
                "ross-copy-star-welcome-week-syllabus-+-lab-contract",
                "ross-copy-star-lesson-1-become-a-superhero-create-your-comic-book-cover",
            )
        ],
        "modules": [
            {**module, "items": items[module["id"]]} for module in old
        ],
        "pages": [
            canvas.get(f"/courses/{COURSE_ID}/pages/{page['url']}") for page in pages
        ],
        "resource_ids": {key: sorted(value) for key, value in resources.items()},
    }
    BACKUP_PATH.parent.mkdir(parents=True, exist_ok=True)
    BACKUP_PATH.write_text(stable_json(backup), encoding="utf-8")

    # Ross's current Week 0 must remain student-accessible after the old module is removed.
    current_week = next(
        module for module in current if module["name"] == "SW1 · Before You Begin (Week 0)"
    )
    canvas.request(
        "PUT",
        f"/courses/{COURSE_ID}/modules/{current_week['id']}",
        {"module[published]": True},
    )
    # Publishing Week 0 can publish all of its page items. Restore the teacher
    # guide boundary immediately while leaving Ross's published assignments live.
    for item in canvas.paged(
        f"/courses/{COURSE_ID}/modules/{current_week['id']}/items?per_page=100"
    ):
        if item["type"] == "Page" and item["title"].startswith("Facilitator Guide:"):
            canvas.request(
                "PUT",
                f"/courses/{COURSE_ID}/pages/{item['page_url']}",
                {"wiki_page[published]": False},
            )
    for module in old:
        if module.get("published"):
            canvas.request(
                "PUT",
                f"/courses/{COURSE_ID}/modules/{module['id']}",
                {"module[published]": False},
            )
    for module in old:
        delete_if_present(canvas, f"/courses/{COURSE_ID}/modules/{module['id']}")
    for page in pages:
        delete_if_present(canvas, f"/courses/{COURSE_ID}/pages/{page['url']}")
    for assignment_id in sorted(resources["assignments"] - PROTECTED_ASSIGNMENTS):
        delete_if_present(canvas, f"/courses/{COURSE_ID}/assignments/{assignment_id}")
    for quiz_id, assignment_id in sorted(quiz_assignment.items()):
        assert assignment_id not in submitted
        delete_if_present(canvas, f"/courses/{COURSE_ID}/quizzes/{quiz_id}")
    for discussion_id in sorted(resources["discussions"]):
        delete_if_present(
            canvas, f"/courses/{COURSE_ID}/discussion_topics/{discussion_id}"
        )

    final_modules, final_items = inventory(canvas)
    assert len(final_modules) == 34
    verify_current(final_modules, final_items)
    final_pages = canvas.paged(f"/courses/{COURSE_ID}/pages?per_page=100")
    final_front = next(page for page in final_pages if page.get("front_page"))
    assert final_front["url"] == FRONT_PAGE_URL
    by_title = defaultdict(list)
    for page in final_pages:
        by_title[page["title"]].append(page)
    assert not {title: rows for title, rows in by_title.items() if len(rows) > 1}
    final_assignments = {
        assignment["id"]
        for assignment in canvas.paged(f"/courses/{COURSE_ID}/assignments?per_page=100")
    }
    assert PROTECTED_ASSIGNMENTS <= final_assignments
    print("APPLIED: removed 34 old modules and 88 old/orphan pages")
    print("VERIFIED: 34 current modules / 503 canonical items / 8 local items")
    print("VERIFIED: Ross front page and four assignments preserved")


if __name__ == "__main__":
    main()
