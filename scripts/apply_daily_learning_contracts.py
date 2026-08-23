#!/usr/bin/env python3
"""Apply the audited semantic Topic, Objective, TEKS, and DOL ledger to Canvas."""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from datetime import datetime
from pathlib import Path

from canvas_api import Canvas, env_course_id


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
LEDGER = ROOT / "data/daily-learning-contracts.json"
CANON = ROOT / "docs/standards/texas-technology-applications-grade-8-teks-2022.md"
MARKER = 'data-vils-daily-learning-contract="2026-08-21-semantic-audit-v1"'
GUIDE_RE = re.compile(r"^Facilitator(?:'s)? Guide:", re.I)
LEGACY_ALIGNMENT_MARKER = 'data-vils-teks-alignment="2026-08-19"'
FILE_VERSION_REPLACEMENTS = {3224320: 3224324}


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


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


def load_ledger() -> list[dict]:
    payload = json.loads(LEDGER.read_text(encoding="utf-8"))
    if payload["course_id"] != 23402:
        raise ValueError("Daily learning contract ledger targets the wrong course")
    if payload["canonical_teks_sha256"] != hashlib.sha256(CANON.read_bytes()).hexdigest():
        raise ValueError("Canonical TEKS source changed after the semantic audit")
    rows = payload["records"]
    if len(rows) != 156 or len({row["module_item_id"] for row in rows}) != 156:
        raise ValueError("Daily learning contract ledger must contain 156 unique guides")
    for row in rows:
        if not row["objective"].startswith("Students will "):
            raise ValueError(f"Objective is not student-facing for {row['module_item_id']}")
        if not row["topic"] or not row["demonstration_of_learning"]:
            raise ValueError(f"Incomplete semantic contract for {row['module_item_id']}")
        for code in row["teks"]:
            expectation_text(code)
    return rows


def teks_html(codes: list[str]) -> str:
    if not codes:
        return (
            '<p style="margin:0 0 8px;"><strong>TEKS:</strong> '
            "No independent Grade 8 Technology Applications TEKS claim. "
            "This lesson provides operational, preparatory, or cross-curricular evidence.</p>"
        )
    items = "".join(
        f'<li style="margin:0 0 7px;"><strong>{html.escape(code)}</strong> — '
        f'{html.escape(expectation_text(code))}</li>'
        for code in codes
    )
    return (
        '<div style="margin:0 0 8px;"><strong>TEKS:</strong>'
        f'<ul style="margin:7px 0 0;padding-left:22px;">{items}</ul></div>'
    )


def contract_block(row: dict) -> str:
    return f'''
<div {MARKER} style="background:#F4F8FC;border:2px solid #1B6F7A;border-radius:12px;padding:16px 18px;margin:16px 0;color:#20313E;">
  <h2 style="margin:0 0 10px;font-size:22px;color:#1B6F7A;">Daily Learning Contract</h2>
  <p style="margin:0 0 8px;"><strong>Topic:</strong> {html.escape(row["topic"])}</p>
  <p style="margin:0 0 8px;"><strong>Objective:</strong> {html.escape(row["objective"])}</p>
  {teks_html(row["teks"])}
  <p style="margin:0;"><strong>Demonstration of learning:</strong> {html.escape(row["demonstration_of_learning"])}</p>
</div>
'''


def enclosing_div_span(body: str, needle_position: int) -> tuple[int, int] | None:
    stack: list[int] = []
    for token in re.finditer(r"<div\b[^>]*>|</div\s*>", body, re.I):
        if token.group(0).lower().startswith("<div"):
            stack.append(token.start())
            continue
        if not stack:
            continue
        start = stack.pop()
        if start <= needle_position < token.end():
            return start, token.end()
    return None


def remove_div_containing(body: str, needle: str) -> str:
    while needle in body:
        span = enclosing_div_span(body, body.index(needle))
        if span is None:
            raise ValueError(f"Could not resolve div containing {needle}")
        body = body[: span[0]] + body[span[1] :]
    return body


def replace_contract(body: str, rendered: str) -> str:
    rendered = rendered.strip("\n")

    def splice(span: tuple[int, int]) -> str:
        before = body[: span[0]].rstrip("\n")
        after = body[span[1] :].lstrip("\n")
        return before + "\n" + rendered + "\n" + after

    marker_position = body.find("data-vils-daily-learning-contract=")
    if marker_position >= 0:
        span = enclosing_div_span(body, marker_position)
        if span is None:
            raise ValueError("Could not resolve existing marked daily contract")
        return splice(span)

    title_position = body.lower().find("daily learning contract")
    if title_position >= 0:
        span = enclosing_div_span(body, title_position)
        if span is None:
            raise ValueError("Could not resolve existing daily contract")
        return splice(span)

    if re.match(r"\s*<div\b", body, re.I):
        first_position = body.lower().find("<div")
        span = enclosing_div_span(body, first_position)
        if span is not None:
            return body[: span[1]].rstrip("\n") + "\n" + rendered + "\n" + body[span[1] :].lstrip("\n")
    return rendered + "\n" + body.lstrip("\n")


