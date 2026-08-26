#!/usr/bin/env python3
"""Seal a recovery plan after a partial Smart Solutions cartridge import.

The command is read-only with respect to Canvas.  It is intentionally narrow:
the canonical import must already have updated one complete 34-module lineage,
the submitted Week 0 objects must remain in a second lineage, and migration
issues must identify assignment bodies that can be repaired from verified
source files.  The emitted plan contains exact payloads and guards; it does not
authorize or perform the recovery.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import re
import sys
import urllib.parse
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


EXPECTED_IMPORT_ERROR_TITLES = {
    "Day 1 · Drawing Mission: Plan, Program, Prove",
    "Day 2 · Precision Movement Lab",
    "Day 3 · Color Sensor Mission",
    "Day 4 · Train It + Connect It",
    "Days 4 + 5 · Talking Robots: School-of-Fish Challenge",
    "Lesson 2: Graphic Design with Canva",
    "OPTION · Vision Board",
    "Step 1: Define",
}
KNOWN_LINK_WARNING_COUNT = 16


def load_audit_helpers():
    path = (
        Path.home()
        / ".codex"
        / "skills"
        / "canvas-fleet-parity"
        / "scripts"
        / "fleet_audit.py"
    )
    spec = importlib.util.spec_from_file_location("fleet_audit_for_recovery", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load semantic audit helpers: {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def rewrite_file_links(
    body: str,
    source_file_ids: list[int],
    file_map: dict[int, dict],
    *,
    course_id: int,
) -> str:
    for source_id in source_file_ids:
        destination = file_map[source_id]
        verifier_match = re.search(
            r"[?&]verifier=([^&]+)", destination.get("url") or ""
        )
        if not verifier_match:
            raise RuntimeError(
                f"Destination file {destination['id']} has no verifier URL"
            )
        verifier = verifier_match.group(1)
        pattern = re.compile(
            rf"https://verizoninnovativelearning\.instructure\.com/"
            rf"courses/23402/files/{source_id}([^\"']*)"
        )

        def replacement(match: re.Match[str]) -> str:
            suffix = match.group(1)
            suffix = re.sub(
                r"((?:\?|&|&amp;)verifier=)[^&\"']+",
                lambda found: found.group(1) + verifier,
                suffix,
            )
            return (
                f"https://learn.irvingisd.net/courses/{course_id}/files/"
                f"{destination['id']}{suffix}"
            )

        body = pattern.sub(replacement, body)
        body = body.replace(
            "https://verizoninnovativelearning.instructure.com/api/v1/"
            f"courses/23402/files/{source_id}",
            f"https://learn.irvingisd.net/api/v1/courses/{course_id}/files/"
            f"{destination['id']}",
        )
    if "verizoninnovativelearning.instructure.com/courses/23402/files/" in body:
        raise RuntimeError("A source file URL remains after rewrite")
    return body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--course-id", type=int, required=True)
    parser.add_argument("--course-label", required=True)
    parser.add_argument("--original-plan", type=Path, required=True)
    parser.add_argument("--approved-original-plan-sha256", required=True)
    parser.add_argument("--migration-id", type=int, required=True)
    parser.add_argument("--source-snapshot", type=Path, required=True)
    parser.add_argument("--current-lineage-min", type=int, required=True)
    parser.add_argument("--current-lineage-max", type=int, required=True)
    parser.add_argument("--retained-week-zero-module", type=int, required=True)
    parser.add_argument("--source-home-page-url", required=True)
    parser.add_argument("--destination-front-page-url", required=True)
    parser.add_argument("--protected-assignment", action="append", type=int, default=[])
    parser.add_argument("--protected-quiz", action="append", type=int, default=[])
    parser.add_argument("--protected-module-item", action="append", type=int, default=[])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    original_plan_path = args.original_plan.expanduser().resolve()
    verify_seal(original_plan_path)
    if sha256_file(original_plan_path) != args.approved_original_plan_sha256:
        raise RuntimeError("Original approved plan hash does not match")
    original = json.loads(original_plan_path.read_text(encoding="utf-8"))
    if original["course_id"] != args.course_id:
        raise RuntimeError("Original plan targets a different course")

    snapshot_path = args.source_snapshot.expanduser().resolve()
    source = json.loads(snapshot_path.read_text(encoding="utf-8"))
    if source.get("semantic_sha256") != original["approved_source"]["semantic_sha256"]:
        raise RuntimeError("Source snapshot changed after original approval")
    source_modules = sorted(source["modules"], key=lambda row: row["position"])
    source_item_count = sum(len(row["items"]) for row in source_modules)
    if len(source_modules) != 34 or source_item_count != 510:
        raise RuntimeError("Recovery expects the approved 34-module/510-item source")

    canvas = Canvas(base=IRVING_API)
    migration = canvas.get(
        f"/courses/{args.course_id}/content_migrations/{args.migration_id}"
    )
    progress = canvas.get(migration["progress_url"])
    if migration.get("workflow_state") != "completed" or progress.get(
        "workflow_state"
    ) != "completed":
        raise RuntimeError("Content migration is not terminal-complete")
    issues = canvas.paged(
        f"/courses/{args.course_id}/content_migrations/{args.migration_id}/"
        "migration_issues?per_page=100"
    )
    import_error_titles = {
        match.group(1)
        for issue in issues
        if (
            match := re.fullmatch(
                r'Import Error: Assignment - "(.+)"', issue.get("description") or ""
            )
        )
    }
    link_warnings = [
        issue
        for issue in issues
        if issue.get("description")
        == "Missing links found in imported content - Assignment description"
    ]
    if import_error_titles != EXPECTED_IMPORT_ERROR_TITLES:
        raise RuntimeError(
            f"Unexpected assignment import errors: {sorted(import_error_titles)}"
        )
    if len(link_warnings) != KNOWN_LINK_WARNING_COUNT:
        raise RuntimeError("Unexpected migration link-warning count")
    if len(issues) != len(EXPECTED_IMPORT_ERROR_TITLES) + KNOWN_LINK_WARNING_COUNT:
        raise RuntimeError("Unexpected migration issue type")

    modules = canvas.paged(f"/courses/{args.course_id}/modules?per_page=100")
    items_by_module = {
        module["id"]: canvas.paged(
            f"/courses/{args.course_id}/modules/{module['id']}/items?per_page=100"
        )
        for module in modules
    }
    current_modules = sorted(
        [
            module
            for module in modules
            if args.current_lineage_min <= module["id"] <= args.current_lineage_max
        ],
        key=lambda row: row["id"],
    )
    if len(current_modules) != 34:
        raise RuntimeError("Current imported lineage does not contain 34 modules")
    for source_module, destination_module in zip(source_modules, current_modules):
        destination_items = items_by_module[destination_module["id"]]
        if destination_module["name"] != source_module["name"]:
            raise RuntimeError(
                f"Canonical module name mismatch: {destination_module['id']}"
            )
        if [
            (item["type"], item["title"]) for item in destination_items
        ] != [
            (item["type"], item["title"]) for item in source_module["items"]
        ]:
            raise RuntimeError(
                f"Canonical item signature mismatch: {destination_module['id']}"
            )

    protected_assignments = [
        canvas.get(f"/courses/{args.course_id}/assignments/{assignment_id}")
        for assignment_id in sorted(set(args.protected_assignment))
    ]
    if not protected_assignments or not all(
        row.get("has_submitted_submissions") for row in protected_assignments
    ):
        raise RuntimeError("A protected submitted assignment lost its submission hold")
    protected_items = {
        item["id"]: (module_id, item)
        for module_id, rows in items_by_module.items()
        for item in rows
        if item["id"] in set(args.protected_module_item)
    }
    if set(protected_items) != set(args.protected_module_item):
        raise RuntimeError("A protected module item is missing")
    if {module_id for module_id, _ in protected_items.values()} != {
        args.retained_week_zero_module
    }:
        raise RuntimeError("Protected placements moved out of retained Week 0")

    files_needed = {
        file_id
        for module in source_modules
        for item in module["items"]
        if item["title"] in import_error_titles
        for file_id in (item.get("resource") or {}).get("referenced_file_ids") or []
    }
    file_map: dict[int, dict] = {}
    for source_file_id in sorted(files_needed):
        source_file = source["files"][str(source_file_id)]
        name = source_file["metadata"]["display_name"]
        candidates = canvas.paged(
            f"/courses/{args.course_id}/files?per_page=100&search_term="
            + urllib.parse.quote(name)
        )
        exact = [row for row in candidates if row.get("display_name") == name]
        if len(exact) != 1:
            raise RuntimeError(f"Destination file identity is ambiguous: {name}")
        destination_file = exact[0]
        actual_hash = hashlib.sha256(
            canvas.download(destination_file["url"])
        ).hexdigest()
        if actual_hash != source_file["sha256"]:
            raise RuntimeError(f"Destination file differs from source: {name}")
        file_map[source_file_id] = destination_file

    audit = load_audit_helpers()
    origins = [
        "https://verizoninnovativelearning.instructure.com",
        "https://learn.irvingisd.net",
    ]
    repairs = []
    for source_module, destination_module in zip(source_modules, current_modules):
        destination_items = items_by_module[destination_module["id"]]
        for source_item, destination_item in zip(
            source_module["items"], destination_items
        ):
            if source_item["title"] not in import_error_titles:
                continue
            assignment_id = destination_item.get("content_id")
            assignment = canvas.get(
                f"/courses/{args.course_id}/assignments/{assignment_id}"
            )
            if assignment.get("has_submitted_submissions"):
                raise RuntimeError(
                    f"Import-error assignment has submissions: {assignment_id}"
                )
            source_resource = source_item["resource"]
            description = rewrite_file_links(
                source_resource.get("body") or "",
                source_resource.get("referenced_file_ids") or [],
                file_map,
                course_id=args.course_id,
            )
            planned_detail = {**assignment, "description": description}
            source_hash = audit.digest(
                audit.semantic_payload(
                    source_item,
                    None,
                    origins,
                    snapshot_resource=source_resource,
                    link_aliases={},
                )
            )
            planned_hash = audit.digest(
                audit.semantic_payload(
                    destination_item,
                    planned_detail,
                    origins,
                    link_aliases={},
                )
            )
            if source_hash != planned_hash:
                raise RuntimeError(
                    f"Planned repair is not semantically canonical: {assignment_id}"
                )
            repairs.append(
                {
                    "assignment_id": assignment_id,
                    "module_id": destination_module["id"],
                    "module_item_id": destination_item["id"],
                    "title": destination_item["title"],
                    "current_description_sha256": hashlib.sha256(
                        (assignment.get("description") or "").encode("utf-8")
                    ).hexdigest(),
                    "planned_description_sha256": hashlib.sha256(
                        description.encode("utf-8")
                    ).hexdigest(),
                    "source_semantic_hash": source_hash,
                    "planned_semantic_hash": planned_hash,
                    "description": description,
                    "file_map": {
                        str(file_id): file_map[file_id]["id"]
                        for file_id in source_resource.get("referenced_file_ids") or []
                    },
                }
            )
    if len(repairs) != len(EXPECTED_IMPORT_ERROR_TITLES):
        raise RuntimeError("Did not resolve every assignment import error")

    page_summaries = canvas.paged(f"/courses/{args.course_id}/pages?per_page=100")
    front_summary = next(
        row for row in page_summaries if row.get("front_page")
    )
    if front_summary["url"] != args.destination_front_page_url:
        raise RuntimeError("Destination front page changed unexpectedly")
    front_page = canvas.get(
        f"/courses/{args.course_id}/pages/{front_summary['url']}"
    )
    source_home = canvas.get(
        f"/courses/{args.course_id}/pages/{args.source_home_page_url}"
    )
    if source_home["title"] != "Student Home — Smart Solutions":
        raise RuntimeError("Imported source homepage is not the expected page")

    current_week_zero = current_modules[0]
    current_week_zero_items = items_by_module[current_week_zero["id"]]
    canonical_xello = next(
        row
        for row in current_week_zero_items
        if row["title"] == "Xello Check-in: Log in to Xello"
    )
    move_items = [
        {
            "module_item_id": row["id"],
            "type": row["type"],
            "title": row["title"],
            "from_module_id": current_week_zero["id"],
            "to_module_id": args.retained_week_zero_module,
            "target_position": position,
        }
        for position, row in enumerate(
            [item for item in current_week_zero_items if item["id"] != canonical_xello["id"]],
            start=1,
        )
    ]
    if len(move_items) != 18:
        raise RuntimeError("Week 0 move set is not exactly 18 canonical items")
    protected_by_title = {
        item["title"]: item
        for _, item in protected_items.values()
    }
    pre_survey = protected_by_title.get("Student: Pre-Survey")
    submitted_xello = protected_by_title.get("Xello Check-in: Log in to Xello")
    if pre_survey is None or submitted_xello is None:
        raise RuntimeError("Protected Week 0 submitted placements are incomplete")
    retained_old_items = items_by_module[args.retained_week_zero_module]
    remove_old_placements = [
        {
            "module_id": args.retained_week_zero_module,
            "module_item_id": row["id"],
            "type": row["type"],
            "title": row["title"],
        }
        for row in retained_old_items
        if row["id"] not in set(args.protected_module_item)
    ]
    obsolete_module_ids = [
        row["id"] for row in original["obsolete_existing_module_containers"]
    ]
    if current_week_zero["id"] not in obsolete_module_ids or len(
        obsolete_module_ids
    ) != 34:
        raise RuntimeError("Obsolete module set differs from the approved plan")

    destination_guard = {
        "course_id": args.course_id,
        "modules": [
            module_guard(module, items_by_module[module["id"]]) for module in modules
        ],
        "front_page": {
            "page_id": front_page["page_id"],
            "url": front_page["url"],
            "title": front_page["title"],
            "body": front_page.get("body") or "",
            "front_page": front_page.get("front_page"),
            "editing_roles": front_page.get("editing_roles"),
            "hide_from_students": front_page.get("hide_from_students"),
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
                "id": repair["assignment_id"],
                "description_sha256": repair["current_description_sha256"],
            }
            for repair in repairs
        ],
    }

    now = datetime.now(timezone.utc)
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    backup_path = output / "post-import-backup.json"
    plan_path = output / "plan.json"
    summary_path = output / "plan.md"
    backup = {
        "schema_version": 1,
        "captured_at": now.isoformat(),
        "course_id": args.course_id,
        "migration": migration,
        "migration_progress": progress,
        "migration_issues": issues,
        "modules": [
            {**module, "items": items_by_module[module["id"]]} for module in modules
        ],
        "front_page": front_page,
        "source_home": source_home,
        "protected_assignments": protected_assignments,
        "repair_assignments": [
            canvas.get(
                f"/courses/{args.course_id}/assignments/{repair['assignment_id']}"
            )
            for repair in repairs
        ],
    }
    write_sealed(backup_path, backup)

    plan = {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "status": "AWAITING_EXPLICIT_AMENDED_APPLY_APPROVAL",
        "course_id": args.course_id,
        "course_label": args.course_label,
        "original_approved_plan": {
            "path": str(original_plan_path),
            "sha256": args.approved_original_plan_sha256,
        },
        "partial_import": {
            "migration_id": args.migration_id,
            "workflow_state": migration.get("workflow_state"),
            "issue_count": len(issues),
            "assignment_import_errors": sorted(import_error_titles),
            "known_link_warnings": len(link_warnings),
        },
        "source": {
            "semantic_sha256": source["semantic_sha256"],
            "module_count": len(source_modules),
            "item_count": source_item_count,
        },
        "destination_preflight": {
            "semantic_structure_sha256": sha256_json(destination_guard),
            "module_count": len(modules),
            "item_count": sum(len(rows) for rows in items_by_module.values()),
            "backup": str(backup_path),
            "backup_sha256": sha256_file(backup_path),
        },
        "repairs": repairs,
        "week_zero": {
            "retained_module_id": args.retained_week_zero_module,
            "canonical_source_module_id": current_week_zero["id"],
            "move_existing_module_items": move_items,
            "remove_old_nonprotected_placements": remove_old_placements,
            "protected_pre_survey_item_id": pre_survey["id"],
            "protected_submitted_xello_item_id": submitted_xello["id"],
            "discard_unsubmitted_canonical_xello_placement_with_module_id": canonical_xello[
                "id"
            ],
            "final_pre_survey_position": 19,
            "final_submitted_xello_position": 20,
        },
        "homepage": {
            "destination_page_id": front_page["page_id"],
            "destination_url": front_page["url"],
            "source_page_id": source_home["page_id"],
            "source_url": source_home["url"],
            "planned_title": source_home["title"],
            "planned_body": source_home.get("body") or "",
            "current_body_sha256": hashlib.sha256(
                (front_page.get("body") or "").encode("utf-8")
            ).hexdigest(),
            "planned_body_sha256": hashlib.sha256(
                (source_home.get("body") or "").encode("utf-8")
            ).hexdigest(),
        },
        "obsolete_module_shell_ids": obsolete_module_ids,
        "protected": {
            "assignment_ids": sorted(set(args.protected_assignment)),
            "quiz_ids": sorted(set(args.protected_quiz)),
            "module_item_ids": sorted(set(args.protected_module_item)),
        },
        "allowed_operations": [
            "Update exactly eight unsubmitted assignment descriptions.",
            "Move exactly 18 existing canonical Week 0 module items by module_item[module_id].",
            "Remove exactly 12 old nonprotected Week 0 placements.",
            "Position the protected Pre-Survey and submitted Xello placements at 19 and 20.",
            "Update the existing front-page title/body in place.",
            "Remove exactly 34 obsolete module shells without deleting underlying content.",
        ],
        "forbidden_operations": [
            "Any publication field or publish/unpublish request.",
            "Any update to protected submitted assignments, quiz, or their content settings.",
            "Any deletion of pages, assignments, quizzes, discussions, files, submissions, or grades.",
            "Any CCE access or write.",
        ],
        "final_gate": {
            "module_count": 34,
            "item_count": 511,
            "canonical_item_count": 510,
            "local_submitted_extra_count": 1,
        },
    }
    write_sealed(plan_path, plan)
    plan_hash = sha256_file(plan_path)
    approval = (
        f"Approve amended partial-import recovery plan {plan_hash} for Canvas course "
        f"{args.course_id}."
    )
    summary_path.write_text(
        "\n".join(
            [
                f"# {args.course_label} partial-import recovery plan",
                "",
                f"- Status: **{plan['status']}**",
                f"- Course: `{args.course_id}` — {args.course_label}",
                f"- Original approved plan: `{args.approved_original_plan_sha256}`",
                f"- Partial migration: `{args.migration_id}` — 24 warnings",
                "- Canonical updated lineage: 34 modules / 510 placements",
                "- Assignment-description repairs: 8, all unsubmitted",
                "- Submitted assessments protected: 2",
                "- Obsolete module shells proposed for removal: 34",
                "- Underlying content deletions: 0",
                "- Publication writes: 0",
                "- Final target: 34 modules / 511 placements",
                "",
                "## Exact approval phrase",
                "",
                f"> {approval}",
                "",
            ]
        ),
        encoding="utf-8",
    )
    summary_path.chmod(0o600)
    print(
        stable_json(
            {
                "status": plan["status"],
                "read_only": True,
                "plan": str(plan_path),
                "plan_sha256": plan_hash,
                "backup": str(backup_path),
                "summary": str(summary_path),
                "approval_phrase": approval,
            }
        ),
        end="",
    )


if __name__ == "__main__":
    main()
