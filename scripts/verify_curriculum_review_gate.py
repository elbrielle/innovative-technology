#!/usr/bin/env python3
"""Fail closed when instructional changes lack a four-lens GO review record."""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REVIEW_DIR = ROOT / "docs/reviews"
DECISION_LABELS = (
    "Teacher implementation",
    "District curriculum",
    "Student experience",
    "Design and language",
    "Consensus",
)
PASSING = {"GO", "GO WITH FIXES"}


def git(*args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def instructional(path: str) -> bool:
    if path.startswith(("curriculum-assets/", "lessons/", "modules/")):
        return True
    if path.startswith("docs/standards/"):
        return True
    if path in {
        "index.html",
        "about.html",
        "parity.html",
        "data/course-snapshot.json",
        "data/daily-learning-contracts.json",
        "data/public-links.json",
        "data/site-manifest.json",
    }:
        return True
    name = Path(path).name
    return path.startswith("scripts/") and (
        name.startswith("apply_")
        or (name.startswith("build_") and ("deck" in name or "asset" in name))
    )


def changed_paths(base: str) -> list[str]:
    paths = set(line for line in git("diff", "--name-only", f"{base}...HEAD").splitlines() if line)
    paths.update(line for line in git("diff", "--name-only").splitlines() if line)
    paths.update(line for line in git("ls-files", "--others", "--exclude-standard").splitlines() if line)
    return sorted(paths)


def parse_record(path: Path) -> tuple[dict[str, str], list[str]]:
    text = path.read_text(encoding="utf-8")
    decisions: dict[str, str] = {}
    failures: list[str] = []
    for label in DECISION_LABELS:
        match = re.search(rf"(?mi)^{re.escape(label)}:\s*(GO WITH FIXES|GO|HOLD)\s*$", text)
        if not match:
            failures.append(f"{path.relative_to(ROOT)} is missing '{label}: ...'")
        else:
            decisions[label] = match.group(1).upper()
    for heading in ("## Reviewed scope", "## Independent findings", "## Adversarial consensus", "## Merge gate", "## Fixes and final rereview"):
        if heading not in text:
            failures.append(f"{path.relative_to(ROOT)} is missing {heading}")
    return decisions, failures


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="HEAD^")
    args = parser.parse_args()
    paths = changed_paths(args.base)
    changed_instructional = [path for path in paths if instructional(path)]
    if not changed_instructional:
        print("CURRICULUM REVIEW GATE: not applicable")
        return 0
    changed_reviews = [ROOT / path for path in paths if path.startswith("docs/reviews/") and path.endswith(".md")]
    changed_reviews = [path for path in changed_reviews if path.name.lower() != "template.md"]
    if not changed_reviews:
        print("CURRICULUM REVIEW GATE: FAIL")
        print("Instructional files changed without a changed docs/reviews/*.md record.")
        return 1
    records = []
    failures: list[str] = []
    for path in changed_reviews:
        decisions, record_failures = parse_record(path)
        records.append((path, decisions))
        failures.extend(record_failures)
    nonpassing = [
        (path, decisions)
        for path, decisions in records
        if not decisions or any(decisions.get(label) not in PASSING for label in DECISION_LABELS)
    ]
    if failures or nonpassing:
        print("CURRICULUM REVIEW GATE: FAIL")
        for failure in failures:
            print("-", failure)
        for path, decisions in records:
            held = [label for label in DECISION_LABELS if decisions.get(label) == "HOLD"]
            if held:
                print(f"- {path.relative_to(ROOT)} remains HOLD: {', '.join(held)}")
        if not failures and not any(decisions for _, decisions in records):
            print("- No complete four-lens decision record was found.")
        return 1
    print(
        "CURRICULUM REVIEW GATE: PASS",
        ", ".join(str(path.relative_to(ROOT)) for path, _ in records),
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