def update_canvas_file_links(body: str, file_metadata: dict[int, dict]) -> str:
    for old_id, new_id in FILE_VERSION_REPLACEMENTS.items():
        if str(old_id) not in body:
            continue
        row = file_metadata[new_id]
        new_url = html.escape(row["url"], quote=True)
        body = re.sub(
            rf'https://verizoninnovativelearning\.instructure\.com/courses/23402/files/{old_id}/download\?[^"<]+',
            new_url,
            body,
        )
        body = body.replace(f"/files/{old_id}", f"/files/{new_id}")
        body = body.replace(
            f'data-vils-google-copy="{old_id}"',
            f'data-vils-google-copy="{new_id}"',
        )
    return body


def live_guides(canvas: Canvas, course_id: int) -> list[dict]:
    rows: list[dict] = []
    for module in canvas.paged(f"/courses/{course_id}/modules?per_page=100"):
        items = canvas.paged(
            f"/courses/{course_id}/modules/{module['id']}/items?per_page=100"
        )
        for item in items:
            if item.get("type") != "Page" or not GUIDE_RE.search(item.get("title", "")):
                continue
            page = canvas.get(f"/courses/{course_id}/pages/{item['page_url']}")
            rows.append({"module": module, "item": item, "page": page})
    return rows


def plain_text(value: str) -> str:
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", value)).split())


def expected_phrases(row: dict) -> list[str]:
    return [row["topic"], row["objective"], row["demonstration_of_learning"], *row["teks"]]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    ledger_rows = load_ledger()
    by_slug = {row["page_slug"]: row for row in ledger_rows}
    canvas = Canvas()
    course_id = env_course_id(23402)
    guides = live_guides(canvas, course_id)
    live_slugs = {row["page"]["url"] for row in guides}
    if live_slugs != set(by_slug):
        raise SystemExit(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "missing_from_ledger": sorted(live_slugs - set(by_slug)),
                    "missing_from_canvas": sorted(set(by_slug) - live_slugs),
                },
                indent=2,
            )
        )

    file_metadata = {
        new_id: canvas.get(f"/files/{new_id}")
        for new_id in FILE_VERSION_REPLACEMENTS.values()
    }
    targets = []
    for guide in guides:
        slug = guide["page"]["url"]
        body = guide["page"].get("body") or ""
        current_text = plain_text(body)
        contract_is_current = (
            MARKER in body
            and body.count("Daily Learning Contract") == 1
            and LEGACY_ALIGNMENT_MARKER not in body
            and all(phrase in current_text for phrase in expected_phrases(by_slug[slug]))
            and not any(str(old_id) in body for old_id in FILE_VERSION_REPLACEMENTS)
        )
        if contract_is_current:
            continue
        updated = remove_div_containing(body, LEGACY_ALIGNMENT_MARKER)
        updated = replace_contract(updated, contract_block(by_slug[slug]))
        updated = update_canvas_file_links(updated, file_metadata)
        updated = "\n".join(line.rstrip() for line in updated.split("\n"))
        if updated != body:
            targets.append({**guide, "updated_body": updated})

    summary = {
        "course_id": course_id,
        "facilitator_guides": len(guides),
        "targets": len(targets),
        "apply": args.apply,
        "module_item_ids": [row["item"]["id"] for row in targets],
    }
    if not args.apply:
        print(json.dumps(summary, indent=2))
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = WORKSPACE / f"course_backup_pre_semantic_daily_contracts_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    (backup_dir / "before.json").write_text(
        json.dumps(guides, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (backup_dir / "plan.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )

    for target in targets:
        slug = target["page"]["url"]
        canvas.request(
            "PUT",
            f"/courses/{course_id}/pages/{slug}",
            {
                "wiki_page[body]": target["updated_body"],
                "wiki_page[published]": "true" if target["page"]["published"] else "false",
            },
        )

    verified = live_guides(canvas, course_id)
    failures: list[str] = []
    before_by_slug = {row["page"]["url"]: row for row in guides}
    for row in verified:
        slug = row["page"]["url"]
        body = row["page"].get("body") or ""
        text = plain_text(body)
        if body.count("Daily Learning Contract") != 1:
            failures.append(f"{slug}: expected exactly one daily contract")
        if LEGACY_ALIGNMENT_MARKER in body:
            failures.append(f"{slug}: legacy module alignment block remains")
        for phrase in expected_phrases(by_slug[slug]):
            if phrase not in text:
                failures.append(f"{slug}: missing audited phrase {phrase}")
        before = before_by_slug[slug]["page"]
        if row["page"]["published"] != before["published"]:
            failures.append(f"{slug}: publication state changed")
        if row["page"]["page_id"] != before["page_id"]:
            failures.append(f"{slug}: page identity changed")

    lesson5 = next(
        row for row in verified if row["page"]["url"] == "facilitator-guide-comics-lesson-5-smart-solution-in-action"
    )
    lesson5_body = lesson5["page"].get("body") or ""
    if "3224324" not in lesson5_body or "3224320" in lesson5_body:
        failures.append("Lesson 5 facilitator guide does not reference Canvas deck version 3224324")

    result = {
        **summary,
        "backup": str(backup_dir),
        "verified_guides": len(verified),
        "failures": failures,
        "ledger_sha256": hashlib.sha256(LEDGER.read_bytes()).hexdigest(),
    }
    (backup_dir / "result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
