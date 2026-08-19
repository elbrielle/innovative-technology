#!/usr/bin/env python3
"""Create the approved missing lesson-level VILS facilitator guides in Canvas.

Canvas remains the curriculum source.  This script intentionally does not run
the static-site sync.  Run without --apply to inspect the proposed writes,
then use --apply after the live course and token have been confirmed.
"""

from __future__ import annotations

import argparse
import html
import re
from dataclasses import dataclass

from canvas_api import Canvas, env_course_id


HOST = "https://verizoninnovativelearning.instructure.com"
MARKER = "data-vils-lesson-guide=\"2026-08-19\""


@dataclass(frozen=True)
class GuideSpec:
    module_id: int
    target_item_id: int
    short_title: str
    topic: str
    objective: str
    evidence: str
    resources: str


# module id, immutable student module-item id, teacher-guide suffix, topic,
# objective, existing student evidence, existing resources.  These are the
# approved records from the 2026-08-19 lesson-guide audit; no student task,
# rubric, or TEKS claim is invented here.
ROWS = """\
72563\t2633983\tWeek 0 — Canvas Launch\tCourse navigation\tStudents will locate the named module and use the submission checklist.\tStudents follow Modules, use the orientation video, and identify the exact page or error to show their teacher.\tStudent's Guide: Getting Started; English and Spanish Canvas orientation videos; course Modules menu
72563\t2633985\tWeek 0 — Syllabus, Lab Contract + Routines\tClassroom launch\tStudents will distinguish course information they keep from materials that require a return.\tCompletion of the applicable syllabus/lab-contract routine and stated signature return materials.\tWelcome Week page; teacher-local syllabus; VILS Lab Usage Agreement; Verizon media release; local CREATE expectations
72563\t2633987\tWeek 0 Option — About Me Smartphone\tCommunity-building digital identity\tStudents will share chosen facts in a bounded, privacy-safe format.\tCompleted About Me Smartphone artifact or page response.\tExisting option page; approved teacher template/materials; optional About Me + What Is VILS Canva template
72563\t2633988\tWeek 0 Option — Moon Landing Teamwork Challenge\tCollaborative decision-making\tStudents will justify a team choice with evidence and listen for a reason to revise it.\tCompleted team ranking/chart and challenge discussion.\tMoon Landing option; Moon Landing Team Decision teacher deck; ranking-chart teacher key
72563\t2633989\tWeek 0 Option — Partner Draw\tPrecise communication\tStudents will give and follow usable verbal instructions.\tCompleted partner drawing and communication reflection/conversation.\tPartner Draw option page; paper and pencils; current visual example
72563\t2633990\tWeek 0 Option — Chromebook Norms + GimKit\tDevice routines\tStudents will apply the classroom's local acceptable-use and help routines.\tGimKit participation/completion and demonstrated device routine.\tChromebook Rules GimKit option; teacher's local device expectations; current GimKit set
72563\t2633991\tWeek 0 — Xello Account + Dashboard Check-in\tAccount readiness\tStudents will access Xello through ClassLink and establish their initial profile setting.\tReadable dashboard screenshot and the current after-high-school-goal reflection sentence.\tCurrent bilingual Xello assignment; ClassLink/Xello; screenshot directions
72565\t2634013\tPiskel Lesson 1 — Promise + Micro Plot\tAnimated storytelling\tStudents will choose one visible promise/action and plan its beginning, change, and end.\tPromise-in-action statement and completed five-part plot diagram.\tAnimation Unit guide; finished comic; Plot Diagram copy; hero materials
72565\t2634015\tPiskel Lesson 2 — Storyboard the Motion\tStoryboarding\tStudents will plan readable key poses before opening the animation tool.\tSix-panel storyboard or approved four-panel support storyboard.\tAnimation Unit guide; storyboard assignment/template; current comic/animation examples
72565\t2634016\tPiskel Lesson 3 — Tools, Frames + Practice Loop\tAnimation tool fluency\tStudents will duplicate frames, adjust timing, and save editable work.\tCompleted 1–2 second practice loop/tutorial evidence.\tPiskel for Kids; current tutorial route; district-approved .piskel storage location
72565\t2634017\tPiskel Lesson 4 — Peer Test + Useful Feedback\tAudience testing\tStudents will give a peer one observable clarity or timing note.\tPosted practice animation and peer response on the Practice Wall.\tPractice Wall discussion; current practice loops; feedback stem in Animation Unit guide
72565\t2634357\tPiskel Lesson 5 — Animate, Hold + Revise\tAnimation production\tStudents will build a coherent animation using intentional frames, holds, and revision.\tFirst pass/work-in-progress animation and documented revision choice.\tAnimation Unit production targets; Piskel; storyboard; peer-feedback notes
72565\t2634018\tPiskel Lesson 6 — Export, Verify + Reflect\tFile publishing\tStudents will export a working GIF and preserve the editable source.\tFinal animated GIF, saved source file, short reflection, and current submission evidence.\tExport and Submit assignment; Piskel export controls; current rubric; district storage route
72566\t2634021\tGraphic Design Lesson 1 — Pop Art Signals\tVisual style and audience\tStudents will use Pop Art choices to make a readable paper name tag.\tPop-Art name-tag photo and sentence-starter reflection.\tGraphic Design unit guide; Pop Art images/deck; paper and markers
72566\t2634022\tGraphic Design Lesson 2 — Lines, Circles + Canva\tConstrained digital composition\tStudents will create one lines-only and one circles-only graphic.\tTwo PNG graphics in the Google/Word worksheet, reflection, and shared link or file.\tCanva via ClassLink; Lesson 2 Google-copy/Word worksheet fallback; unit deck
72566\t2634023\tGraphic Design Lesson 3 — Read Visual Design\tVisual-analysis vocabulary\tStudents will connect video examples to design decisions.\tCurrent video or EdPuzzle completion response.\tEmbedded Canvas video; optional reusable EdPuzzle copy/Live Mode; unit-guide setup instructions
72566\t2634024\tGraphic Design Lesson 4 — Paths, Shapes + Color\tVector-shape construction\tStudents will make and explain deliberate visual choices.\tCompleted Paths, Shapes, and Colors artifact/submission.\tCanva; current assignment; unit guide; teacher deck/examples
72566\t2634025\tGraphic Design Lesson 5 — Pictographs\tSymbolic communication\tStudents will reduce an idea to a recognizable shape-based image.\tCompleted pictograph artifact/submission.\tCanva; pictograph teacher deck; current assignment and exemplars
72566\t2634026\tGraphic Design Lesson 6 — Advanced Form + Color\tRefinement\tStudents will use advanced shape and color choices while keeping a graphic readable.\tCompleted Advanced Shapes and Colors artifact/submission.\tCanva; unit deck; current assignment; relevant examples
72566\t2634030\tEmoji Lesson 1 — Define the Gap\tNeed finding\tStudents will identify an idea existing emoji do not communicate well.\tCurrent Emoji Define proposal or identified communication gap.\tEmoji Hub; Emoji Project guide; History of Emoji deck; Define form/Word fallback
72566\t2634031\tEmoji Lesson 2 — Ideate Widely\tDivergent ideation\tStudents will generate multiple distinct visual approaches before choosing one.\tRequired rough sketches/options and selected concept.\tEmoji Hub; Emoji deck slides 1–13; sketch materials; current criteria
72566\t2634032\tEmoji Lesson 3 — Prototype + Small-Size Test\tDigital prototyping\tStudents will build and revise a shapes-only emoji that works at small scale.\tEmoji prototype, small-size test, revision/export evidence in the current assignment.\tEmoji Hub; Canva; Emoji deck slides 14–28; authentic model
72566\t2634033\tEmoji Lesson 4 — Gallery Walk + Pitch\tAudience feedback\tStudents will present an emoji, review peers, and explain design choices.\tGallery-review sheets, student pitch/presentation, peer feedback, and showcase submission.\tEmoji Hub; Emoji deck slides 29–37; printed peer-review sheets; current rubric
72567\t2634036\tLaser Lesson 1 — Pixels, Paths + Machine Operations\tFabrication literacy\tStudents will predict cut, score, and engrave from a design file.\tCompleted First Look worksheet or inspection response.\tLaser Cutting deck slides 1–11; First Look editable/printable worksheet; cut-score-engrave sample SVG/tile
72567\t2634037\tLaser Lessons 2–5 — Define, File Check, Test + Queue\tConstraint-driven fabrication\tStudents will design and revise a privacy-safe laser-ready tag for a real use.\tTeacher-checked file, cut result, revision, reflection, and final identity tag.\tLaser deck slides 12–end; Canva/SVG; real-size test; class queue; teacher-approved machine/materials; current rubric
72567\t2634038\tLaser Career Connection — Skills, Tools + Roles\tCareer transfer\tStudents will connect a fabrication skill or tool to a career context.\tCurrent Xello check-in completion/screenshot and reflection.\tXello via ClassLink; current assignment; laser vocabulary and tag process
72568\t2634040\tOrnament Lesson 1 — Predict the Operations\tApplied fabrication reading\tStudents will predict cut, score, and engrave in an ornament design.\tCurrent Learn activity response or prediction.\tCore laser deck slides 4–10; current student activity; teacher model
72568\t2634041\tOrnament Lessons 2–3 — Design, File Check + Fabricate\tSeasonal production\tStudents will build a teacher-checked ornament file using established queue and safety routines.\tSVG, model/revision, finished-object photo, and reflection.\tCanva; SVG/Glowforge; existing model; core deck slides 15–23; approved wood/string; class queue
72569\t2634044\t3D Modeling Lesson 1 — Currency to 3D Thinking\t2D versus 3D communication\tStudents will design a readable currency concept and identify what would need depth to become 3D.\tCurrent currency design artifact/submission.\tCAD Skill Ladder; 3D Modeling Foundations deck slides 3–8; paper/markers
72569\t2634045\t3D Modeling Lesson 2 — Coin, Solids + Holes\tCAD basics\tStudents will use Tinkercad solids, holes, and alignment to model a coin.\tCurrent 3D coin/Tinkercad artifact and required submission evidence.\tCAD Skill Ladder; Foundations deck slides 9–19; teacher-created Tinkercad Classroom/Activity; coin example
72569\t2634046\t3D Modeling Lesson 3 — Ring + Print Constraints\tPrint-aware design\tStudents will model a ring and diagnose what may fail in physical printing.\tCurrent ring model/PNG and print-readiness reflection.\tCAD Skill Ladder; Foundations deck slides 20–28; Tinkercad class; ring-diameter example; optional failed-print example
72569\t2634052\t3D Modeling — Xello Skills Check-in\tTransferable skill naming\tStudents will add or reflect on a skill developed through CAD.\tCurrent Xello completion/screenshot and skills reflection.\tXello via ClassLink; current assignment; CAD vocabulary; Portfolio Example
72571\t2634067\tFlex Option — Email Etiquette\tFormal digital communication\tStudents will repair weak messages and draft one useful school email.\tFour repaired emails and one useful email connected to an actual school need.\tCareer + Communication Flex Menu; Lucero email-etiquette deck slides 1–28; district practice document
72571\t2634070\tFlex Option — Vision Board\tPrivate future-facing communication\tStudents will connect current identity to one direction they may explore.\tCurrent Vision Board artifact/submission.\tFlex Menu; current assignment; teacher-approved creation tool/materials; stated privacy boundary
72571\t2634079\tCareer Fair Setup — Build a Career Starting Pool\tResearch launch\tStudents will save possible careers before committing to one for research.\tCurrent Xello starting-pool completion/saved careers.\tXello via ClassLink; Career Fair guide; current assignment
72571\t2634074\tCareer Fair Step 1 — Choose + Commit\tResearch framing\tStudents will choose one career with a stated reason to investigate it.\tThree-career shortlist and one career commitment.\tCareer Fair project guide; project walkthrough deck; Xello pool; current Step 1 assignment
72571\t2634075\tCareer Fair Step 2 — Research + Source Log\tSearch and citation\tStudents will gather current evidence and label facts with sources and year.\tResearch organizer and source log; published facts have sources.\tCareer Fair guide; full research deck; research organizer PDF/editable DOCX; source examples
72571\t2634076\tCareer Fair Step 3 — Explain for a Visitor\tInformation design\tStudents will turn research into a public page another viewer can open.\tOne public informational website/page and working share link.\tCareer Fair guide; project walkthrough deck; website examples; current assignment/rubric
72571\t2634077\tCareer Fair Step 4 — Invite + Make It Findable\tPromotional communication\tStudents will create a matching poster and handout.\tPoster and matching handout with readable headline/visual system.\tCareer Fair guide; promotional-material examples deck; current assignment/rubric
72571\t2634078\tCareer Fair Step 5 — Booth, Pitch + Questions\tPublic explanation\tStudents will use evidence to pitch and respond honestly to visitor questions.\tBooth, short pitch, visitor round/questions, and presentation evidence.\tCareer Fair guide; project walkthrough deck; booth materials; completed website/poster/handout; rubric
72573\t2634105\tCode + Web Day 1 — Algorithm + First Program\tSequencing\tStudents will create, run, and revise a block-code algorithm.\tCode.org progress screenshot and reflection.\tCode.org Express Lesson 1 / Programming with Angry Birds; existing 49-slide deck; current bilingual assignment
72573\t2634106\tCode + Web Day 2 — Choice Coding + Patterns\tCoding patterns\tStudents will choose an appropriately challenging coding activity and identify sequence, loop, or event.\tCertificate, completion screenshot, or finished project plus reflection.\tHour of Code activity list; existing deck; current assignment
72573\t2634107\tCode + Web Day 3 — Predict, Debug + Log\tDebugging\tStudents will test one change at a time and explain the result.\tProgress screenshot, three-bug log, and reflection.\tCode.org Express Lesson 2 / Debugging in Maze; existing deck; current assignment
72573\t2634108\tCode + Web Day 4 — Input, Storage, Processing + Output\tSystem models\tStudents will map a real device action through input, storage, processing, and output.\tDevice map and reflection.\tCS Discoveries Unit 1 Lessons 4 and 6; current assignment; existing deck
72573\t2634109\tCode + Web Day 5 — Web Pages + First HTML\tHTML structure\tStudents will connect HTML tags to the rendered page.\tReadable screenshot showing first HTML code and preview, plus reflection.\tCS Discoveries Unit 2 Lessons 1–2 / Web Lab; existing deck; current assignment
72573\t2634111\tCode + Web Day 6 — Headings, Lists + Nesting\tSemantic organization\tStudents will make a page outline visible in HTML.\tStructured-page screenshot, outline, and reflection.\tCS Discoveries Unit 2 Lesson 3; Web Lab; current assignment; existing deck
72573\t2634112\tCode + Web Day 7 — Build + Publish an HTML Page\tAudience-centered publishing\tStudents will plan, code, and test a one-page site.\tPublished link, screenshot, and reflection.\tCS Discoveries Unit 2 Lesson 5; Web Lab; current assignment; peer ten-second test
72573\t2634113\tCode + Web Day 8 — CSS Rules + Readability\tCSS concepts\tStudents will change styling without breaking document structure.\tBefore-and-after screenshot and reflection.\tCS Discoveries Unit 2 Lessons 6 and 9; Day 7 project; Web Lab; current assignment
72573\t2634114\tCode + Web Day 9 — Style, Test + Republish\tVisual hierarchy\tStudents will add purposeful CSS and revise from reader feedback.\tStyled-page screenshot, published link, and reflection.\tCS Discoveries Unit 2 Lesson 10; Web Lab; current assignment; peer ten-second test
72573\t2634115\tCode + Web Day 10 — Walkthrough, Feedback + Pathway\tTechnical communication\tStudents will explain code choices and use specific feedback.\tPublished link, 90-second walkthrough, peer feedback, and reflection.\tWeb Lab links; existing deck slides 41–49; CS Discoveries topic list; current assignment
72573\t2634116\tCode + Web — Xello Skills Connection\tCareer transfer\tStudents will connect a coding skill to work in another setting.\tXello Skills completion screenshot and reflection connecting one Xello skill to a coding-unit skill.\tXello via ClassLink; current assignment; current coding evidence
72574\t2634118\tVideo Game Design Lesson 1 — Skillmap, Sign-in + Save\tMakeCode onboarding\tStudents will complete two tutorials and preserve a recoverable project.\tScreenshot of two completed Skillmap pieces, reflection, and saved/downloaded project PNG.\tVideo Game Design guide; MakeCode Arcade Skillmap; school Microsoft sign-in; teacher deck slides 1–12
72574\t2634119\tVideo Game Design Lesson 2 — Remix, Test + Explain\tProgram revision\tStudents will modify a working game with purposeful features and test player experience.\tRemixed game with two or more purposeful features, submission evidence, and reflection.\tExisting project/PNG fallback; official Greeting Card fallback; MakeCode Arcade; teacher deck slides 13–21; rubric
"""


