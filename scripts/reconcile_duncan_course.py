#!/usr/bin/env python3
"""Remove Duncan's archived-template course surfaces after a verified sync.

The script deliberately keeps the two Duncan/course-shell modules and the
August 10 Commons lineage. The August 5 package remains in Canvas import
history as the recovery source. Any assessment with submitted student work is
left untouched.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

from canvas_api import Canvas, stable_json


IRVING_API = "https://learn.irvingisd.net/api/v1"
COURSE_ID = 97806
CUSTOM_MODULE_IDS = {537449, 537450}
OLD_IMPORT_MIN = 540000
CURRENT_IMPORT_MIN = 545000
OLD_IMPORT_STARTED = "2026-08-05T17:57:38Z"
OLD_IMPORT_FINISHED = "2026-08-05T18:04:23Z"
CURRENT_HOME_URL = "student-home-smart-solutions"


def item_signature(items: list[dict]) -> list[tuple[str, str]]:
    return [(item["type"], item["title"]) for item in items]


def current_source_modules() -> dict[str, dict]:
    snapshot = json.loads(Path("data/course-snapshot.json").read_text(encoding="utf-8"))
    modules = snapshot["modules"]
    assert len(modules) == 34, f"Expected 34 source modules, found {len(modules)}"
    assert sum(len(module["items"]) for module in modules) == 503
    return {module["name"]: module for module in modules}


def live_inventory(canvas: Canvas) -> tuple[list[dict], dict[int, list[dict]]]:
    modules = canvas.paged(f"/courses/{COURSE_ID}/modules?per_page=100")
    items = {
        module["id"]: canvas.paged(
            f"/courses/{COURSE_ID}/modules/{module['id']}/items?per_page=100"
        )
        for module in modules
    }
    return modules, items


def classify(modules: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    custom = [module for module in modules if module["id"] < OLD_IMPORT_MIN]
    old = [
        module
        for module in modules
        if OLD_IMPORT_MIN <= module["id"] < CURRENT_IMPORT_MIN
    ]
    current = [module for module in modules if module["id"] >= CURRENT_IMPORT_MIN]
    assert {module["id"] for module in custom} == CUSTOM_MODULE_IDS, (
        "Unexpected non-template modules; refusing to infer ownership: "
        f"{[(module['id'], module['name']) for module in custom]}"
    )
    assert len(old) == 34, f"Expected 34 archived-template modules, found {len(old)}"
    assert len(current) == 34, (
        "Expected exactly one 34-module current Commons lineage. "
        f"Found {len(current)}; the Commons import may be incomplete or duplicated."
    )
    return custom, old, current


def verify_current_lineage(current: list[dict], items: dict[int, list[dict]]) -> None:
    source = current_source_modules()
    live_by_name = {module["name"]: module for module in current}
    assert set(live_by_name) == set(source), (
        "Current module names do not match the August 19 source.\n"
        f"Missing: {sorted(set(source) - set(live_by_name))}\n"
        f"Extra: {sorted(set(live_by_name) - set(source))}"
    )
    for name, source_module in source.items():
        live_module = live_by_name[name]
        expected = item_signature(source_module["items"])
        actual = item_signature(items[live_module["id"]])
        assert actual == expected, (
            f"Current module is not at the verified Commons release: {name}\n"
            f"Expected {len(expected)} items; found {len(actual)}."
        )


def resource_sets(old: list[dict], items: dict[int, list[dict]]) -> dict[str, set]:
    resources: dict[str, set] = {
        "pages": set(),
        "assignments": set(),
        "quizzes": set(),
        "discussions": set(),
    }
    for module in old:
        for item in items[module["id"]]:
            if item["type"] == "Page" and item.get("page_url"):
                resources["pages"].add(item["page_url"])
            elif item["type"] == "Assignment" and item.get("content_id"):
                resources["assignments"].add(item["content_id"])
            elif item["type"] == "Quiz" and item.get("content_id"):
                resources["quizzes"].add(item["content_id"])
            elif item["type"] == "Discussion" and item.get("content_id"):
                resources["discussions"].add(item["content_id"])
    return resources


def assessment_submission_state(canvas: Canvas, resources: dict[str, set]) -> dict[int, bool]:
    assignment_ids = set(resources["assignments"])
    for quiz_id in resources["quizzes"]:
        quiz = canvas.get(f"/courses/{COURSE_ID}/quizzes/{quiz_id}")
        if quiz.get("assignment_id"):
            assignment_ids.add(quiz["assignment_id"])
    all_assignments = {
        assignment["id"]: assignment
        for assignment in canvas.paged(f"/courses/{COURSE_ID}/assignments?per_page=100")
    }
    assert assignment_ids <= set(all_assignments)
    states = {
        assignment_id: bool(
            all_assignments[assignment_id].get("has_submitted_submissions")
        )
        for assignment_id in assignment_ids
    }
    return states


def old_import_pages(canvas: Canvas) -> list[dict]:
    pages = canvas.paged(f"/courses/{COURSE_ID}/pages?per_page=100")
    old = [
        page
        for page in pages
        if OLD_IMPORT_STARTED <= (page.get("created_at") or "") <= OLD_IMPORT_FINISHED
    ]
    assert len(old) == 88, f"Expected 88 August 5 imported pages, found {len(old)}"
    return old


def make_backup(
    canvas: Canvas,
    modules: list[dict],
    items: dict[int, list[dict]],
    resources: dict[str, set],
    old_pages: list[dict],
) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "course_id": COURSE_ID,
        "purpose": "Recoverable inventory of archived-template module placements before removal",
        "modules": [
            {
                "id": module["id"],
                "name": module["name"],
                "position": module["position"],
                "published": module.get("published"),
                "items": [
                    {
                        key: item.get(key)
                        for key in (
                            "id",
                            "position",
                            "type",
                            "title",
                            "content_id",
                            "page_url",
                            "external_url",
                            "published",
                        )
                    }
                    for item in items[module["id"]]
                ],
            }
            for module in modules
        ],
        "resource_ids": {key: sorted(value) for key, value in resources.items()},
        "pages": [
            canvas.get(f"/courses/{COURSE_ID}/pages/{page['url']}")
            for page in old_pages
        ],
    }


def delete_old_resources(
    canvas: Canvas,
    resources: dict[str, set],
    submissions: dict[int, bool],
    old_pages: list[dict],
) -> dict[str, int]:
    counts = {"pages": 0, "assignments": 0, "quizzes": 0, "discussions": 0}
    for page in old_pages:
        canvas.request("DELETE", f"/courses/{COURSE_ID}/pages/{page['url']}")
        counts["pages"] += 1
    for assignment_id in sorted(resources["assignments"]):
        if not submissions.get(assignment_id, False):
            canvas.request("DELETE", f"/courses/{COURSE_ID}/assignments/{assignment_id}")
            counts["assignments"] += 1
    for quiz_id in sorted(resources["quizzes"]):
        quiz = canvas.get(f"/courses/{COURSE_ID}/quizzes/{quiz_id}")
        assignment_id = quiz.get("assignment_id")
        if not submissions.get(assignment_id, False):
            canvas.request("DELETE", f"/courses/{COURSE_ID}/quizzes/{quiz_id}")
            counts["quizzes"] += 1
    for discussion_id in sorted(resources["discussions"]):
        discussion = canvas.get(
            f"/courses/{COURSE_ID}/discussion_topics/{discussion_id}"
        )
        assert not discussion.get("discussion_subentry_count")
        canvas.request(
            "DELETE", f"/courses/{COURSE_ID}/discussion_topics/{discussion_id}"
        )
        counts["discussions"] += 1
    return counts


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    canvas = Canvas(base=IRVING_API)
    modules, items = live_inventory(canvas)
    custom, old, current = classify(modules)
    verify_current_lineage(current, items)
    resources = resource_sets(old, items)
    submissions = assessment_submission_state(canvas, resources)
    old_pages = old_import_pages(canvas)
    preserved = sorted(
        assignment_id for assignment_id, has_work in submissions.items() if has_work
    )

    print(f"verified current Commons lineage: {len(current)} modules / 503 items")
    print(f"preserving teacher-owned modules: {[(m['id'], m['name']) for m in custom]}")
    print(f"archived-template modules to remove: {len(old)}")
    print(f"archived-template pages to remove: {len(old_pages)}")
    print(f"assessments preserved because they have submissions: {preserved}")
    if not args.apply:
        print("DRY RUN complete; no Canvas changes made")
        return

    backup = make_backup(canvas, old, items, resources, old_pages)
    backup_path = Path("artifacts/duncan-old-template-module-backup-2026-08-19.json")
    backup_path.parent.mkdir(parents=True, exist_ok=True)
    backup_path.write_text(stable_json(backup), encoding="utf-8")

    current_home = canvas.get(f"/courses/{COURSE_ID}/pages/{CURRENT_HOME_URL}")
    assert current_home["title"] == "Student Home — Smart Solutions"
    assert (current_home.get("created_at") or "").startswith("2026-08-10")
    canvas.request(
        "PUT",
        f"/courses/{COURSE_ID}/pages/{CURRENT_HOME_URL}",
        {"wiki_page[front_page]": True},
    )

    for module in old:
        if module.get("published"):
            canvas.request(
                "PUT",
                f"/courses/{COURSE_ID}/modules/{module['id']}",
                {"module[published]": False},
            )
    for module in old:
        canvas.request("DELETE", f"/courses/{COURSE_ID}/modules/{module['id']}")
    deleted = delete_old_resources(canvas, resources, submissions, old_pages)

    after_modules, after_items = live_inventory(canvas)
    after_custom, after_old, after_current = classify_after(after_modules)
    assert not after_old
    assert {module["id"] for module in after_custom} == CUSTOM_MODULE_IDS
    assert len(after_current) == 34
    verify_current_lineage(after_current, after_items)
    assert len(after_modules) == 36
    remaining_old_pages = old_import_pages_after(canvas)
    assert not remaining_old_pages
    final_home = canvas.get(f"/courses/{COURSE_ID}/pages/{CURRENT_HOME_URL}")
    assert final_home.get("front_page") is True
    print(f"APPLIED: removed {len(old)} old module containers")
    print(f"deleted old resources: {deleted}")
    print(f"preserved submitted assessments: {preserved}")
    print(f"verified final course: {len(after_modules)} modules (34 current + 2 teacher-owned)")


def classify_after(modules: list[dict]) -> tuple[list[dict], list[dict], list[dict]]:
    custom = [module for module in modules if module["id"] < OLD_IMPORT_MIN]
    old = [
        module
        for module in modules
        if OLD_IMPORT_MIN <= module["id"] < CURRENT_IMPORT_MIN
    ]
    current = [module for module in modules if module["id"] >= CURRENT_IMPORT_MIN]
    return custom, old, current


def old_import_pages_after(canvas: Canvas) -> list[dict]:
    return [
        page
        for page in canvas.paged(f"/courses/{COURSE_ID}/pages?per_page=100")
        if OLD_IMPORT_STARTED <= (page.get("created_at") or "") <= OLD_IMPORT_FINISHED
    ]


if __name__ == "__main__":
    main()
