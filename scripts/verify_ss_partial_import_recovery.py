#!/usr/bin/env python3
"""Read-only final verifier for an approved SS partial-import recovery."""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from apply_ss_partial_import_recovery import assignment_guard
from canvas_api import Canvas, stable_json
from plan_ss_legacy_rebootstrap import IRVING_API, sha256_file, verify_seal, write_sealed
from plan_ss_partial_import_recovery import load_audit_helpers


ACTIVE_MIGRATION_STATES = {
    "queued",
    "pre_processing",
    "running",
    "waiting_for_select",
}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True, type=Path)
    parser.add_argument("--plan-sha256", required=True)
    parser.add_argument("--source-snapshot", required=True, type=Path)
    parser.add_argument("--result", required=True, type=Path)
    args = parser.parse_args()

    plan_path = args.plan.expanduser().resolve()
    verify_seal(plan_path)
    if sha256_file(plan_path) != args.plan_sha256:
        raise RuntimeError("Approved amended plan hash does not match")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    backup_path = Path(plan["destination_preflight"]["backup"])
    verify_seal(backup_path)
    if sha256_file(backup_path) != plan["destination_preflight"]["backup_sha256"]:
        raise RuntimeError("Post-import backup hash does not match")
    backup = json.loads(backup_path.read_text(encoding="utf-8"))
    source = json.loads(args.source_snapshot.read_text(encoding="utf-8"))
    if source.get("semantic_sha256") != plan["source"]["semantic_sha256"]:
        raise RuntimeError("Canonical source changed before final verification")

    canvas = Canvas(base=IRVING_API)
    course_id = plan["course_id"]
    modules = canvas.paged(f"/courses/{course_id}/modules?per_page=100")
    items = {
        module["id"]: canvas.paged(
            f"/courses/{course_id}/modules/{module['id']}/items?per_page=100"
        )
        for module in modules
    }
    module_by_id = {module["id"]: module for module in modules}
    item_by_id = {item["id"]: item for rows in items.values() for item in rows}
    if len(modules) != plan["final_gate"]["module_count"]:
        raise RuntimeError("Final module count mismatch")
    if sum(len(rows) for rows in items.values()) != plan["final_gate"]["item_count"]:
        raise RuntimeError("Final module-item count mismatch")

    source_modules = sorted(source["modules"], key=lambda row: row["position"])
    final_modules = sorted(modules, key=lambda row: row["position"])
    if [row["name"] for row in final_modules] != [
        row["name"] for row in source_modules
    ]:
        raise RuntimeError("Final canonical module name/order mismatch")
    for index, (source_module, destination_module) in enumerate(
        zip(source_modules, final_modules)
    ):
        destination_items = items[destination_module["id"]]
        if index == 0:
            destination_items = [
                row
                for row in destination_items
                if row["id"]
                != plan["week_zero"]["protected_pre_survey_item_id"]
            ]
        if [
            (row["type"], row["title"]) for row in destination_items
        ] != [
            (row["type"], row["title"]) for row in source_module["items"]
        ]:
            raise RuntimeError(
                f"Final canonical item order mismatch: {destination_module['id']}"
            )

    backup_modules = {row["id"]: row for row in backup["modules"]}
    backup_items = {
        item["id"]: item for module in backup["modules"] for item in module["items"]
    }
    if not all(
        module_by_id[module_id].get("published")
        == backup_modules[module_id].get("published")
        for module_id in module_by_id
    ):
        raise RuntimeError("Retained module publication changed")
    if not all(
        item_by_id[item_id].get("published")
        == backup_items[item_id].get("published")
        for item_id in item_by_id
    ):
        raise RuntimeError("Retained module-item publication changed")

    page_summaries = canvas.paged(f"/courses/{course_id}/pages?per_page=100")
    front_summary = next(row for row in page_summaries if row.get("front_page"))
    front = canvas.get(f"/courses/{course_id}/pages/{front_summary['url']}")
    if front["page_id"] != plan["homepage"]["destination_page_id"]:
        raise RuntimeError("Homepage identity changed")
    if front["title"] != plan["homepage"]["planned_title"]:
        raise RuntimeError("Homepage title mismatch")
    if hashlib.sha256((front.get("body") or "").encode("utf-8")).hexdigest() != plan[
        "homepage"
    ]["planned_body_sha256"]:
        raise RuntimeError("Homepage body mismatch")
    if front.get("published") != backup["front_page"].get("published"):
        raise RuntimeError("Homepage publication changed")

    protected_backup = {
        row["id"]: row for row in backup["protected_assignments"]
    }
    protected = []
    for assignment_id in plan["protected"]["assignment_ids"]:
        assignment = canvas.get(f"/courses/{course_id}/assignments/{assignment_id}")
        if assignment_guard(assignment) != assignment_guard(
            protected_backup[assignment_id]
        ):
            raise RuntimeError(
                f"Protected submitted assignment changed: {assignment_id}"
            )
        if not assignment.get("has_submitted_submissions"):
            raise RuntimeError(f"Submission hold disappeared: {assignment_id}")
        protected.append(assignment_id)
    protected_quiz_id = plan["protected"]["quiz_ids"][0]
    protected_quiz = canvas.get(f"/courses/{course_id}/quizzes/{protected_quiz_id}")
    if protected_quiz.get("assignment_id") not in protected:
        raise RuntimeError("Protected quiz lost its submitted assignment identity")

    audit = load_audit_helpers()
    origins = [
        "https://verizoninnovativelearning.instructure.com",
        "https://learn.irvingisd.net",
    ]
    source_by_key = {
        (item["type"], item["title"]): item
        for module in source_modules
        for item in module["items"]
    }
    repair_backup = {row["id"]: row for row in backup["repair_assignments"]}
    repaired = []
    for repair in plan["repairs"]:
        assignment = canvas.get(
            f"/courses/{course_id}/assignments/{repair['assignment_id']}"
        )
        if assignment.get("has_submitted_submissions"):
            raise RuntimeError(
                f"Repaired assignment gained submissions: {assignment['id']}"
            )
        if assignment_guard(
            assignment, include_description=False
        ) != assignment_guard(
            repair_backup[assignment["id"]], include_description=False
        ):
            raise RuntimeError(
                f"Repaired assignment settings changed: {assignment['id']}"
            )
        destination_item = item_by_id[repair["module_item_id"]]
        source_item = source_by_key[
            (destination_item["type"], destination_item["title"])
        ]
        live_hash = audit.digest(
            audit.semantic_payload(
                destination_item,
                assignment,
                origins,
                link_aliases={},
            )
        )
        if live_hash != repair["source_semantic_hash"]:
            raise RuntimeError(
                f"Repaired assignment is not canonical: {assignment['id']}"
            )
        repaired.append(assignment["id"])

    if set(plan["obsolete_module_shell_ids"]) & set(module_by_id):
        raise RuntimeError("An obsolete module shell remains")
    active_migrations = [
        row
        for row in canvas.paged(f"/courses/{course_id}/content_migrations?per_page=100")
        if row.get("workflow_state") in ACTIVE_MIGRATION_STATES
    ]
    if active_migrations:
        raise RuntimeError("A content migration is still active")

    result = {
        "schema_version": 1,
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "status": "APPLIED_AND_VERIFIED",
        "course_id": course_id,
        "plan": str(plan_path),
        "plan_sha256": args.plan_sha256,
        "final": {
            "module_count": len(modules),
            "item_count": sum(len(rows) for rows in items.values()),
            "canonical_item_count": plan["final_gate"]["canonical_item_count"],
            "local_submitted_extra_count": plan["final_gate"][
                "local_submitted_extra_count"
            ],
            "homepage_id": front["page_id"],
            "homepage_url": front["url"],
            "homepage_title": front["title"],
            "protected_assignment_ids": protected,
            "repaired_assignment_ids": repaired,
            "obsolete_module_shells_remaining": 0,
            "active_migrations": 0,
            "publication_readback_unchanged": True,
        },
    }
    result_path = args.result.expanduser().resolve()
    write_sealed(result_path, result)
    print(stable_json({**result, "result": str(result_path)}), end="")


if __name__ == "__main__":
    main()