def specs() -> list[GuideSpec]:
    rows: list[GuideSpec] = []
    for line in ROWS.strip().splitlines():
        cells = line.split("\t")
        if len(cells) != 7:
            raise ValueError(f"Expected seven tab-separated cells, got {len(cells)}: {line!r}")
        rows.append(GuideSpec(int(cells[0]), int(cells[1]), *cells[2:]))
    return rows


OVERVIEW_SLUG = {
    72563: "facilitators-guide-getting-started",
    72565: "animation-unit-|-facilitator-guide",
    72566: "facilitators-guide-graphic-design-with-the-1960s",
    72567: "facilitators-guide-cnc-lasercutting",
    72568: "facilitators-guide-holiday-ornaments",
    72569: "facilitators-guide-3d-modeling-overview",
    72571: "teacher-guide-star-career-+-communication-flex-menu",
    72573: "facilitators-guide-code-and-web",
    72574: "facilitators-guide-video-game-design",
}


def lesson_flow(spec: GuideSpec) -> list[tuple[str, str]]:
    return [
        ("1. Launch", f"Put the purpose in front of students: {spec.objective}"),
        ("2. Model", f"Use one current example, tool, or teacher resource before students begin {spec.topic.lower()}."),
        ("3. Guide", "Complete the first decision or step together; conference before students commit to a direction."),
        ("4. Build", f"Students complete the existing Canvas task. Do not add a second product or change the current rubric."),
        ("5. Check + next step", f"Verify this evidence before students leave: {spec.evidence}"),
    ]


