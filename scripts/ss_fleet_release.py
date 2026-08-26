#!/usr/bin/env python3
"""Record an approved VILS source release and audit the enabled SS fleet.

This orchestrator is read-only with respect to Canvas. ``approve-source``
exports and verifies the approved Verizon source into the repository, then
records immutable private evidence. ``audit`` validates that evidence and runs
the personal canvas-fleet-parity engine against every enabled destination.
Neither command authorizes or performs destination writes.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT = ROOT / "data" / "course-snapshot.json"
DEFAULT_PRIVATE = Path.home() / ".config" / "canvas-fleet-parity" / "vils"
DEFAULT_ADAPTER = DEFAULT_PRIVATE / "vils-smart-solutions.json"
DEFAULT_STATE = (
    DEFAULT_PRIVATE / "states" / "vils-smart-solutions-reviewed-identity.json"
)
FLEET_AUDIT = (
    Path.home()
    / ".codex"
    / "skills"
    / "canvas-fleet-parity"
    / "scripts"
    / "fleet_audit.py"
)
SOURCE_COURSE_ID = 23402


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(command: list[str], *, env: dict[str, str] | None = None) -> None:
    subprocess.run(command, cwd=ROOT, check=True, env=env)


def git(*args: str) -> str:
    return subprocess.check_output(
        ["git", *args], cwd=ROOT, text=True
    ).strip()


def write_private(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    os.chmod(path.parent, 0o700)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    os.chmod(path, 0o600)


def seal_private(path: Path) -> Path:
    sidecar = path.with_suffix(path.suffix + ".sha256")
    sidecar.write_text(file_sha(path) + "\n", encoding="utf-8")
    os.chmod(sidecar, 0o600)
    return sidecar


def enabled_courses(adapter: dict) -> list[dict]:
    return [row for row in adapter.get("courses") or [] if row.get("enabled")]


def validate_fleet_adapter(adapter_path: Path) -> dict:
    adapter = json.loads(adapter_path.read_text(encoding="utf-8"))
    courses = enabled_courses(adapter)
    if not courses:
        raise RuntimeError("The VILS adapter has no enabled Smart Solutions destinations")
    ids = [int(row["course_id"]) for row in courses]
    if len(ids) != len(set(ids)):
        raise RuntimeError("The private adapter contains a duplicate course ID")
    source_path = Path(adapter["source"]["path"]).expanduser().resolve()
    if source_path != SNAPSHOT.resolve():
        raise RuntimeError("The private adapter does not point to this VILS snapshot")
    return adapter


def snapshot_evidence() -> dict:
    snapshot = json.loads(SNAPSHOT.read_text(encoding="utf-8"))
    source = snapshot.get("source") or {}
    if int(source.get("course_id") or -1) != SOURCE_COURSE_ID:
        raise RuntimeError("Snapshot is not sourced from Verizon Canvas course 23402")
    return {
        "path": str(SNAPSHOT.resolve()),
        "file_sha256": file_sha(SNAPSHOT),
        "semantic_sha256": snapshot["semantic_sha256"],
        "generated_at": snapshot["generated_at"],
        "source": source,
        "module_count": len(snapshot["modules"]),
        "item_count": sum(len(module["items"]) for module in snapshot["modules"]),
    }


def latest_release(private_root: Path) -> Path:
    candidates = sorted((private_root / "releases").glob("*-approved.json"))
    if not candidates:
        raise RuntimeError("No approved VILS source-release manifest exists")
    return candidates[-1]


def validate_release(release_path: Path) -> dict:
    sidecar = release_path.with_suffix(release_path.suffix + ".sha256")
    if not sidecar.is_file() or sidecar.read_text(encoding="utf-8").strip() != file_sha(
        release_path
    ):
        raise RuntimeError("Approved source-release manifest seal does not match")
    release = json.loads(release_path.read_text(encoding="utf-8"))
    if release.get("status") != "source_approved_by_user":
        raise RuntimeError("Release manifest is not user-approved")
    if release.get("snapshot") != snapshot_evidence():
        raise RuntimeError(
            "The VILS snapshot changed after source approval; obtain a new approval"
        )
    return release


def approve_source(args: argparse.Namespace) -> None:
    note = args.approval_note.strip()
    if not note:
        raise RuntimeError("An exact user approval note is required")
    token_path = args.source_token_file.expanduser()
    if not token_path.is_file():
        raise RuntimeError(
            f"Verizon source token file is missing: {token_path}. "
            "Keep it separate from the Irving destination token."
        )
    if stat.S_IMODE(token_path.stat().st_mode) & 0o077:
        raise RuntimeError(
            f"Verizon source token permissions must be 600: {token_path}"
        )
    adapter_path = args.adapter.expanduser().resolve()
    adapter = validate_fleet_adapter(adapter_path)
    destinations = [
        {"course_id": int(row["course_id"]), "label": row.get("label")}
        for row in enabled_courses(adapter)
    ]
    run(
        [
            sys.executable,
            str(ROOT / "scripts" / "sync_course.py"),
            "--source-token-file",
            str(token_path),
        ]
    )
    run([sys.executable, str(ROOT / "scripts" / "verify_curriculum_review_gate.py")])
    run(
        [
            sys.executable,
            str(FLEET_AUDIT),
            "--adapter",
            str(adapter_path),
            "--validate-only",
        ]
    )
    evidence = snapshot_evidence()
    now = datetime.now(timezone.utc)
    release = {
        "schema_version": 1,
        "status": "source_approved_by_user",
        "approved_at": now.isoformat(),
        "approval_note": note,
        "source_course_id": SOURCE_COURSE_ID,
        "snapshot": evidence,
        "git": {
            "head": git("rev-parse", "HEAD"),
            "branch": git("branch", "--show-current"),
            "changed_paths": [
                row
                for row in git("status", "--porcelain=v1").splitlines()
                if row
            ],
        },
        "adapter_path": str(adapter_path),
        "destinations_at_approval": destinations,
        "destination_count_at_approval": len(destinations),
        "boundary": (
            "Source approval authorizes read-only fleet audit and planning only; "
            "destination writes require a separate reviewed plan and explicit approval."
        ),
    }
    stamp = now.strftime("%Y%m%dT%H%M%SZ")
    output = (
        args.private_root.expanduser()
        / "releases"
        / f"{stamp}-{evidence['semantic_sha256'][:12]}-approved.json"
    )
    write_private(output, release)
    seal = seal_private(output)
    print(
        json.dumps(
            {
                "status": "PASS",
                "release_manifest": str(output),
                "release_manifest_sha256": str(seal),
                "source_semantic_sha256": evidence["semantic_sha256"],
                "destination_count": len(destinations),
                "next": "Run the audit subcommand; no destination writes are authorized.",
            },
            indent=2,
        )
    )


def audit(args: argparse.Namespace) -> None:
    private_root = args.private_root.expanduser()
    release_path = (
        args.release.expanduser().resolve()
        if args.release
        else latest_release(private_root)
    )
    release = validate_release(release_path)
    adapter_path = args.adapter.expanduser().resolve()
    adapter = validate_fleet_adapter(adapter_path)
    if str(adapter_path) != release["adapter_path"]:
        raise RuntimeError("Approved release and requested adapter do not match")
    state_path = args.state.expanduser().resolve()
    enabled_ids = {int(row["course_id"]) for row in enabled_courses(adapter)}
    selected_ids = set(args.course or enabled_ids)
    if not selected_ids or not selected_ids.issubset(enabled_ids):
        raise RuntimeError("Requested audit course is not enabled in the private adapter")
    command = [
        sys.executable,
        str(FLEET_AUDIT),
        "--adapter",
        str(adapter_path),
        "--content-depth",
        "semantic",
    ]
    if state_path.is_file():
        command.extend(["--state", str(state_path)])
    for course_id in sorted(selected_ids):
        command.extend(["--course", str(course_id)])
    now = datetime.now(timezone.utc)
    output = (
        private_root
        / "reports"
        / (
            f"{now.strftime('%Y-%m-%dT%H%M%SZ')}-ss-fleet-"
            f"{release['snapshot']['semantic_sha256'][:12]}"
        )
    )
    command.extend(["--output", str(output)])
    run(command)
    report = json.loads((output / "audit.json").read_text(encoding="utf-8"))
    courses = report.get("courses") or []
    expected_count = len(selected_ids)
    if len(courses) != expected_count:
        raise RuntimeError(
            f"Audit returned {len(courses)} of {expected_count} enabled destinations"
        )
    if {int(row["course_id"]) for row in courses} != selected_ids:
        raise RuntimeError("Audit course IDs do not match the requested enabled scope")
    print(
        json.dumps(
            {
                "status": "PASS",
                "read_only": True,
                "release_manifest": str(release_path),
                "report_directory": str(output),
                "courses": [
                    {
                        "course_id": row["course_id"],
                        "course_label": row["course_label"],
                        "module_count": row["module_count"],
                        "item_count": row["item_count"],
                        "counts": row["counts"],
                    }
                    for row in courses
                ],
                "next": (
                    "Review each course's holds/preserves and create immutable "
                    "course-specific plans. Do not apply without new user approval."
                ),
            },
            indent=2,
            ensure_ascii=False,
        )
    )


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser()
    root.add_argument("--private-root", type=Path, default=DEFAULT_PRIVATE)
    root.add_argument("--adapter", type=Path, default=DEFAULT_ADAPTER)
    subcommands = root.add_subparsers(dest="command", required=True)
    approve = subcommands.add_parser("approve-source")
    approve.add_argument("--approval-note", required=True)
    approve.add_argument(
        "--source-token-file",
        type=Path,
        default=Path.home() / ".canvas_vils_source_token",
    )
    approve.set_defaults(func=approve_source)
    check = subcommands.add_parser("audit")
    check.add_argument("--release", type=Path)
    check.add_argument("--state", type=Path, default=DEFAULT_STATE)
    check.add_argument("--course", type=int, action="append")
    check.set_defaults(func=audit)
    return root


def main() -> None:
    args = parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
