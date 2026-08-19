#!/usr/bin/env python3
"""Write the approved module-level TEKS alignment blocks to Canvas guides."""

from __future__ import annotations

import argparse
import html
import re
from pathlib import Path

from canvas_api import Canvas, env_course_id


ROOT = Path(__file__).resolve().parents[1]
AUDIT = ROOT / "docs/standards/vils-grade-8-teks-module-audit-2026-08-19.md"
CANON = ROOT / "docs/standards/texas-technology-applications-grade-8-teks-2022.md"
MARKER = 'data-vils-teks-alignment="2026-08-19"'
GUIDE_WORDS = ("facilitator", "teacher guide", "teacher reference")


def parse_audit() -> dict[int, dict[str, str]]:
    records: dict[int, dict[str, str]] = {}
    for line in AUDIT.read_text(encoding="utf-8").splitlines():
        if not re.match(r"^\| \d+ \|", line):
            continue
        cells = [part.strip() for part in line.split("|")[1:-1]]
        number = int(cells[0])
        if "; evidence: " in cells[3]:
            objective, evidence = cells[3].split("; evidence: ", 1)
        else:
            objective, evidence = cells[3], "No active demonstration of learning."
        records[number] = {
            "module": cells[1],
            "topic": cells[2],
            "objective": objective,
            "evidence": evidence,
            "essential": cells[4],
            "supporting": cells[5],
            "status": cells[6],
        }
    return records


def expectation_text(code: str) -> str:
    source = CANON.read_text(encoding="utf-8")
    lettered = re.search(rf"\*\*{re.escape(code)}:\*\* (.+)", source)
    if lettered:
        return lettered.group(1)
    whole = re.search(
        rf"### {re.escape(code)}\.[^\n]+\n\n(.+?)(?=\n\n### |\Z)", source, re.S
    )
    if whole:
        return " ".join(whole.group(1).split())
    raise ValueError(f"No canonical wording found for {code}")


def codes(cell: str) -> list[str]:
    return re.findall(r"§126\.19\(c\)(?:\(\d+\))?(?:\([A-Z]\))?", cell)


def standards_list(cell: str) -> str:
    selected = codes(cell)
    if not selected:
        return "<p style=\"margin:0;\">None claimed for this module-level record.</p>"
    items = "".join(
        f"<li style=\"margin:0 0 8px;\"><strong>{html.escape(code)}</strong> — {html.escape(expectation_text(code))}</li>"
        for code in selected
    )
    return f"<ul style=\"margin:7px 0 0;padding-left:22px;\">{items}</ul>"


def block(record: dict[str, str]) -> str:
    optional = "<p style=\"margin:10px 0 0;\"><strong>Scope note:</strong> This is an optional route. Use this alignment only when the module is assigned.</p>" if "Optional" in record["status"] else ""
    return f'''\n<div {MARKER} style="background:#F4F8FC;border:2px solid #274C77;border-radius:12px;padding:16px 18px;margin:16px 0;color:#10223B;">\n  <h2 style="margin:0 0 10px;font-size:22px;color:#10223B;">Instructional Alignment</h2>\n  <p style="margin:0 0 8px;"><strong>Topic:</strong> {html.escape(record["topic"])}</p>\n  <p style="margin:0 0 8px;"><strong>Student objective:</strong> Students will {html.escape(record["objective"])}</p>\n  <div style="margin:0 0 8px;"><strong>Essential TEKS:</strong>{standards_list(record["essential"])}</div>\n  <div style="margin:0 0 8px;"><strong>Supporting TEKS:</strong>{standards_list(record["supporting"])}</div>\n  <p style="margin:0 0 8px;"><strong>Demonstration of learning:</strong> {html.escape(record["evidence"])}</p>\n  <p style="margin:0;"><strong>Alignment status:</strong> {html.escape(record["status"])}</p>{optional}\n</div>\n'''


def insert_alignment(body: str, rendered: str) -> str:
    if MARKER in body:
        return re.sub(
            rf"\n?<div {MARKER}.*?</div>\n?",
            rendered,
            body,
            count=1,
            flags=re.S,
        )
    closing = body.find("</div>")
    if closing >= 0:
        return body[: closing + 6] + rendered + body[closing + 6 :]
    return rendered + body


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write changes to Canvas.")
    args = parser.parse_args()

    audit = parse_audit()
    canvas = Canvas()
    course_id = env_course_id()
    modules = canvas.paged(f"/courses/{course_id}/modules?per_page=100")
    targets: list[tuple[int, dict, dict[str, str]]] = []
    for module in modules:
        record = audit[module["position"]]
        if record["status"] == "N/A":
            continue
        items = canvas.paged(f"/courses/{course_id}/modules/{module['id']}/items?per_page=100")
        guide = next((i for i in items if any(word in i["title"].lower() for word in GUIDE_WORDS)), None)
        if guide is None:
            print(f"SKIP {module['position']:02d} {module['name']}: no facilitator guide")
            continue
        page = canvas.get(f"/courses/{course_id}/pages/{guide['page_url']}")
        updated = insert_alignment(page["body"], block(record))
        targets.append((module["position"], guide, {"body": updated, "title": guide["title"]}))

    for position, guide, payload in targets:
        action = "APPLY" if args.apply else "DRY-RUN"
        print(f"{action} {position:02d} {guide['id']} {payload['title']}")
        if args.apply:
            canvas.request(
                "PUT",
                f"/courses/{course_id}/pages/{guide['page_url']}",
                {"wiki_page[body]": payload["body"]},
            )
    print(f"targets: {len(targets)}")


if __name__ == "__main__":
    main()
