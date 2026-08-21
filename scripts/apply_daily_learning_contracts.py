#!/usr/bin/env python3
"""Audit and repair missing daily learning contracts on Canvas facilitator guides.

The lesson-specific records below are grounded in the live lesson bodies and the
approved module alignment ledger. TEKS wording is always read from the dated
canonical transcript instead of being copied into this script.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path

from canvas_api import Canvas, env_course_id


ROOT = Path(__file__).resolve().parents[1]
WORKSPACE = ROOT.parent
CANON = ROOT / "docs/standards/texas-technology-applications-grade-8-teks-2022.md"
MARKER = 'data-vils-daily-learning-contract="2026-08-21"'
GUIDE_RE = re.compile(r"^Facilitator(?:'s)? Guide:", re.I)


@dataclass(frozen=True)
class Contract:
    topic: str
    objective: str
    teks: tuple[str, ...]
    demonstration: str
    scope: str = "Practiced"


CONTRACTS: dict[str, Contract] = {
    "facilitator-guide-ready-set-design": Contract(
        "User-centered design process",
        "Students will use empathize, define, ideate, prototype, and test to build and improve a solution for a stated user need.",
        ("§126.19(c)(3)(B)",),
        "Team prototype, user-need statement, test feedback, and one documented revision.",
        "Demonstrated",
    ),
    "facilitator-guide-comics-lesson-1-welcome-and-comic-cover": Contract(
        "Visual identity and first impressions",
        "Students will design a comic cover whose title, hero image, colors, and details communicate a clear first impression.",
        ("§126.19(c)(3)(B)",),
        "Assembled booklet and comic cover with a readable title, hero name, central image, and one explained design choice.",
    ),
    "facilitator-guide-comics-lesson-2-biography-and-motivation": Contract(
        "Character motivation and design choices",
        "Students will develop a hero biography whose abilities, facts, and goals give evidence for a choice the hero would make.",
        ("§126.19(c)(3)(B)",),
        "Comic Page 1 with a readable identity, abilities, facts, goals, and one evidence-based prediction about the hero's choices.",
    ),
    "facilitator-guide-comics-lesson-3-hero-gadget-design": Contract(
        "Problem-solving gadget design",
        "Students will design and label a gadget that addresses a user problem, explain its function, and identify at least one input or output.",
        ("§126.19(c)(3)(B)",),
        "Comic Page 2 with the gadget's name, function, drawing, problem solved, and at least one labeled input or output.",
    ),
    "facilitator-guide-comics-lesson-4-hero-logo-design": Contract(
        "Logo design and visual communication",
        "Students will develop thumbnail ideas and refine one logo whose symbol and color choices communicate the hero's identity.",
        ("§126.19(c)(3)(B)",),
        "Comic Page 3 with three thumbnails, one refined emblem, purposeful color choices, and short symbol and color explanations.",
    ),
    "facilitator-guide-comics-lesson-5-smart-solution-in-action": Contract(
        "Sustainable smart solutions",
        "Students will examine a sustainability challenge and create a readable comic sequence showing their hero using a smart solution to produce a visible result.",
        ("§126.19(c)(3)(B)",),
        "Comic Page 4 showing the challenge, the hero's choice, the gadget in action, and the result, plus the complete comic submission.",
        "Demonstrated",
    ),
    "facilitator-guide-emoji-project-overview": Contract(
        "Emoji design for an audience",
        "Students will define a communication gap, develop multiple ideas, prototype an original emoji, test it at small size, and present the final design.",
        ("§126.19(c)(3)(B)", "§126.19(c)(11)(B)", "§126.19(c)(12)(H)"),
        "Original emoji proposal with ideation evidence, small-size test, revised prototype, peer feedback, and pitch.",
        "Demonstrated",
    ),
    "facilitator-guide-cad-skill-ladder": Contract(
        "CAD foundations and print constraints",
        "Students will move from a flat design to 3D models, use solids and holes, and revise a model for basic 3D-printing constraints.",
        ("§126.19(c)(3)(B)", "§126.19(c)(12)(C)"),
        "Currency design, modeled coin, and ring model that shows accurate dimensions and a revision based on print constraints.",
    ),
    "facilitator-guide-favorite-toy-shape-decomposition": Contract(
        "Shape decomposition in CAD",
        "Students will identify the basic forms inside a complex object and use those forms to build and revise a proportional model.",
        ("§126.19(c)(3)(B)", "§126.19(c)(12)(C)"),
        "Favorite-toy plan, Tinkercad model, comparison to the reference, and one documented revision.",
        "Demonstrated",
    ),
    "facilitator-guide-dream-room-capstone": Contract(
        "Scale and spatial modeling",
        "Students will plan a room from references, convert measurements to one consistent scale, build the model, test it with another person, and revise it.",
        ("§126.19(c)(3)(B)", "§126.19(c)(12)(C)"),
        "Scaled room plan, Tinkercad model, measurement evidence, peer test, revision, and final submission screenshots.",
        "Demonstrated",
    ),
    "facilitator-guide-welcome-mission": Contract(
        "Interactive guidance for a first-time visitor",
        "Students will plan, build, and test an interactive map that helps a specific first-time visitor arrive, find a destination, and get help or continue.",
        ("§126.19(c)(3)(B)", "§126.19(c)(11)(A)", "§126.19(c)(11)(B)", "§126.19(c)(12)(C)"),
        "Published Welcome Mission link with three purposeful stops, working tags, a visitor test, and one revision.",
        "Demonstrated",
    ),
    "facilitator-guide-360-guide": Contract(
        "Choosing flat and 360 media",
        "Students will choose when a 360 image improves visitor understanding, build one 360 stop, test its navigation, and revise it.",
        ("§126.19(c)(3)(B)", "§126.19(c)(11)(A)", "§126.19(c)(11)(B)", "§126.19(c)(12)(C)"),
        "Revised Welcome Mission with a functional 360 stop, purposeful tags, partner-test evidence, and a published link.",
        "Demonstrated",
    ),
    "facilitator-guide-branching-narratives": Contract(
        "Branching choices and consequences",
        "Students will plan, build, test, and revise an interactive route in which visitor choices lead to different outcomes.",
        ("§126.19(c)(3)(B)", "§126.19(c)(11)(A)", "§126.19(c)(11)(B)", "§126.19(c)(12)(C)"),
        "Story map and published branching experience with working choices, at least two outcomes, test evidence, and one revision.",
        "Demonstrated",
    ),
    "facilitator-guide-career-fair-project": Contract(
        "Career research and public communication",
        "Students will investigate one career using traceable sources, design accurate information for a visitor, and explain their findings aloud.",
        ("§126.19(c)(5)(B)", "§126.19(c)(9)(C)", "§126.19(c)(8)(B)", "§126.19(c)(8)(C)"),
        "Research organizer and source log, visitor-facing materials, booth or display, and live career explanation.",
        "Optional route, demonstrated when assigned",
    ),
    "facilitator-guide-complete-paths-+-safe-testing": Contract(
        "Complete circuits and safe troubleshooting",
        "Students will trace a complete circuit path, test conductors and insulators, and use repeatable evidence to troubleshoot a failed build.",
        ("§126.19(c)(12)(F)", "§126.19(c)(12)(A)"),
        "Working lamp circuit, contrasting material tests, circuit-path explanation, and troubleshooting record.",
        "Demonstrated",
    ),
    "facilitator-guide-series-parallel-+-reliability": Contract(
        "Series, parallel, and reliability",
        "Students will compare one-path and multi-path circuits, predict what happens after a component failure, and design for continued operation.",
        ("§126.19(c)(12)(F)", "§126.19(c)(3)(B)", "§126.19(c)(12)(A)"),
        "Series and parallel builds, failure-test comparison, and a reliability design with a supported prediction.",
        "Demonstrated",
    ),
    "facilitator-guide-leds-resistors-+-motors": Contract(
        "Controlled light and motion outputs",
        "Students will control LED and motor behavior, identify the role of a resistor, and explain a system from control or input to output.",
        ("§126.19(c)(12)(F)", "§126.19(c)(12)(A)"),
        "LED direction test, motor direction test, resistor comparison, and labeled input-to-output system diagram.",
        "Demonstrated",
    ),
    "facilitator-guide-coded-signal-system": Contract(
        "Coded electrical communication",
        "Students will plan and build a coded signal system, test it with a listener, identify the weak point, and revise the system.",
        ("§126.19(c)(12)(F)", "§126.19(c)(3)(B)", "§126.19(c)(12)(A)"),
        "Signal planner, working coded-message system, blind decode result, and one evidence-based revision.",
        "Demonstrated",
    ),
    "facilitator-guide-360-images-and-scenes": Contract(
        "360 media and virtual scene construction",
        "Students will import a 360 image, add purposeful 3D objects, and rebuild the place as a navigable 3D scene.",
        ("§126.19(c)(3)(B)", "§126.19(c)(11)(A)", "§126.19(c)(11)(B)", "§126.19(c)(12)(C)"),
        "Delightex share link containing the completed 360-photo scene and the corresponding navigable 3D scene.",
        "Demonstrated",
    ),
    "facilitator-guide-lesson-2-empathize-and-define": Contract(
        "Empathize and define a circuit-system need",
        "Students will gather information about a user and define a clear problem their Snap Circuits solution can address.",
        ("§126.19(c)(3)(B)",),
        "Completed project-specific Empathize and Define worksheet submitted in Canvas.",
    ),
    "facilitator-guide-lesson-3-ideate-and-prototype": Contract(
        "Ideate and prototype a circuit solution",
        "Students will develop possible circuit solutions, select one using stated criteria, and build a testable prototype.",
        ("§126.19(c)(3)(B)", "§126.19(c)(12)(F)"),
        "Ideation evidence and a working Snap Circuits prototype ready for testing.",
    ),
    "facilitator-guide-lesson-4-test-and-submit": Contract(
        "Test, revise, and submit a circuit solution",
        "Students will test their circuit prototype, document a problem, make one useful revision, and submit the finished project evidence.",
        ("§126.19(c)(3)(B)", "§126.19(c)(12)(F)"),
        "Completed Test and Submit worksheet, prototype evidence, documented revision, and final Canvas submission.",
        "Demonstrated",
    ),
    "facilitator-guide-lesson-2-project-2-empathize-and-define": Contract(
        "Empathize and define a micro:bit solution",
        "Students will identify a user need and define a clear problem for a micro:bit wearable or programmed solution.",
        ("§126.19(c)(3)(B)",),
        "Completed project-specific Empathize and Define worksheet submitted in Canvas.",
    ),
    "facilitator-guide-lesson-3-project-2-ideate": Contract(
        "Ideate a micro:bit solution",
        "Students will sketch a micro:bit wearable prototype, compare possible features, and plan the materials needed to build it.",
        ("§126.19(c)(3)(B)", "§126.19(c)(1)(E)"),
        "Prototype sketch, planned micro:bit behavior, and materials budget recorded in the Ideate worksheet.",
    ),
    "facilitator-guide-lesson-4-project-2-prototype": Contract(
        "Build and debug a micro:bit prototype",
        "Students will build the planned micro:bit solution, test its program, and revise the prototype when the behavior does not match the plan.",
        ("§126.19(c)(3)(B)", "§126.19(c)(1)(E)", "§126.19(c)(2)(C)"),
        "Working micro:bit prototype with program evidence and at least one documented test or revision.",
    ),
    "facilitator-guide-lesson-5-project-2-test-share-submit": Contract(
        "Test, improve, and share a micro:bit solution",
        "Students will test the micro:bit solution with another person, use the feedback to improve it, and submit the final project evidence.",
        ("§126.19(c)(3)(B)", "§126.19(c)(1)(E)", "§126.19(c)(2)(C)"),
        "Completed testing-and-feedback worksheet, revised prototype or program, and final Canvas submission.",
        "Demonstrated",
    ),
    "facilitator-guide-lesson-2-project-3-empathize-and-define": Contract(
        "Empathize and define a smart-electronics need",
        "Students will identify an end user's need and define a clear problem for a smart-electronics solution.",
        ("§126.19(c)(3)(B)",),
        "Completed project-specific Empathize and Define worksheet submitted in Canvas.",
    ),
    "facilitator-guide-lesson-3-project-3-ideate": Contract(
        "Ideate a smart-electronics solution",
        "Students will sketch a micro:bit expansion-board prototype, compare possible features, and plan the materials needed to build it.",
        ("§126.19(c)(3)(B)",),
        "Prototype sketch, planned system behavior, and materials budget recorded in the Ideate worksheet.",
    ),
    "facilitator-guide-lesson-4-project-3-prototype": Contract(
        "Build and troubleshoot a smart-electronics prototype",
        "Students will build the planned smart-electronics solution, test its input and output behavior, and revise a problem in the system.",
        ("§126.19(c)(3)(B)", "§126.19(c)(1)(E)", "§126.19(c)(2)(C)", "§126.19(c)(12)(F)"),
        "Working smart-electronics prototype with program or wiring evidence and at least one documented test or revision.",
    ),
    "facilitator-guide-lesson-5-project-3-feedback": Contract(
        "End-user feedback and revision",
        "Students will have the end user test the prototype, record specific feedback, and improve the design in response.",
        ("§126.19(c)(3)(B)", "§126.19(c)(12)(F)"),
        "Completed feedback worksheet with end-user evidence and one documented prototype improvement.",
        "Demonstrated",
    ),
    "facilitator-guide-lesson-6-project-3-pitch-and-submit": Contract(
        "Pitch and submit a smart-electronics solution",
        "Students will explain the user need, demonstrate the final solution, and submit the complete project evidence.",
        ("§126.19(c)(3)(B)",),
        "Final pitch, completed project artifacts, prototype evidence, and Canvas submission.",
        "Demonstrated",
    ),
}


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


def contract_block(record: Contract) -> str:
    teks_items = "".join(
        f'<li style="margin:0 0 7px;"><strong>{html.escape(code)}</strong> — '
        f'{html.escape(expectation_text(code))}</li>'
        for code in record.teks
    )
    return f'''
<div {MARKER} style="background:#F4F8FC;border:2px solid #1B6F7A;border-radius:12px;padding:16px 18px;margin:16px 0;color:#20313E;">
  <h2 style="margin:0 0 10px;font-size:22px;color:#1B6F7A;">Daily Learning Contract</h2>
  <p style="margin:0 0 8px;"><strong>Topic:</strong> {html.escape(record.topic)}</p>
  <p style="margin:0 0 8px;"><strong>Objective:</strong> {html.escape(record.objective)}</p>
  <div style="margin:0 0 8px;"><strong>TEKS:</strong><ul style="margin:7px 0 0;padding-left:22px;">{teks_items}</ul></div>
  <p style="margin:0 0 8px;"><strong>Demonstration of learning:</strong> {html.escape(record.demonstration)}</p>
  <p style="margin:0;"><strong>Scope:</strong> {html.escape(record.scope)}</p>
</div>
'''


def has_contract(body: str) -> bool:
    patterns = (
        r"<strong>\s*Topic\s*:",
        r"<strong>\s*(?:Student )?Objective\s*:",
        r"<strong>\s*(?:TEKS|Essential TEKS)\s*:",
        r"<strong>\s*(?:Demonstration of learning|Show Your Learning)\s*:",
    )
    return all(re.search(pattern, body, re.I) for pattern in patterns)


def insert_contract(body: str, rendered: str) -> str:
    if MARKER in body:
        return re.sub(
            rf"\n?<div {re.escape(MARKER)}.*?</div>\n?",
            rendered,
            body,
            count=1,
            flags=re.S,
        )
    # Current authored guides begin with a colored title banner. Keep the
    # contract immediately after it. Legacy bridge guides receive it first.
    if re.match(r"\s*<div\b", body, re.I):
        closing = body.find("</div>")
        if closing >= 0:
            return body[: closing + 6] + rendered + body[closing + 6 :]
    return rendered + body


def remove_stale_comics_teks(slug: str, body: str) -> str:
    if slug != "facilitator-guide-comics-lesson-3-hero-gadget-design":
        return body
    return re.sub(
        r"\s*<p[^>]*>\s*<strong>S:</strong>\s*TEKS §127\.2\(d\)\(3\)\(I\).*?</p>",
        "",
        body,
        count=1,
        flags=re.I | re.S,
    )


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


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    canvas = Canvas()
    course_id = env_course_id(23402)
    rows = live_guides(canvas, course_id)
    missing = [row for row in rows if not has_contract(row["page"].get("body") or "")]
    missing_slugs = {row["page"]["url"] for row in missing}
    live_slugs = {row["page"]["url"] for row in rows}
    unknown = sorted(missing_slugs - CONTRACTS.keys())
    orphaned_specs = sorted(CONTRACTS.keys() - live_slugs)
    if unknown or orphaned_specs:
        raise SystemExit(
            json.dumps(
                {
                    "status": "BLOCKED",
                    "unknown_missing": unknown,
                    "orphaned_specs": orphaned_specs,
                },
                indent=2,
            )
        )

    summary = {
        "course_id": course_id,
        "facilitator_guides": len(rows),
        "complete_before": len(rows) - len(missing),
        "missing_before": len(missing),
        "apply": args.apply,
        "targets": [
            {
                "module_id": row["module"]["id"],
                "module": row["module"]["name"],
                "module_item_id": row["item"]["id"],
                "page_id": row["page"]["page_id"],
                "slug": row["page"]["url"],
                "title": row["page"]["title"],
                "published": row["page"]["published"],
                "before_sha256": sha256_text(row["page"].get("body") or ""),
                "contract": asdict(CONTRACTS[row["page"]["url"]]),
            }
            for row in missing
        ],
    }

    if not args.apply:
        print(json.dumps(summary, indent=2))
        return

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = WORKSPACE / f"course_backup_pre_daily_learning_contracts_{stamp}"
    backup_dir.mkdir(parents=True, exist_ok=False)
    (backup_dir / "manifest.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    for row in missing:
        slug = row["page"]["url"]
        body = row["page"].get("body") or ""
        (backup_dir / f"{row['page']['page_id']}-{slug}.html").write_text(
            body, encoding="utf-8"
        )
        updated = insert_contract(body, contract_block(CONTRACTS[slug]))
        updated = remove_stale_comics_teks(slug, updated)
        canvas.request(
            "PUT",
            f"/courses/{course_id}/pages/{slug}",
            {"wiki_page[body]": updated},
        )

    verified = live_guides(canvas, course_id)
    still_missing = [
        {
            "module_item_id": row["item"]["id"],
            "slug": row["page"]["url"],
            "title": row["page"]["title"],
        }
        for row in verified
        if not has_contract(row["page"].get("body") or "")
    ]
    published_drift = [
        row["page"]["url"]
        for row in verified
        if row["page"]["url"] in missing_slugs
        and row["page"]["published"]
        != next(
            before["page"]["published"]
            for before in missing
            if before["page"]["url"] == row["page"]["url"]
        )
    ]
    stale_teks = [
        row["page"]["url"]
        for row in verified
        if GUIDE_RE.search(row["page"]["title"])
        and "§127.2" in (row["page"].get("body") or "")
    ]
    result = {
        **summary,
        "backup": str(backup_dir),
        "complete_after": len(verified) - len(still_missing),
        "missing_after": still_missing,
        "publication_state_drift": published_drift,
        "stale_noncanonical_teks": stale_teks,
    }
    (backup_dir / "result.json").write_text(
        json.dumps(result, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(result, indent=2))
    if still_missing or published_drift or stale_teks:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
