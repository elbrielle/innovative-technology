#!/usr/bin/env python3
"""Synchronize a reviewed, additions-only VILS fleet plan to one Canvas course.

Dry-run is the default. The apply path is deliberately limited to the seven
August 2026 Xello/Coding Foundations additions. It verifies the immutable plan,
source snapshot, live destination guard, inactive migration state, and private
backup before creating anything. It never renames, deletes, publishes, dates,
or replaces an existing teacher object.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import urllib.parse
from datetime import datetime, timezone
from pathlib import Path

import apply_coding_foundations_retrofit as coding
import sync_duncan_current_release as sync_release
from canvas_api import Canvas


EXPECTED_SOURCE_IDS = {
    2665839,
    2661806,
    2661807,
    2661808,
    2661809,
    2661810,
    2661811,
}
ACTIVE_MIGRATION_STATES = {
    "queued",
    "pre_processing",
    "running",
    "waiting_for_select",
}
IRVING_HOST = "https://learn.irvingisd.net"
IRVING_API = f"{IRVING_HOST}/api/v1"
VIDEO_LEGACY_TITLES = [
    "Unit at a Glance: Video Game Design",
    "Facilitator Guide: Video Game Design Lesson 1 — Skillmap, Sign-in + Save",
    "Lesson 1: Skillmap",
    "Facilitator Guide: Video Game Design Lesson 2 — Remix, Test + Explain",
    "Lesson 2: Remix",
]
VIDEO_NEW_TITLES = [
    "Text-Code Bridge (2 days)",
    "Facilitator Guide: Text-Code Bridge Day 1 — Trace, Predict + Repair",
    "Lesson 3: Text Code — Trace, Predict + Repair",
    "Facilitator Guide: Text-Code Bridge Day 2 — Change the Grid with Purpose",
    "Lesson 4: Text Code — Emergency Supply Grid",
    "Checkpoint: Text Code + Nested Loops",
]
MODULE_ITEM_GUARD_FIELDS = (
    "id",
    "type",
    "title",
    "position",
    "content_id",
    "page_url",
)
XELLO_TITLE = (
    "Facilitator Guide: Xello — Matchmaker, Personality Style, and Learning Style"
)
ASSET_KEYS = (
    "passport_en_docx",
    "passport_en_pdf",
    "passport_es_docx",
    "passport_es_pdf",
    "teacher_deck",
    "screenshot_code",
    "screenshot_result",
    "day1_highlighted",
    "day2_scaffold",
    "exemplar",
)


def stable_json(value: object) -> str:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False
    )


def semantic_sha(value: object) -> str:
    return hashlib.sha256(stable_json(value).encode("utf-8")).hexdigest()


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_private(path: Path, value: object) -> None:
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.chmod(path, 0o600)


def page_path(value: str) -> str:
    return urllib.parse.quote(value, safe="+-_")


def module_item_guard(row: dict) -> dict:
    """Publication is teacher discretion and never participates in a guard."""
    return {key: row.get(key) for key in MODULE_ITEM_GUARD_FIELDS}


def front_page_content_guard(row: dict) -> dict:
    """Protect the homepage content/identity while ignoring publication state."""
    return {
        key: row.get(key)
        for key in (
            "page_id",
            "url",
            "title",
            "body",
            "front_page",
            "editing_roles",
            "hide_from_students",
        )
    }


def live_guard(canvas: Canvas, plan: dict) -> tuple[dict, dict[str, list[dict]]]:
    course_id = int(plan["course_id"])
    course = canvas.get(
        f"/courses/{course_id}?include[]=term&include[]=syllabus_body"
    )
    front = canvas.get(f"/courses/{course_id}/front_page")
    modules = canvas.paged(f"/courses/{course_id}/modules?per_page=100")
    modules_by_id = {int(row["id"]): row for row in modules}
    parents = plan["parents"]
    week = modules_by_id.get(int(parents["week1_module_id"]))
    video = modules_by_id.get(int(parents["video_module_id"]))
    if not week or not video:
        raise RuntimeError("A reviewed parent module ID is no longer present")
    module_items = {
        "week": canvas.paged(
            f"/courses/{course_id}/modules/{week['id']}/items?per_page=100"
        ),
        "video": canvas.paged(
            f"/courses/{course_id}/modules/{video['id']}/items?per_page=100"
        ),
    }
    all_items: list[dict] = []
    for module in modules:
        if int(module["id"]) == int(week["id"]):
            rows = module_items["week"]
        elif int(module["id"]) == int(video["id"]):
            rows = module_items["video"]
        else:
            rows = canvas.paged(
                f"/courses/{course_id}/modules/{module['id']}/items?per_page=100"
            )
        all_items.extend(rows)
    target_titles = [row["title"] for row in plan["operations"]]
    if any(row.get("title") in target_titles for row in all_items):
        raise RuntimeError("A planned addition title now exists; stop and re-audit")
    groups = canvas.paged(f"/courses/{course_id}/assignment_groups?per_page=100")
    minor = [row for row in groups if row.get("name") == "Minor Grades"]
    major = [row for row in groups if row.get("name") == "Major Grades"]
    if len(minor) != 1 or len(major) != 1:
        raise RuntimeError("Minor Grades or Major Grades is no longer uniquely mapped")
    guard = {
        "course": {
            key: course.get(key)
            for key in ("id", "name", "course_code", "workflow_state", "default_view")
        },
        "front_page": {
            key: front.get(key)
            for key in ("page_id", "url", "title", "front_page")
        },
        "week_module": {
            "id": week["id"],
            "name": week["name"],
            "items": [module_item_guard(row) for row in module_items["week"]],
        },
        "video_module": {
            "id": video["id"],
            "name": video["name"],
            "items": [module_item_guard(row) for row in module_items["video"]],
        },
        "groups": {"minor": minor[0]["id"], "major": major[0]["id"]},
        "missing_titles_confirmed": target_titles,
    }
    return guard, module_items


def source_index(snapshot: dict) -> tuple[dict[int, dict], dict[int, dict]]:
    items: dict[int, dict] = {}
    modules: dict[int, dict] = {}
    for module in snapshot["modules"]:
        modules[int(module["id"])] = module
        for item in module["items"]:
            items[int(item["id"])] = item
    return items, modules


def source_file_ids(snapshot: dict, source_items: dict[int, dict]) -> dict[str, int]:
    required = {
        int(file_id)
        for source_id in EXPECTED_SOURCE_IDS
        for file_id in (
            (source_items[source_id].get("resource") or {}).get(
                "referenced_file_ids"
            )
            or []
        )
    }
    result: dict[str, int] = {}
    for source_id, entry in snapshot["files"].items():
        source_id_int = int(source_id)
        if source_id_int not in required:
            continue
        result[entry["metadata"]["filename"]] = source_id_int
    return result


def marker(source_id: int) -> str:
    return (
        '<div data-vils-fleet-addition="2026-08-25" '
        f'data-vils-source-module-item="{source_id}" '
        'style="display:none;" aria-hidden="true"></div>'
    )


def verify_plan(plan_path: Path, plan: dict) -> tuple[dict, dict]:
    sidecar = plan_path.with_suffix(plan_path.suffix + ".sha256")
    if not sidecar.exists() or sidecar.read_text(encoding="utf-8").strip() != file_sha(
        plan_path
    ):
        raise RuntimeError("Reviewed plan sidecar hash is missing or does not match")
    if plan.get("review_status") != "reviewed_by_user":
        raise RuntimeError("Plan is not marked reviewed_by_user")
    operations = plan.get("operations") or []
    if {int(row["canonical_item_id"]) for row in operations} != EXPECTED_SOURCE_IDS:
        raise RuntimeError("Plan is outside the identity-locked seven-item scope")
    if any(row.get("action") != "add" for row in operations):
        raise RuntimeError("Only add operations are supported")
    if any(row.get("published") is not False for row in operations):
        raise RuntimeError("Every planned addition must remain unpublished")
    preserve = plan.get("preserve") or {}
    if preserve.get("deletions_allowed") is not False:
        raise RuntimeError("Plan does not explicitly prohibit deletion")
    backup_path = Path(plan["backup_path"]).expanduser()
    backup = json.loads(backup_path.read_text(encoding="utf-8"))
    if semantic_sha(backup) != plan["backup_sha256"]:
        raise RuntimeError("Private backup hash no longer matches the plan")
    snapshot_path = Path(plan["canonical_snapshot"]).expanduser()
    snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if file_sha(snapshot_path) != plan["canonical_snapshot_file_sha256"]:
        raise RuntimeError("Canonical snapshot file changed after review")
    if snapshot.get("generated_at") != plan["canonical_generated_at"]:
        raise RuntimeError("Canonical snapshot timestamp changed after review")
    if snapshot.get("semantic_sha256") != plan["canonical_semantic_sha256"]:
        raise RuntimeError("Canonical snapshot semantic identity changed after review")
    return snapshot, backup


def ensure_inactive_migrations(canvas: Canvas, course_id: int) -> None:
    migrations = canvas.paged(
        f"/courses/{course_id}/content_migrations?per_page=100"
    )
    active = [
        {"id": row.get("id"), "workflow_state": row.get("workflow_state")}
        for row in migrations
        if row.get("workflow_state") in ACTIVE_MIGRATION_STATES
    ]
    if active:
        raise RuntimeError(f"Active Canvas migration holds apply: {active}")


def create_module_item(
    canvas: Canvas,
    course_id: int,
    module_id: int,
    *,
    title: str,
    item_type: str,
    content_id: int | None = None,
    page_url: str | None = None,
    position: int | None = None,
) -> dict:
    params: dict[str, object] = {
        "module_item[type]": item_type,
        "module_item[title]": title,
        "module_item[published]": "false",
    }
    if content_id is not None:
        params["module_item[content_id]"] = str(content_id)
    if page_url is not None:
        params["module_item[page_url]"] = page_url
    if position is not None:
        params["module_item[position]"] = str(position)
    created, _ = canvas.request(
        "POST", f"/courses/{course_id}/modules/{module_id}/items", params
    )
    return created


def verify_after(
    canvas: Canvas,
    plan: dict,
    backup: dict,
    journal: dict,
) -> dict:
    course_id = int(plan["course_id"])
    week_id = int(plan["parents"]["week1_module_id"])
    video_id = int(plan["parents"]["video_module_id"])
    front = canvas.get(f"/courses/{course_id}/front_page")
    if front_page_content_guard(front) != front_page_content_guard(
        backup["front_page"]
    ):
        raise RuntimeError("Protected front page changed during additions-only apply")
    video_module = canvas.get(f"/courses/{course_id}/modules/{video_id}")
    if video_module.get("name") != "SW3 · Video Game Design":
        raise RuntimeError("Ross's reviewed module name changed")
    video_items = sorted(
        canvas.paged(f"/courses/{course_id}/modules/{video_id}/items?per_page=100"),
        key=lambda row: row["position"],
    )
    if [row["title"] for row in video_items] != VIDEO_LEGACY_TITLES + VIDEO_NEW_TITLES:
        raise RuntimeError("Video module order does not match the reviewed append plan")
    old_guard = plan["destination_guard"]["video_module"]["items"]
    for before, after in zip(old_guard, video_items[: len(VIDEO_LEGACY_TITLES)]):
        for field in ("id", "type", "title", "content_id", "page_url"):
            if before.get(field) != after.get(field):
                raise RuntimeError(f"Existing Video Game item changed field {field}")
    if any(row.get("published") for row in video_items[len(VIDEO_LEGACY_TITLES) :]):
        raise RuntimeError("A new Video Game item was unexpectedly published")
    week_items = canvas.paged(
        f"/courses/{course_id}/modules/{week_id}/items?per_page=100"
    )
    xello_module_item = next(
        (row for row in week_items if row.get("title") == XELLO_TITLE), None
    )
    if not xello_module_item or int(xello_module_item["position"]) != 6:
        raise RuntimeError("Xello guide is not at the reviewed Week 1 anchor")
    if xello_module_item.get("published"):
        raise RuntimeError("Xello guide was unexpectedly published")
    page_titles = {
        XELLO_TITLE,
        VIDEO_NEW_TITLES[1],
        VIDEO_NEW_TITLES[3],
    }
    pages = {
        row["title"]: row
        for row in canvas.paged(f"/courses/{course_id}/pages?per_page=100")
        if row.get("title") in page_titles
    }
    if set(pages) != page_titles:
        raise RuntimeError("A planned facilitator-guide page is missing")
    for title, row in pages.items():
        detail = canvas.get(
            f"/courses/{course_id}/pages/{page_path(row['url'])}"
        )
        body = detail.get("body") or ""
        if 'data-vils-fleet-addition="2026-08-25"' not in body:
            raise RuntimeError(f"Fleet identity marker missing from {title}")
        if "verizoninnovativelearning.instructure.com/courses/23402" in body:
            raise RuntimeError(f"Source-instance Canvas link remains in {title}")
        if detail.get("published"):
            raise RuntimeError(f"New page unexpectedly published: {title}")
    assignments = {
        row["name"]: row
        for row in canvas.paged(f"/courses/{course_id}/assignments?per_page=100")
    }
    day1 = canvas.get(
        f"/courses/{course_id}/assignments/{assignments[VIDEO_NEW_TITLES[2]]['id']}"
    )
    day2 = canvas.get(
        f"/courses/{course_id}/assignments/{assignments[VIDEO_NEW_TITLES[4]]['id']}?include[]=rubric&include[]=rubric_settings"
    )
    if float(day1.get("points_possible") or 0) != 25:
        raise RuntimeError("Day 1 points drifted")
    if float(day2.get("points_possible") or 0) != 100:
        raise RuntimeError("Day 2 points drifted")
    for row in (day1, day2):
        if row.get("published") or row.get("due_at") or row.get("unlock_at") or row.get("lock_at"):
            raise RuntimeError("A new assignment gained publication or dates")
        if set(row.get("submission_types") or []) != {
            "online_upload",
            "online_text_entry",
        }:
            raise RuntimeError("A new assignment lost its equivalent submission routes")
        if "verizoninnovativelearning.instructure.com/courses/23402" in (
            row.get("description") or ""
        ):
            raise RuntimeError("Source-instance Canvas link remains in an assignment")
    if len(day2.get("rubric") or []) != 4:
        raise RuntimeError("Day 2 rubric was not created completely")
    quizzes = {
        row["title"]: row
        for row in canvas.paged(f"/courses/{course_id}/quizzes?per_page=100")
    }
    quiz = canvas.get(
        f"/courses/{course_id}/quizzes/{quizzes[VIDEO_NEW_TITLES[5]]['id']}"
    )
    questions = canvas.paged(
        f"/courses/{course_id}/quizzes/{quiz['id']}/questions?per_page=100"
    )
    if len(questions) != 8 or quiz.get("published"):
        raise RuntimeError("Checkpoint quiz is incomplete or published")
    quiz_assignment = canvas.get(
        f"/courses/{course_id}/assignments/{quiz['assignment_id']}"
    )
    if float(quiz_assignment.get("points_possible") or 0) != 8:
        raise RuntimeError("Checkpoint gradebook total is not 8 points")
    verification = {
        "status": "PASS",
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "course_id": course_id,
        "created_module_item_ids": journal.get("created_module_item_ids", {}),
        "created_content_ids": journal.get("created_content_ids", {}),
        "asset_file_ids": journal.get("asset_file_ids", {}),
        "video_titles": [row["title"] for row in video_items],
        "xello_position": xello_module_item["position"],
        "quiz_questions": len(questions),
        "front_page_preserved": True,
        "existing_video_ids_preserved": True,
        "all_new_items_unpublished": True,
        "no_existing_object_deleted": True,
    }
    return verification


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", type=Path, required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    plan_path = args.plan.expanduser().resolve()
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    snapshot, backup = verify_plan(plan_path, plan)
    source_items, _ = source_index(snapshot)
    for operation in plan["operations"]:
        source = source_items[int(operation["canonical_item_id"])]
        if (source.get("type"), source.get("title")) != (
            operation.get("type"),
            operation.get("title"),
        ):
            raise RuntimeError("Plan/source identity mismatch")
    canvas = Canvas(base=IRVING_API)
    course_id = int(plan["course_id"])
    ensure_inactive_migrations(canvas, course_id)
    guard, _ = live_guard(canvas, plan)
    if semantic_sha(guard) != plan["destination_guard_sha256"]:
        raise RuntimeError("Live destination changed after the reviewed plan")
    print(
        json.dumps(
            {
                "status": "PREFLIGHT_PASS",
                "course_id": course_id,
                "operations": len(plan["operations"]),
                "apply": args.apply,
            },
            indent=2,
        )
    )
    if not args.apply:
        return

    coding.HOST = IRVING_HOST
    coding.MINOR_GROUP_ID = int(plan["assignment_groups"]["minor_id"])
    coding.MAJOR_GROUP_ID = int(plan["assignment_groups"]["major_id"])
    sync_release.COURSE_ID = course_id
    sync_release.IRVING_WEB = f"{IRVING_HOST}/courses/{course_id}"
    asset_rows: dict[str, dict] = {}
    for key in ASSET_KEYS:
        path = coding.ASSETS[key]
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"Reviewed asset missing: {path}")
        asset_rows[key] = coding.upload_canvas_file(canvas, course_id, path)
        print("ASSET", key, asset_rows[key]["id"])
    filename_to_source_id = source_file_ids(snapshot, source_items)
    filename_to_dest_id = {
        coding.ASSETS[key].name: int(row["id"])
        for key, row in asset_rows.items()
    }
    source_to_dest_files = {
        source_id: filename_to_dest_id[filename]
        for filename, source_id in filename_to_source_id.items()
        if filename in filename_to_dest_id
    }
    required_files = {
        int(file_id)
        for source_id in EXPECTED_SOURCE_IDS
        for file_id in (
            (source_items[source_id].get("resource") or {}).get(
                "referenced_file_ids"
            )
            or []
        )
    }
    if set(source_to_dest_files) != required_files:
        raise RuntimeError("Not every canonical file dependency was mapped")

    journal_path = plan_path.with_name("apply-journal.json")
    journal: dict = {
        "status": "running",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "course_id": course_id,
        "plan_sha256": file_sha(plan_path),
        "asset_file_ids": {key: int(row["id"]) for key, row in asset_rows.items()},
        "created_content_ids": {},
        "created_module_item_ids": {},
    }
    write_private(journal_path, journal)

    def body_for(source_id: int) -> str:
        source = source_items[source_id]
        body = (source.get("resource") or {}).get("body") or ""
        rewritten = sync_release.replace_content_links(
            body, source_items, {}, source_to_dest_files
        )
        return marker(source_id) + rewritten

    xello = coding.ensure_page(
        canvas, course_id, XELLO_TITLE, body_for(2665839), True
    )
    journal["created_content_ids"][str(2665839)] = {
        "type": "Page",
        "page_id": xello.get("page_id"),
        "url": xello["url"],
    }
    xello_item = create_module_item(
        canvas,
        course_id,
        int(plan["parents"]["week1_module_id"]),
        title=XELLO_TITLE,
        item_type="Page",
        page_url=xello["url"],
        position=6,
    )
    journal["created_module_item_ids"][str(2665839)] = xello_item["id"]
    write_private(journal_path, journal)

    video_id = int(plan["parents"]["video_module_id"])
    subheader = create_module_item(
        canvas,
        course_id,
        video_id,
        title=VIDEO_NEW_TITLES[0],
        item_type="SubHeader",
    )
    journal["created_module_item_ids"][str(2661806)] = subheader["id"]
    write_private(journal_path, journal)

    guide1 = coding.ensure_page(
        canvas, course_id, VIDEO_NEW_TITLES[1], body_for(2661807), True
    )
    journal["created_content_ids"][str(2661807)] = {
        "type": "Page",
        "page_id": guide1.get("page_id"),
        "url": guide1["url"],
    }
    guide1_item = create_module_item(
        canvas,
        course_id,
        video_id,
        title=VIDEO_NEW_TITLES[1],
        item_type="Page",
        page_url=guide1["url"],
    )
    journal["created_module_item_ids"][str(2661807)] = guide1_item["id"]
    write_private(journal_path, journal)

    day1 = coding.ensure_assignment(
        canvas, course_id, VIDEO_NEW_TITLES[2], body_for(2661808), 1, True
    )
    journal["created_content_ids"][str(2661808)] = {
        "type": "Assignment",
        "id": day1["id"],
    }
    day1_item = create_module_item(
        canvas,
        course_id,
        video_id,
        title=VIDEO_NEW_TITLES[2],
        item_type="Assignment",
        content_id=day1["id"],
    )
    journal["created_module_item_ids"][str(2661808)] = day1_item["id"]
    write_private(journal_path, journal)

    guide2 = coding.ensure_page(
        canvas, course_id, VIDEO_NEW_TITLES[3], body_for(2661809), True
    )
    journal["created_content_ids"][str(2661809)] = {
        "type": "Page",
        "page_id": guide2.get("page_id"),
        "url": guide2["url"],
    }
    guide2_item = create_module_item(
        canvas,
        course_id,
        video_id,
        title=VIDEO_NEW_TITLES[3],
        item_type="Page",
        page_url=guide2["url"],
    )
    journal["created_module_item_ids"][str(2661809)] = guide2_item["id"]
    write_private(journal_path, journal)

    day2 = coding.ensure_assignment(
        canvas, course_id, VIDEO_NEW_TITLES[4], body_for(2661810), 2, True
    )
    coding.ensure_rubric(canvas, course_id, day2, True)
    journal["created_content_ids"][str(2661810)] = {
        "type": "Assignment",
        "id": day2["id"],
    }
    day2_item = create_module_item(
        canvas,
        course_id,
        video_id,
        title=VIDEO_NEW_TITLES[4],
        item_type="Assignment",
        content_id=day2["id"],
    )
    journal["created_module_item_ids"][str(2661810)] = day2_item["id"]
    write_private(journal_path, journal)

    quiz = coding.ensure_quiz(canvas, course_id, True)
    journal["created_content_ids"][str(2661811)] = {
        "type": "Quiz",
        "id": quiz["id"],
        "assignment_id": quiz.get("assignment_id"),
    }
    quiz_item = create_module_item(
        canvas,
        course_id,
        video_id,
        title=VIDEO_NEW_TITLES[5],
        item_type="Quiz",
        content_id=quiz["id"],
    )
    journal["created_module_item_ids"][str(2661811)] = quiz_item["id"]
    write_private(journal_path, journal)

    verification = verify_after(canvas, plan, backup, journal)
    verification_path = plan_path.with_name("verification.json")
    write_private(verification_path, verification)
    journal["status"] = "complete"
    journal["completed_at"] = datetime.now(timezone.utc).isoformat()
    journal["verification_path"] = str(verification_path)
    write_private(journal_path, journal)
    print(json.dumps(verification, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