def alignment_block(body: str) -> str:
    """Return the existing exact module alignment div, including its TEKS text."""
    marker = re.search(r"<div\b[^>]*data-vils-teks-alignment=[^>]*>", body, re.I)
    if not marker:
        raise RuntimeError("Module overview does not contain the expected TEKS alignment block")
    start = marker.start()
    depth = 0
    token_re = re.compile(r"</?div\b[^>]*>", re.I)
    for token in token_re.finditer(body, marker.start()):
        if token.group(0).lower().startswith("</"):
            depth -= 1
            if depth == 0:
                return body[start:token.end()]
        else:
            depth += 1
    raise RuntimeError("Unclosed TEKS alignment div")


def page_body(spec: GuideSpec, target: dict, alignment: str) -> str:
    title = html.escape(spec.short_title)
    student_title = html.escape(target["title"])
    target_url = f"{HOST}/courses/{env_course_id()}/modules/items/{spec.target_item_id}"
    resources = "".join(f"<li>{html.escape(item.strip())}</li>" for item in spec.resources.split(";"))
    flow = "".join(
        f"<li><strong>{html.escape(label)}:</strong> {html.escape(detail)}</li>"
        for label, detail in lesson_flow(spec)
    )
    return f'''<div {MARKER} data-vils-target-module-item="{spec.target_item_id}" style="max-width:900px;margin:0 auto;font-size:16px;line-height:1.55;color:#1F2430;">
<div style="background:#0E7C7B;border-radius:10px;padding:18px 20px;margin:0 0 16px 0;">
  <p style="margin:0 0 5px;color:#FFFFFF;font-size:14px;letter-spacing:.04em;"><strong>TEACHER ONLY · LESSON GUIDE</strong></p>
  <h1 style="color:#FFFFFF;margin:0 0 6px;font-size:26px;">{title}</h1>
  <p style="color:#FFFFFF;margin:0;">Run the current student lesson with its existing evidence, resources, and submission route.</p>
</div>
<div style="background:#F4F8FC;border:2px solid #274C77;border-radius:12px;padding:16px 18px;margin:0 0 16px;color:#10223B;">
  <h2 style="margin:0 0 10px;font-size:22px;color:#10223B;">Daily Learning Contract</h2>
  <p style="margin:0 0 8px;"><strong>Topic:</strong> {html.escape(spec.topic)}</p>
  <p style="margin:0 0 8px;"><strong>Student objective:</strong> {html.escape(spec.objective)}</p>
  <p style="margin:0;"><strong>Demonstration of learning:</strong> {html.escape(spec.evidence)}</p>
</div>
<div style="margin:0 0 16px;">{alignment}</div>
<div style="background:#FFF3D6;border-radius:10px;padding:14px 16px;margin:0 0 16px;">
  <h2 style="margin:0 0 6px;font-size:19px;color:#0E7C7B;">Use what is already in Canvas</h2>
  <p style="margin:0 0 8px;">Student-facing task: <a style="color:#0E7C7B;" href="{target_url}"><strong>{student_title}</strong></a>. Keep the current student page, requirements, points, and rubric as the source of truth.</p>
  <ul style="margin:0;padding-left:24px;">{resources}</ul>
</div>
<h2 style="margin:22px 0 8px;font-size:20px;color:#0E7C7B;">Before students begin</h2>
<ul style="margin:0 0 16px;padding-left:24px;"><li>Open the student task in Student View and test the exact sign-in, link, file, or submission path students will use.</li><li>Prepare only the listed existing materials; do not require a personal account or a new unlisted product.</li><li>Keep the current student page available as the accessible and absence route.</li></ul>
<h2 style="margin:22px 0 8px;font-size:20px;color:#0E7C7B;">Lesson flow</h2>
<ol style="margin:0 0 16px;padding-left:24px;">{flow}</ol>
<div style="background:#E4F1F1;border-radius:10px;padding:14px 16px;margin:0 0 16px;">
  <h2 style="margin:0 0 6px;font-size:19px;color:#0E7C7B;">Scaffolds and teacher decisions</h2>
  <p style="margin:0;">Keep the student lesson's bilingual tabs, word bank, models, and current support route in view while students work. Reduce the number of examples or provide a partially completed planning frame before reducing the evidence. If a student needs an alternate format, preserve the same named evidence and use the current rubric or teacher judgment rather than adding a hidden requirement.</p>
</div>
<h2 style="margin:22px 0 8px;font-size:20px;color:#0E7C7B;">Close the loop</h2>
<p style="margin:0 0 16px;">Use the current Canvas submission for grading. Record the specific misconception, access issue, or revision need you observed; use it to choose the next lesson's launch rather than creating a duplicate exit assignment.</p>
</div>'''


