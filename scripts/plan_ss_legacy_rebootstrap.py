#!/usr/bin/env python3
"""Create a sealed, read-only Smart Solutions legacy-rebootstrap plan.

This planner is for the narrow case where a teacher course contains duplicate
historical imports that cannot receive Commons updates.  It inventories the
current course, records submitted-assessment holds, and pins a proposed module
container mapping to the approved Verizon source package.  It performs no
Canvas writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from canvas_api import Canvas, stable_json


IRVING_API = "https://learn.irvingisd.net/api/v1"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sha256_json(value: object) -> str:
    encoded = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def write_sealed(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    path.write_text(stable_json(value), encoding="utf-8")
    path.chmod(0o600)
    seal = path.with_suffix(path.suffix + ".sha256")
    seal.write_text(f"{sha256_file(path)}  {path.name}\n", encoding="utf-8")
    seal.chmod(0o600)


def verify_seal(path: Path) -> None:
    seal = path.with_suffix(path.suffix + ".sha256")
    if not seal.is_file():
        raise RuntimeError(f"Required SHA-256 seal is missing: {seal}")
    recorded = seal.read_text(encoding="utf-8").split()[0]
    if recorded != sha256_file(path):
        raise RuntimeError(f"SHA-256 seal does not match: {path}")


def parse_keep_module(value: str) -> tuple[int, int]:
    try:
        position_text, module_text = value.split("=", 1)
        position, module_id = int(position_text), int(module_text)
    except (ValueError, TypeError) as exc:
        raise argparse.ArgumentTypeError(
            "--keep-module must use SOURCE_POSITION=DESTINATION_MODULE_ID"
        ) from exc
    if position < 1 or module_id < 1:
        raise argparse.ArgumentTypeError("module positions and IDs must be positive")
    return position, module_id


def module_guard(module: dict, items: list[dict]) -> dict:
    """Return publication-neutral structure used as an apply preflight guard."""
    return {
        "id": module["id"],
        "name": module["name"],
        "position": module["position"],
        "unlock_at": module.get("unlock_at"),
        "require_sequential_progress": module.get("require_sequential_progress"),
        "prerequisite_module_ids": module.get("prerequisite_module_ids") or [],
        "items": [
            {
                "id": item["id"],
                "position": item["position"],
                "type": item["type"],
                "title": item["title"],
                "content_id": item.get("content_id"),
                "page_url": item.get("page_url"),
                "external_url": item.get("external_url"),
                "indent": item.get("indent", 0),
                "completion_requirement": item.get("completion_requirement"),
            }
            for item in items
        ],
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--course-id", required=True, type=int)
    parser.add_argument("--course-label", required=True)
    parser.add_argument("--package", required=True, type=Path)
    parser.add_argument("--package-manifest", required=True, type=Path)
    parser.add_argument("--release", required=True, type=Path)
    parser.add_argument("--source-snapshot", required=True, type=Path)
    parser.add_argument("--keep-module", action="append", type=parse_keep_module, required=True)
    parser.add_argument("--protected-assignment", action="append", type=int, default=[])
    parser.add_argument("--protected-quiz", action="append", type=int, default=[])
    parser.add_argument("--protected-module-item", action="append", type=int, default=[])
    parser.add_argument("--front-page-url", required=True)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()

    package = args.package.expanduser().resolve()
    package_manifest_path = args.package_manifest.expanduser().resolve()
    release_path = args.release.expanduser().resolve()
    snapshot_path = args.source_snapshot.expanduser().resolve()
    for path in (package, package_manifest_path, release_path, snapshot_path):
        if not path.is_file():
            raise RuntimeError(f"Required input is missing: {path}")
    verify_seal(package_manifest_path)
    verify_seal(release_path)

    package_manifest = json.loads(package_manifest_path.read_text(encoding="utf-8"))
    release = json.loads(release_path.read_text(encoding="utf-8"))
    source = json.loads(snapshot_path.read_text(encoding="utf-8"))
    package_hash = sha256_file(package)
    expected_package_hash = package_manifest.get("sha256") or package_manifest.get(
        "package_sha256"
    )
    if package_hash != expected_package_hash:
        raise RuntimeError("Source package hash does not match its manifest")
    source_hash = source.get("semantic_sha256")
    if source_hash != release.get("snapshot", {}).get("semantic_sha256"):
        raise RuntimeError("Approved release and source snapshot semantic hashes differ")
    source_modules = sorted(source["modules"], key=lambda row: row["position"])
    source_item_count = sum(len(module["items"]) for module in source_modules)

    keep_map = dict(args.keep_module)
    if len(keep_map) != len(args.keep_module):
        raise RuntimeError("Duplicate source positions in --keep-module mapping")
    if set(keep_map) != set(range(1, len(source_modules) + 1)):
        raise RuntimeError("Keep mapping must cover every canonical source position exactly")
    if len(set(keep_map.values())) != len(keep_map):
        raise RuntimeError("A destination module cannot represent two source modules")

    canvas = Canvas(base=IRVING_API)
    course = canvas.get(f"/courses/{args.course_id}")
    modules = canvas.paged(f"/courses/{args.course_id}/modules?per_page=100")
    items_by_module = {
        module["id"]: canvas.paged(
            f"/courses/{args.course_id}/modules/{module['id']}/items?per_page=100"
        )
        for module in modules
    }
    live_module_ids = {module["id"] for module in modules}
    if not set(keep_map.values()).issubset(live_module_ids):
        missing = sorted(set(keep_map.values()) - live_module_ids)
        raise RuntimeError(f"Mapped destination modules are missing: {missing}")

    assignments = canvas.paged(f"/courses/{args.course_id}/assignments?per_page=100")
    submitted_assignment_ids = {
        assignment["id"]
        for assignment in assignments
        if assignment.get("has_submitted_submissions")
    }
    protected_assignments = set(args.protected_assignment)
    if submitted_assignment_ids != protected_assignments:
        raise RuntimeError(
            "Submitted-assessment guard mismatch. "
            f"Live={sorted(submitted_assignment_ids)} "
            f"declared={sorted(protected_assignments)}"
        )
    assignment_by_id = {row["id"]: row for row in assignments}
    protected_assignment_details = [
        canvas.get(f"/courses/{args.course_id}/assignments/{assignment_id}")
        for assignment_id in sorted(protected_assignments)
    ]
    protected_quiz_details = [
        canvas.get(f"/courses/{args.course_id}/quizzes/{quiz_id}")
        for quiz_id in sorted(set(args.protected_quiz))
    ]
    quiz_assignment_ids = {
        row.get("assignment_id") for row in protected_quiz_details if row.get("assignment_id")
    }
    if not quiz_assignment_ids.issubset(protected_assignments):
        raise RuntimeError("A protected quiz is not backed by a protected submitted assignment")

    protected_item_ids = set(args.protected_module_item)
    all_items = [item for rows in items_by_module.values() for item in rows]
    item_by_id = {row["id"]: row for row in all_items}
    if not protected_item_ids.issubset(item_by_id):
        raise RuntimeError("A protected module item is not present in the live course")
    protected_content_ids = {
        item_by_id[item_id].get("content_id") for item_id in protected_item_ids
    }
    # A classic-quiz module item stores the quiz ID as content_id, while Canvas
    # reports submission state on the quiz's linked assignment.  Direct
    # assignment placements store the assignment ID.  Protect both records,
    # but compare module placements against the identifier type they contain.
    expected_protected_content = (
        protected_assignments - quiz_assignment_ids
    ) | set(args.protected_quiz)
    if protected_content_ids != expected_protected_content:
        raise RuntimeError(
            "Protected placement content IDs do not match submitted assignment/quiz holds"
        )

    pages = canvas.paged(f"/courses/{args.course_id}/pages?per_page=100")
    front_pages = [row for row in pages if row.get("front_page")]
    if len(front_pages) != 1 or front_pages[0]["url"] != args.front_page_url:
        raise RuntimeError("Declared front page does not match the live Canvas front page")
    front_page = canvas.get(
        f"/courses/{args.course_id}/pages/{args.front_page_url}"
    )

    module_guards = [
        module_guard(module, items_by_module[module["id"]])
        for module in modules
    ]
    destination_guard = {
        "course_id": args.course_id,
        "course_name": course.get("name"),
        "modules": module_guards,
        "front_page": {
            "page_id": front_page["page_id"],
            "url": front_page["url"],
            "title": front_page["title"],
            "body": front_page.get("body") or "",
            "front_page": front_page.get("front_page"),
            "editing_roles": front_page.get("editing_roles"),
            "hide_from_students": front_page.get("hide_from_students"),
        },
        "submitted_assessments": [
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
            for row in protected_assignment_details
        ],
    }
    destination_hash = sha256_json(destination_guard)

    kept_ids = set(keep_map.values())
    obsolete_modules = [
        {
            "id": module["id"],
            "name": module["name"],
            "position": module["position"],
            "item_count": len(items_by_module[module["id"]]),
            "published_readback_only": module.get("published"),
        }
        for module in modules
        if module["id"] not in kept_ids
    ]
    kept_modules = []
    for source_module in source_modules:
        destination_id = keep_map[source_module["position"]]
        destination_module = next(row for row in modules if row["id"] == destination_id)
        protected_here = sorted(
            item_id
            for item_id in protected_item_ids
            if item_by_id[item_id] in items_by_module[destination_id]
        )
        kept_modules.append(
            {
                "source_module_id": source_module["id"],
                "source_position": source_module["position"],
                "canonical_name": source_module["name"],
                "canonical_item_count": len(source_module["items"]),
                "destination_module_id": destination_id,
                "current_name": destination_module["name"],
                "current_position": destination_module["position"],
                "current_item_count": len(items_by_module[destination_id]),
                "published_readback_only": destination_module.get("published"),
                "protected_module_item_ids": protected_here,
            }
        )

    now = datetime.now(timezone.utc)
    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=False, mode=0o700)
    backup_path = output / "destination-backup.json"
    plan_path = output / "plan.json"
    summary_path = output / "plan.md"
    backup = {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "read_only_capture": True,
        "course": course,
        "modules": [
            {**module, "items": items_by_module[module["id"]]} for module in modules
        ],
        "front_page": front_page,
        "protected_assignments": protected_assignment_details,
        "protected_quizzes": protected_quiz_details,
    }
    write_sealed(backup_path, backup)

    plan = {
        "schema_version": 1,
        "generated_at": now.isoformat(),
        "status": "AWAITING_EXPLICIT_APPLY_APPROVAL",
        "course_id": args.course_id,
        "course_label": args.course_label,
        "course_name": course.get("name"),
        "approved_source": {
            "semantic_sha256": source_hash,
            "module_count": len(source_modules),
            "item_count": source_item_count,
            "release_manifest": str(release_path),
            "package": str(package),
            "package_sha256": package_hash,
            "package_size": package.stat().st_size,
        },
        "destination_preflight": {
            "semantic_structure_sha256": destination_hash,
            "module_count": len(modules),
            "item_count": len(all_items),
            "front_page_id": front_page["page_id"],
            "front_page_url": front_page["url"],
            "backup": str(backup_path),
            "backup_sha256": sha256_file(backup_path),
        },
        "protected": {
            "submitted_assignment_ids": sorted(protected_assignments),
            "submitted_quiz_ids": sorted(set(args.protected_quiz)),
            "submitted_module_item_ids": sorted(protected_item_ids),
            "policy": (
                "Do not update, replace, delete, move out of the retained Week 0 "
                "module, or change dates/settings/publication on these objects."
            ),
        },
        "kept_module_containers": kept_modules,
        "obsolete_existing_module_containers": obsolete_modules,
        "planned_operations": [
            {
                "step": 1,
                "operation": "preflight",
                "detail": (
                    "Re-read the destination and require the publication-neutral "
                    "structure hash to match this plan exactly."
                ),
            },
            {
                "step": 2,
                "operation": "import_current_source_as_staging",
                "detail": (
                    "Import the sealed cartridge with all course settings and "
                    "visibility settings skipped. Stop on any migration issue or if "
                    f"the result is not exactly {len(source_modules)} modules and "
                    f"{source_item_count} canonical items."
                ),
            },
            {
                "step": 3,
                "operation": "rebuild_retained_module_structure",
                "detail": (
                    "Keep the listed 34 destination module IDs and their existing "
                    "publication choices. Replace only module-item placements with "
                    "the staged canonical placements; retain the two submitted Week 0 "
                    "placements and use the existing submitted Xello assignment instead "
                    "of the staged copy. Retain Student: Pre-Survey as a local extra."
                ),
            },
            {
                "step": 4,
                "operation": "canonicalize_module_names_order_structure",
                "detail": (
                    "Update retained module names and positions to the canonical map. "
                    "Omit every module[published] and item publication parameter."
                ),
            },
            {
                "step": 5,
                "operation": "update_homepage_in_place",
                "detail": (
                    "Update the existing destination front-page ID in place using the "
                    "staged, destination-rewritten Student Home body/title. Preserve its "
                    "front-page identity and omit wiki_page[published]."
                ),
            },
            {
                "step": 6,
                "operation": "remove_obsolete_module_shells_only",
                "detail": (
                    f"Remove {len(obsolete_modules)} obsolete existing module shells and "
                    f"the {len(source_modules)} empty staging module shells. Canvas keeps "
                    "their pages, assignments, quizzes, files, and submissions in the "
                    "course; this plan deletes no underlying content object."
                ),
            },
            {
                "step": 7,
                "operation": "verify_and_stop",
                "detail": (
                    f"Require {len(source_modules)} modules, {source_item_count + 1} "
                    "placements (510 canonical plus submitted local Pre-Survey), exact "
                    "canonical order, both submitted objects unchanged, homepage ID "
                    "unchanged, no publication mutation, and no migration issues."
                ),
            },
        ],
        "explicit_non_operations": [
            "No CCE course access or write.",
            "No publish or unpublish request for any existing object.",
            "No assignment, quiz, page, discussion, file, submission, or grade deletion.",
            "No due-date, availability-date, points, rubric, submission-type, or assignment-group change.",
            "No overwrite of the two submitted assessments.",
        ],
        "approval_required": (
            "Explicitly approve this exact sealed destination plan before any content "
            "migration or destination mutation."
        ),
    }
    write_sealed(plan_path, plan)
    approval_phrase = (
        f"Approve sealed legacy rebootstrap plan {sha256_file(plan_path)} for Canvas course "
        f"{args.course_id}."
    )
    summary = [
        f"# {args.course_label} Smart Solutions rebootstrap plan",
        "",
        f"- Status: **{plan['status']}**",
        f"- Course: `{args.course_id}` — {course.get('name')}",
        f"- Approved source: `{source_hash}`",
        f"- Source package: `{package_hash}` ({package.stat().st_size:,} bytes)",
        f"- Current destination: {len(modules)} modules / {len(all_items)} placements",
        f"- Retained module containers: {len(kept_modules)}",
        f"- Obsolete existing module shells proposed for removal: {len(obsolete_modules)}",
        f"- Protected submitted assignments: {', '.join(map(str, sorted(protected_assignments)))}",
        f"- Protected submitted quiz objects: {', '.join(map(str, sorted(set(args.protected_quiz))))}",
        f"- Final target: {len(source_modules)} modules / {source_item_count + 1} placements",
        "- Publication: read back for verification only; never a guard or write field",
        "- Underlying content deletion: none",
        "",
        "## Exact approval phrase",
        "",
        f"> {approval_phrase}",
        "",
        "See `plan.json` for every retained/obsolete module ID and operation.",
    ]
    summary_path.write_text("\n".join(summary) + "\n", encoding="utf-8")
    summary_path.chmod(0o600)
    print(
        stable_json(
            {
                "status": plan["status"],
                "read_only": True,
                "plan": str(plan_path),
                "plan_sha256": sha256_file(plan_path),
                "backup": str(backup_path),
                "summary": str(summary_path),
                "approval_phrase": approval_phrase,
            }
        ),
        end="",
    )


if __name__ == "__main__":
    main()
