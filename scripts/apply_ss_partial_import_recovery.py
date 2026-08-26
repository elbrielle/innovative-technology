#!/usr/bin/env python3
"""Apply one explicitly approved partial-import recovery plan.

The script is intentionally plan-bound. It verifies the sealed plan, current
publication-neutral destination guard, current private backup, submitted holds,
and exact assignment payload hashes before issuing any Canvas mutation. It
never sends publication parameters and deletes only approved module placements
and module shells, not their underlying course content.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from canvas_api import Canvas, stable_json
from plan_ss_legacy_rebootstrap import (
    IRVING_API,
    module_guard,
    sha256_file,
    sha256_json,
    verify_seal,
    write_sealed,
)
from plan_ss_partial_import_recovery import load_audit_helpers


def assignment_guard(assignment: dict, *, include_description: bool = True) -> dict:
    result = {
        "id": assignment["id"],
        "name": assignment["name"],
        "points_possible": assignment.get("points_possible"),
        "grading_type": assignment.get("grading_type"),
        "submission_types": assignment.get("submission_types") or [],
        "allowed_attempts": assignment.get("allowed_attempts"),
        "omit_from_final_grade": assignment.get("omit_from_final_grade"),
        "peer_reviews": assignment.get("peer_reviews"),
        "anonymous_peer_reviews": assignment.get("anonymous_peer_reviews"),
        "automatic_peer_reviews": assignment.get("automatic_peer_reviews"),
        "assignment_group_id": assignment.get("assignment_group_id"),
        "due_at": assignment.get("due_at"),
        "unlock_at": assignment.get("unlock_at"),
        "lock_at": assignment.get("lock_at"),
        "has_submitted_submissions": assignment.get("has_submitted_submissions"),
        "external_tool_tag_attributes": assignment.get(
            "external_tool_tag_attributes"
        ),
    }
    if include_description:
        result["description"] = assignment.get("description") or ""
    return result


def live_state(canvas: Canvas, plan: dict) -> tuple[dict, dict, dict[int, list[dict]]]:
    course_id = plan["course_id"]
    modules = canvas.paged(f"/courses/{course_id}/modules?per_page=100")
    items = {
        module["id"]: canvas.paged(
            f"/courses/{course_id}/modules/{module['id']}/items?per_page=100"
        )
        for module in modules
    }
    page_summaries = canvas.paged(f"/courses/{course_id}/pages?per_page=100")
    front_summary = next(row for row in page_summaries if row.get("front_page"))
    front = canvas.get(f"/courses/{course_id}/pages/{front_summary['url']}")
    source_home = canvas.get(
        f"/courses/{course_id}/pages/{plan['homepage']['source_url']}"
    )
    protected_assignments = [
        canvas.get(f"/courses/{course_id}/assignments/{assignment_id}")
        for assignment_id in plan["protected"]["assignment_ids"]
    ]
    repair_assignments = [
        canvas.get(f"/courses/{course_id}/assignments/{repair['assignment_id']}")
        for repair in plan["repairs"]
    ]
    guard = {
        "course_id": course_id,
        "modules": [module_guard(module, items[module["id"]]) for module in modules],
        "front_page": {
            "page_id": front["page_id"],
            "url": front["url"],
            "title": front["title"],
            "body": front.get("body") or "",
            "front_page": front.get("front_page"),
            "editing_roles": front.get("editing_roles"),
            "hide_from_students": front.get("hide_from_students"),
        },
        "source_home": {
            "page_id": source_home["page_id"],
            "url": source_home["url"],
            "title": source_home["title"],
            "body": source_home.get("body") or "",
        },
        "protected_assignments": [
            {
                "id": row["id"],
                "name": row["name"],
                "description": row.get("description") or "",
                "points_possible": row.get("points_possible"),
                "submission_types": row.get("submission_types") or [],
                "due_at": row.get("due_at"),
                "unlock_at": row.get("unlock_at"),
                "lock_at": row.get("lock_at"),
                "has_submitted_submissions": row.get("has_submitted_submissions"),
            }
            for row in protected_assignments
        ],
        "repair_assignments": [
            {
                "id": row["id"],
                "description_sha256": hashlib.sha256(
                    (row.get("description") or "").encode("utf-8")
                ).hexdigest(),
            }
            for row in repair_assignments
        ],
    }
    extras = {
        "front": front,
        "source_home": source_home,
        "protected_assignments": protected_assignments,
        "repair_assignments": repair_assignments,
    }
    return guard, {module["id"]: module for module in modules}, items | {
        -1: [extras]
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--approval-note", required=True)
    parser.add_argument("--source-snapshot", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args()

    plan_path = args.plan.expanduser().resolve()
    verify_seal(plan_path)
    if sha256_file(plan_path) != args.plan_sha256:
        raise RuntimeError("Approved amended plan hash does not match")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    if plan.get("status") != "AWAITING_EXPLICIT_AMENDED_APPLY_APPROVAL":
        raise RuntimeError("Plan is not awaiting amended apply approval")

    backup_path = Path(plan["destination_preflight"]["backup"])
    verify_seal(backup_path)
    if sha256_file(backup_path) != plan["destination_preflight"]["backup_sha256"]:
        raise RuntimeError("Post-import backup hash does not match the plan")
    backup = json.loads(backup_path.read_text(encoding="utf-8"))

    source = json.loads(args.source_snapshot.read_text(encoding="utf-8"))
    if source.get("semantic_sha256") != plan["source"]["semantic_sha256"]:
        raise RuntimeError("Canonical source changed after amended planning")

    canvas = Canvas(base=IRVING_API)
    guard, module_by_id, combined = live_state(canvas, plan)
    items_by_module = {key: value for key, value in combined.items() if key != -1}
    extras = combined[-1][0]
    guard_hash = sha256_json(guard)
    if guard_hash != plan["destination_preflight"]["semantic_structure_sha256"]:
        raise RuntimeError(
            "Destination changed after amended planning; refusing to apply"
        )
    if not all(
        row.get("has_submitted_submissions")
        for row in extras["protected_assignments"]
    ):
        raise RuntimeError("A protected assignment lost its submission hold")

    backup_repairs = {
        row["id"]: row for row in backup["repair_assignments"]
    }
    live_repairs = {
        row["id"]: row for row in extras["repair_assignments"]
    }
    for repair in plan["repairs"]:
        assignment_id = repair["assignment_id"]
        if assignment_guard(live_repairs[assignment_id]) != assignment_guard(
            backup_repairs[assignment_id]
        ):
            raise RuntimeError(
                f"Repair assignment changed after backup: {assignment_id}"
            )
        if live_repairs[assignment_id].get("has_submitted_submissions"):
            raise RuntimeError(
                f"Repair assignment now has submissions: {assignment_id}"
            )

    retained_module_ids = {
        plan["week_zero"]["retained_module_id"]
    } | {
        module_id
        for module_id in module_by_id
        if 547874 <= module_id <= 547906
    }
    if len(retained_module_ids) != 34:
        raise RuntimeError("Retained module set is not exactly 34 modules")
    removed_placement_ids = {
        row["module_item_id"]
        for row in plan["week_zero"]["remove_old_nonprotected_placements"]
    }
    retained_item_ids = ({
        row["id"]
        for module_id in retained_module_ids
        for row in items_by_module[module_id]
    } | {
        move["module_item_id"]
        for move in plan["week_zero"]["move_existing_module_items"]
    }) - removed_placement_ids
    publication_snapshot = {
        "modules": {
            str(module_id): module_by_id[module_id].get("published")
            for module_id in retained_module_ids
        },
        "items": {
            str(item["id"]): item.get("published")
            for rows in items_by_module.values()
            for item in rows
            if item["id"] in retained_item_ids
        },
        "front_page": extras["front"].get("published"),
        "protected_assignments": {
            str(row["id"]): row.get("published")
            for row in extras["protected_assignments"]
        },
        "repair_assignments": {
            str(row["id"]): row.get("published")
            for row in extras["repair_assignments"]
        },
    }

    touched = {
        "assignment_descriptions": [],
        "moved_module_items": [],
        "removed_week_zero_placements": [],
        "positioned_protected_items": [],
        "updated_homepage": None,
        "removed_module_shells": [],
    }

    audit = load_audit_helpers()
    origins = [
        "https://verizoninnovativelearning.instructure.com",
        "https://learn.irvingisd.net",
    ]
    source_item_by_key = {
        (item["type"], item["title"]): item
        for module in source["modules"]
        for item in module["items"]
    }
    for repair in plan["repairs"]:
        assignment_id = repair["assignment_id"]
        current = canvas.get(
            f"/courses/{plan['course_id']}/assignments/{assignment_id}"
        )
        current_hash = hashlib.sha256(
            (current.get("description") or "").encode("utf-8")
        ).hexdigest()
        if current_hash != repair["current_description_sha256"]:
            raise RuntimeError(
                f"Assignment body changed before write: {assignment_id}"
            )
        canvas.request(
            "PUT",
            f"/courses/{plan['course_id']}/assignments/{assignment_id}",
            {"assignment[description]": repair["description"]},
        )
        readback = canvas.get(
            f"/courses/{plan['course_id']}/assignments/{assignment_id}"
        )
        if assignment_guard(readback, include_description=False) != assignment_guard(
            backup_repairs[assignment_id], include_description=False
        ):
            raise RuntimeError(
                f"Assignment settings changed during repair: {assignment_id}"
            )
        destination_item = next(
            item
            for item in items_by_module[repair["module_id"]]
            if item["id"] == repair["module_item_id"]
        )
        source_item = source_item_by_key[
            (destination_item["type"], destination_item["title"])
        ]
        readback_hash = audit.digest(
            audit.semantic_payload(
                destination_item,
                readback,
                origins,
                link_aliases={},
            )
        )
        if readback_hash != repair["source_semantic_hash"]:
            raise RuntimeError(
                f"Assignment semantic readback mismatch: {assignment_id}"
            )
        touched["assignment_descriptions"].append(assignment_id)

    front_before = canvas.get(
        f"/courses/{plan['course_id']}/pages/{plan['homepage']['destination_url']}"
    )
    if front_before["page_id"] != plan["homepage"]["destination_page_id"]:
        raise RuntimeError("Homepage identity changed before write")
    canvas.request(
        "PUT",
        f"/courses/{plan['course_id']}/pages/{plan['homepage']['destination_url']}",
        {
            "wiki_page[title]": plan["homepage"]["planned_title"],
            "wiki_page[body]": plan["homepage"]["planned_body"],
        },
    )
    front_after = canvas.get(
        f"/courses/{plan['course_id']}/pages/{plan['homepage']['destination_url']}"
    )
    if front_after["page_id"] != plan["homepage"]["destination_page_id"]:
        raise RuntimeError("Homepage was replaced instead of updated in place")
    if front_after.get("title") != plan["homepage"]["planned_title"]:
        raise RuntimeError("Homepage title readback mismatch")
    if hashlib.sha256(
        (front_after.get("body") or "").encode("utf-8")
    ).hexdigest() != plan["homepage"]["planned_body_sha256"]:
        raise RuntimeError("Homepage body readback mismatch")
    if front_after.get("published") != front_before.get("published"):
        raise RuntimeError("Homepage publication changed")
    touched["updated_homepage"] = front_after["page_id"]

    target_module_id = plan["week_zero"]["retained_module_id"]
    for move in plan["week_zero"]["move_existing_module_items"]:
        canvas.request(
            "PUT",
            f"/courses/{plan['course_id']}/modules/{move['from_module_id']}/"
            f"items/{move['module_item_id']}",
            {
                "module_item[module_id]": target_module_id,
                "module_item[position]": move["target_position"],
            },
        )
        target_items = canvas.paged(
            f"/courses/{plan['course_id']}/modules/{target_module_id}/items?per_page=100"
        )
        moved = next(
            (row for row in target_items if row["id"] == move["module_item_id"]),
            None,
        )
        if moved is None:
            raise RuntimeError(
                f"Moved module item missing from target: {move['module_item_id']}"
            )
        touched["moved_module_items"].append(move["module_item_id"])

    for removal in plan["week_zero"]["remove_old_nonprotected_placements"]:
        canvas.request(
            "DELETE",
            f"/courses/{plan['course_id']}/modules/{removal['module_id']}/"
            f"items/{removal['module_item_id']}",
        )
        touched["removed_week_zero_placements"].append(
            removal["module_item_id"]
        )

    for item_id, position in (
        (
            plan["week_zero"]["protected_pre_survey_item_id"],
            plan["week_zero"]["final_pre_survey_position"],
        ),
        (
            plan["week_zero"]["protected_submitted_xello_item_id"],
            plan["week_zero"]["final_submitted_xello_position"],
        ),
    ):
        canvas.request(
            "PUT",
            f"/courses/{plan['course_id']}/modules/{target_module_id}/items/{item_id}",
            {"module_item[position]": position},
        )
        touched["positioned_protected_items"].append(item_id)

    target_items = canvas.paged(
        f"/courses/{plan['course_id']}/modules/{target_module_id}/items?per_page=100"
    )
    if len(target_items) != 20:
        raise RuntimeError("Retained Week 0 does not have 20 planned placements")
    expected_week_zero = [
        (item["type"], item["title"])
        for item in sorted(source["modules"], key=lambda row: row["position"])[0][
            "items"
        ]
    ]
    actual_without_local = [
        (item["type"], item["title"])
        for item in target_items
        if item["id"] != plan["week_zero"]["protected_pre_survey_item_id"]
    ]
    if actual_without_local != expected_week_zero:
        raise RuntimeError("Retained Week 0 canonical order mismatch")

    for module_id in plan["obsolete_module_shell_ids"]:
        if module_id not in module_by_id:
            raise RuntimeError(f"Obsolete module shell disappeared: {module_id}")
        canvas.request(
            "DELETE", f"/courses/{plan['course_id']}/modules/{module_id}"
        )
        touched["removed_module_shells"].append(module_id)

    final_modules = canvas.paged(f"/courses/{plan['course_id']}/modules?per_page=100")
    final_items = {
        module["id"]: canvas.paged(
            f"/courses/{plan['course_id']}/modules/{module['id']}/items?per_page=100"
        )
        for module in final_modules
    }
    if len(final_modules) != plan["final_gate"]["module_count"]:
        raise RuntimeError("Final module count mismatch")
    if sum(len(rows) for rows in final_items.values()) != plan["final_gate"][
        "item_count"
    ]:
        raise RuntimeError("Final module-item count mismatch")
    final_modules_sorted = sorted(final_modules, key=lambda row: row["position"])
    source_modules_sorted = sorted(source["modules"], key=lambda row: row["position"])
    if [row["name"] for row in final_modules_sorted] != [
        row["name"] for row in source_modules_sorted
    ]:
        raise RuntimeError("Final canonical module name/order mismatch")
    for index, (source_module, destination_module) in enumerate(
        zip(source_modules_sorted, final_modules_sorted)
    ):
        rows = final_items[destination_module["id"]]
        if index == 0:
            rows = [
                row
                for row in rows
                if row["id"]
                != plan["week_zero"]["protected_pre_survey_item_id"]
            ]
        if [(row["type"], row["title"]) for row in rows] != [
            (row["type"], row["title"]) for row in source_module["items"]
        ]:
            raise RuntimeError(
                f"Final canonical item order mismatch: {destination_module['id']}"
            )

    final_module_by_id = {row["id"]: row for row in final_modules}
    final_item_by_id = {
        row["id"]: row for rows in final_items.values() for row in rows
    }
    final_publication = {
        "modules": {
            module_id: final_module_by_id[int(module_id)].get("published")
            for module_id in publication_snapshot["modules"]
        },
        "items": {
            item_id: final_item_by_id[int(item_id)].get("published")
            for item_id in publication_snapshot["items"]
        },
        "front_page": canvas.get(
            f"/courses/{plan['course_id']}/pages/{plan['homepage']['destination_url']}"
        ).get("published"),
        "protected_assignments": {
            assignment_id: canvas.get(
                f"/courses/{plan['course_id']}/assignments/{assignment_id}"
            ).get("published")
            for assignment_id in publication_snapshot["protected_assignments"]
        },
        "repair_assignments": {
            assignment_id: canvas.get(
                f"/courses/{plan['course_id']}/assignments/{assignment_id}"
            ).get("published")
            for assignment_id in publication_snapshot["repair_assignments"]
        },
    }
    if final_publication != publication_snapshot:
        raise RuntimeError("Publication readback changed during recovery")

    final_protected = [
        canvas.get(f"/courses/{plan['course_id']}/assignments/{assignment_id}")
        for assignment_id in plan["protected"]["assignment_ids"]
    ]
    backup_protected = {
        row["id"]: row for row in backup["protected_assignments"]
    }
    for row in final_protected:
        if assignment_guard(row) != assignment_guard(backup_protected[row["id"]]):
            raise RuntimeError(
                f"Protected submitted assignment changed: {row['id']}"
            )

    result = {
        "schema_version": 1,
        "completed_at": datetime.now(timezone.utc).isoformat(),
        "status": "APPLIED_AND_VERIFIED",
        "course_id": plan["course_id"],
        "plan": str(plan_path),
        "plan_sha256": args.plan_sha256,
        "approval_note": args.approval_note,
        "preflight_sha256": guard_hash,
        "touched": touched,
        "final": {
            "module_count": len(final_modules),
            "item_count": sum(len(rows) for rows in final_items.values()),
            "homepage_id": front_after["page_id"],
            "homepage_title": front_after["title"],
            "protected_assignment_ids": [row["id"] for row in final_protected],
            "publication_readback_unchanged": True,
        },
    }
    result_path = args.result.expanduser().resolve()
    write_sealed(result_path, result)
    print(stable_json({**result, "result": str(result_path)}), end="")


if __name__ == "__main__":
    main()