def pages_by_title(canvas: Canvas, course_id: int) -> dict[str, dict]:
    return {row["title"]: row for row in canvas.paged(f"/courses/{course_id}/pages?per_page=100")}


def module_items(canvas: Canvas, course_id: int, module_id: int) -> list[dict]:
    return canvas.paged(f"/courses/{course_id}/modules/{module_id}/items?per_page=100")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write pages and module items to Canvas.")
    args = parser.parse_args()
    course_id = env_course_id()
    canvas = Canvas()
    all_specs = specs()
    if len(all_specs) != 53:
        raise RuntimeError(f"Expected 53 lesson-guide specs, found {len(all_specs)}")

    existing_pages = pages_by_title(canvas, course_id)
    created: list[dict] = []
    skipped: list[dict] = []
    alignment_by_module: dict[int, str] = {}
    for module_id, slug in OVERVIEW_SLUG.items():
        overview = canvas.get(f"/courses/{course_id}/pages/{slug}")
        alignment_by_module[module_id] = alignment_block(overview.get("body") or "")

    for spec in all_specs:
        title = f"Teacher Guide: {spec.short_title}"
        items = module_items(canvas, course_id, spec.module_id)
        target = next((item for item in items if item["id"] == spec.target_item_id), None)
        if target is None:
            raise RuntimeError(f"Target module item {spec.target_item_id} is not in module {spec.module_id}")
        page = existing_pages.get(title)
        if page:
            page_body_live = canvas.get(f"/courses/{course_id}/pages/{page['url']}").get("body") or ""
            if f'data-vils-target-module-item="{spec.target_item_id}"' not in page_body_live:
                raise RuntimeError(f"Existing page title conflicts with expected guide: {title}")
            item = next((row for row in items if row.get("page_url") == page["url"]), None)
            if not item:
                if not args.apply:
                    skipped.append({"title": title, "target": spec.target_item_id, "action": "would insert existing page"})
                    continue
                created_item, _ = canvas.request("POST", f"/courses/{course_id}/modules/{spec.module_id}/items", {
                    "module_item[type]": "Page", "module_item[page_url]": page["url"], "module_item[position]": str(target["position"]), "module_item[published]": "false"})
                created.append({"title": title, "page_url": page["url"], "module_item_id": created_item["id"], "target": spec.target_item_id, "action": "inserted existing page"})
            else:
                skipped.append({"title": title, "target": spec.target_item_id, "module_item_id": item["id"], "action": "already present"})
            continue
        if not args.apply:
            created.append({"title": title, "target": spec.target_item_id, "action": "would create"})
            continue
        new_page, _ = canvas.request("POST", f"/courses/{course_id}/pages", {
            "wiki_page[title]": title, "wiki_page[body]": page_body(spec, target, alignment_by_module[spec.module_id]),
            "wiki_page[published]": "false", "wiki_page[hide_from_students]": "true", "wiki_page[editing_roles]": "teachers", "wiki_page[notify_of_update]": "false"})
        existing_pages[title] = new_page
        new_item, _ = canvas.request("POST", f"/courses/{course_id}/modules/{spec.module_id}/items", {
            "module_item[type]": "Page", "module_item[page_url]": new_page["url"], "module_item[position]": str(target["position"]), "module_item[published]": "false"})
        created.append({"title": title, "page_url": new_page["url"], "module_item_id": new_item["id"], "target": spec.target_item_id, "action": "created"})

    # Placement and content verification deliberately rereads live Canvas, but
    # a dry run must remain read-only and cannot expect pages that do not exist.
    verified: list[dict] = []
    if args.apply:
        for spec in all_specs:
            title = f"Teacher Guide: {spec.short_title}"
            page = pages_by_title(canvas, course_id).get(title)
            if not page:
                raise RuntimeError(f"Missing expected page after apply: {title}")
            body = canvas.get(f"/courses/{course_id}/pages/{page['url']}").get("body") or ""
            if MARKER not in body or f'data-vils-target-module-item="{spec.target_item_id}"' not in body:
                raise RuntimeError(f"Guide contract marker missing: {title}")
            items = sorted(module_items(canvas, course_id, spec.module_id), key=lambda item: item["position"])
            guide_index = next((index for index, item in enumerate(items) if item.get("page_url") == page["url"]), None)
            if guide_index is None or guide_index + 1 >= len(items) or items[guide_index + 1]["id"] != spec.target_item_id:
                raise RuntimeError(f"Guide is not immediately before target {spec.target_item_id}: {title}")
            verified.append({"title": title, "page_url": page["url"], "target": spec.target_item_id, "guide_module_item_id": items[guide_index]["id"]})

    import json
    print(json.dumps({"course_id": course_id, "apply": args.apply, "created": created, "skipped": skipped, "verified": verified, "counts": {"specs": len(all_specs), "created": len(created), "skipped": len(skipped), "verified": len(verified)}}, indent=2))


if __name__ == "__main__":
    main()
