#!/usr/bin/env python3
"""Apply the Coding Foundations Retrofit to Canvas course 23402.

Dry-run is the default. The --apply path preserves existing item identities and
publication states, uploads reviewed source assets, updates five existing
lesson pairs in place, and adds the two-day text-code bridge plus checkpoint.
Run the normal Canvas-to-site sync only after this script verifies live state.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import mimetypes
import os
import re
import urllib.parse
import urllib.request
import uuid
from dataclasses import dataclass
from pathlib import Path

from apply_teks_alignment import expectation_text
from canvas_api import Canvas, DEFAULT_BASE, env_course_id


ROOT = Path(__file__).resolve().parents[1]
HOST = "https://verizoninnovativelearning.instructure.com"
COURSE_ID = 23402
INTRO_MODULE_ID = 72573
VIDEO_MODULE_ID = 72574
RVR_MODULE_ID = 72580
MINOR_GROUP_ID = 34828
MAJOR_GROUP_ID = 34827
MARKER = 'data-vils-coding-foundations="2026-08-22"'
OVERVIEW_MARKER = 'data-vils-coding-foundations-overview="2026-08-22"'

DRIVE_PASSPORT_EN = "1fJGKVRLazdLojOlnwIUrpb9xfv5X9ukQRYdUPjRtuGc"
DRIVE_PASSPORT_ES = "1pcosaTw_XiBPEq8G4j1YoyoF6ZhLHTA_pX3yq2hveYE"
DRIVE_DECK = "1oi0ZohdSAbD5q0gtJlWyse3yTv-qbzLKumGedSkgA0s"

ASSETS = {
    "passport_en_docx": ROOT / "curriculum-assets/coding-foundations/Coding_Foundations_Passport_EN.docx",
    "passport_en_pdf": ROOT / "curriculum-assets/coding-foundations/Coding_Foundations_Passport_EN.pdf",
    "passport_es_docx": ROOT / "curriculum-assets/coding-foundations/Coding_Foundations_Passport_ES.docx",
    "passport_es_pdf": ROOT / "curriculum-assets/coding-foundations/Coding_Foundations_Passport_ES.pdf",
    "teacher_deck": ROOT / "curriculum-assets/coding-foundations/Smart_Solutions_Coding_Foundations_Retrofit_Teacher_Deck_2027.pptx",
    "screenshot_code": ROOT / "curriculum-assets/coding-foundations/makecode-supply-grid-code.png",
    "screenshot_variables": ROOT / "curriculum-assets/coding-foundations/makecode-supply-grid-variables.png",
    "screenshot_result": ROOT / "curriculum-assets/coding-foundations/makecode-supply-grid-result.png",
    "bug_challenge": ROOT / "curriculum-assets/coding-foundations/Emergency_Supply_Grid_Bug_Challenge.txt",
    "core_starter": ROOT / "curriculum-assets/coding-foundations/Emergency_Supply_Grid_Core_Starter.txt",
    "exemplar": ROOT / "curriculum-assets/coding-foundations/Emergency_Supply_Grid_Exemplar.txt",
}


@dataclass(frozen=True)
class ExistingSpec:
    module_id: int
    kind: str
    identity: str | int
    title: str
    expected_sha256: str
    checkpoint: int
    timing: str
    slide_range: str
    evidence_en: str
    evidence_es: str


EXISTING = (
    ExistingSpec(INTRO_MODULE_ID, "page", "facilitator-guide-code-+-web-day-1-algorithm-+-first-program", "Facilitator Guide: Code + Web Day 1 — Algorithm + First Program", "8fc94f73bb21e425acfddb364add70cdb8bf7cdce38dc0e79cf051e87996fb84", 1, "15–20 minutes inside the current period", "Slides 3–6", "Passport Checkpoint 1: goal, inputs/outputs, three subproblems, first pseudocode draft, and literal partner test.", "Punto de control 1: meta, entradas/salidas, tres subproblemas, primer borrador de pseudocódigo y prueba literal."),
    ExistingSpec(INTRO_MODULE_ID, "assignment", 1183240, "Day 1: Your First Code", "4479d0362d42b4594f0923ae05f63b4d25476ce370fe505162a6d9c714a20ec5", 1, "15–20 minutes", "Slides 3–6", "Complete Passport Checkpoint 1 before the Code.org blocks, then submit one readable Passport screenshot with the existing evidence.", "Completa el Punto de control 1 antes de los bloques de Code.org y entrega una captura legible junto con la evidencia existente."),
    ExistingSpec(INTRO_MODULE_ID, "page", "facilitator-guide-code-+-web-day-2-choice-coding-+-patterns", "Facilitator Guide: Code + Web Day 2 — Choice Coding + Patterns", "495de271db81e828635ddd5d678ec562180304d565618280680892e414cfd8b6", 2, "10–15 minutes inside the current period", "Slides 7–9", "Passport Checkpoint 2: repeated pattern, iteration benefit, variables/types/operations, and generalized pseudocode.", "Punto de control 2: patrón repetido, beneficio de la iteración, variables/tipos/operaciones y pseudocódigo generalizado."),
    ExistingSpec(INTRO_MODULE_ID, "assignment", 1183242, "Day 2: Hour of Code", "1bbae9da126641023f7006a82ae52bc5edf19b5a3816d524dd77d5191d37be17", 2, "10–15 minutes", "Slides 7–9", "Complete Passport Checkpoint 2 using a pattern from the selected Hour of Code activity; submit a readable checkpoint screenshot with the existing evidence.", "Completa el Punto de control 2 con un patrón de la actividad seleccionada y entrega una captura legible junto con la evidencia existente."),
    ExistingSpec(INTRO_MODULE_ID, "page", "facilitator-guide-code-+-web-day-3-predict-debug-+-log", "Facilitator Guide: Code + Web Day 3 — Predict, Debug + Log", "1950346e2594a5129585ee83318d97b5e55ddca4f541c290d86edeb1467341ff", 3, "10–15 minutes inside the current period", "Slides 10–12", "Passport Checkpoint 3: three prediction/observation/change/result records, revised pseudocode, and an improvement claim.", "Punto de control 3: tres registros de predicción/observación/cambio/resultado, pseudocódigo revisado y una afirmación de mejora."),
    ExistingSpec(INTRO_MODULE_ID, "assignment", 1183246, "Day 3: Debugging Detective", "f2e048ffe09aee06e80d34c5c2602bbb0c4c4c52b99bb915e81417078d1035fe", 3, "10–15 minutes", "Slides 10–12", "Use Passport Checkpoint 3 as the three-bug log. Revise the matching pseudocode after each successful repair and submit a readable checkpoint screenshot.", "Usa el Punto de control 3 como registro de tres errores. Revisa el pseudocódigo correspondiente después de cada reparación y entrega una captura legible."),
    ExistingSpec(VIDEO_MODULE_ID, "page", "facilitator-guide-video-game-design-lesson-2-remix-test-+-explain", "Facilitator Guide: Video Game Design Lesson 2 — Remix, Test + Explain", "f34268145bd0b206dd5f0681d209d68651eb1ec8c66d41fe65fd75788a99a802", 4, "10–15 minutes before students edit", "Slides 13–14", "Passport Checkpoint 4: feature goal, WHEN/SHOULD statement, feature pseudocode, and one test result.", "Punto de control 4: meta de la función, enunciado CUANDO/DEBE, pseudocódigo de la función y un resultado de prueba."),
    ExistingSpec(VIDEO_MODULE_ID, "assignment", 1183360, "Lesson 2: Remix", "71c31b86768f5d830804faca8500b86fea422a447b872363816df74f627f2c4f", 4, "10–15 minutes", "Slides 13–14", "Plan one required feature in Passport Checkpoint 4 before adding it. Submit a readable checkpoint screenshot with the existing remix evidence.", "Planea una función requerida en el Punto de control 4 antes de agregarla. Entrega una captura legible junto con la evidencia del remix."),
    ExistingSpec(RVR_MODULE_ID, "page", "facilitator-guide-rvr-day-1-draw-plan-program-prove", "Facilitator Guide: RVR Day 1 — Draw, Plan, Program, Prove", "873e42bb4597b283af6f7aba86b5132b5ebe5af686b84939393200d96941bc42", 5, "15–20 minutes before and after the first run", "Slides 24–26", "Passport Checkpoint 5: roles, timeline, robot pseudocode, literal execution result, revision, and final transfer reflection.", "Punto de control 5: roles, línea de tiempo, pseudocódigo del robot, resultado literal, revisión y reflexión final."),
    ExistingSpec(RVR_MODULE_ID, "assignment", 1183265, "Day 1 · Drawing Mission: Plan, Program, Prove", "7d791169b3dd066e62d4a3cfa0a0a8fceb465bee5aec194eb1b08d505b87eadf", 5, "15–20 minutes", "Slides 24–26", "Complete Passport Checkpoint 5 with your team before the first RVR run and revise it after the test. Submit a readable checkpoint screenshot with the existing mission evidence.", "Completa el Punto de control 5 con tu equipo antes de la primera prueba de RVR y revísalo después. Entrega una captura legible junto con la evidencia de la misión."),
)


def digest(text: str) -> str:
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()


def find_marked_div(body: str, marker: str) -> tuple[int, int] | None:
    match = re.search(rf"<div\b[^>]*{re.escape(marker)}[^>]*>", body, re.I)
    if not match:
        return None
    depth = 0
    for token in re.finditer(r"</?div\b[^>]*>", body[match.start():], re.I):
        if token.group(0).lower().startswith("</"):
            depth -= 1
            if depth == 0:
                return match.start(), match.start() + token.end()
        else:
            depth += 1
    raise RuntimeError(f"Unclosed marked div: {marker}")


def upsert_block(body: str, marker: str, block: str) -> str:
    found = find_marked_div(body, marker)
    if found:
        return body[: found[0]] + block + body[found[1] :]
    return (body or "") + block


def upsert_prefixed_block(body: str, marker: str, block: str) -> str:
    """Replace an existing marked block or place a new notice first."""
    found = find_marked_div(body, marker)
    if found:
        return body[: found[0]] + block + body[found[1] :]
    return block + (body or "")


def canvas_file_anchor(course_id: int, row: dict, label: str) -> str:
    file_id = int(row["id"])
    href = f"{HOST}/courses/{course_id}/files/{file_id}?wrap=1"
    api = f"{HOST}/api/v1/courses/{course_id}/files/{file_id}"
    return f'<a href="{href}" target="_blank" data-api-endpoint="{api}" data-api-returntype="File"><strong>{html.escape(label)}</strong></a>'


def canvas_image(course_id: int, row: dict, alt: str) -> str:
    file_id = int(row["id"])
    src = f"{HOST}/courses/{course_id}/files/{file_id}/preview"
    api = f"{HOST}/api/v1/courses/{course_id}/files/{file_id}"
    return f'<img src="{src}" alt="{html.escape(alt)}" style="max-width:100%;height:auto;border:1px solid #CFD8DC;border-radius:10px;" data-api-endpoint="{api}" data-api-returntype="File">'


def google_copy(kind: str, file_id: str, label: str) -> str:
    return f'<a href="https://docs.google.com/{kind}/d/{file_id}/copy" target="_blank"><strong>{html.escape(label)}</strong></a>'


def passport_links(course_id: int, files: dict[str, dict]) -> str:
    return (
        '<ul style="margin:8px 0 0;padding-left:22px;">'
        f'<li>English: {google_copy("document", DRIVE_PASSPORT_EN, "Make a Google copy")} · {canvas_file_anchor(course_id, files["passport_en_docx"], "Word")} · {canvas_file_anchor(course_id, files["passport_en_pdf"], "PDF")}</li>'
        f'<li>Español: {google_copy("document", DRIVE_PASSPORT_ES, "Crear una copia de Google")} · {canvas_file_anchor(course_id, files["passport_es_docx"], "Word")} · {canvas_file_anchor(course_id, files["passport_es_pdf"], "PDF")}</li>'
        '</ul>'
    )


def exact_teks(codes: tuple[str, ...]) -> str:
    return "".join(f"<li><strong>{html.escape(code)}</strong> — {html.escape(expectation_text(code))}</li>" for code in codes)


def existing_teacher_block(spec: ExistingSpec, course_id: int, files: dict[str, dict]) -> str:
    return f'''<div {MARKER} data-vils-checkpoint="{spec.checkpoint}" style="margin:18px 0;padding:16px 18px;border:3px solid #00B8C8;border-radius:14px;background:#F4FBFC;color:#172033;">
<p style="margin:0 0 5px;color:#0E7C7B;"><strong>CODING FOUNDATIONS RETROFIT · PASSPORT CHECKPOINT {spec.checkpoint}</strong></p>
<h2 style="margin:0 0 8px;font-size:21px;color:#172033;">Fold this planning evidence into the current lesson</h2>
<p style="margin:0 0 8px;"><strong>Added time:</strong> {html.escape(spec.timing)}<br><strong>Projectable support:</strong> {google_copy("presentation", DRIVE_DECK, f"Editable retrofit deck, {spec.slide_range}")} · {canvas_file_anchor(course_id, files["teacher_deck"], "PowerPoint fallback")}</p>
<p style="margin:0 0 8px;"><strong>Required evidence:</strong> {html.escape(spec.evidence_en)}</p>
{passport_links(course_id, files)}
<p style="margin:10px 0 0;"><strong>Teacher move:</strong> Check the assigned Passport checkpoint instead of creating a second worksheet or a separate pseudocode unit. Preserve the current assignment points and submission route.</p>
</div>'''


def existing_student_block(spec: ExistingSpec, course_id: int, files: dict[str, dict]) -> str:
    return f'''<div {MARKER} data-vils-checkpoint="{spec.checkpoint}" style="margin:18px 0;padding:16px 18px;border:3px solid #00B8C8;border-radius:14px;background:#F4FBFC;color:#172033;">
<p style="margin:0 0 5px;color:#0E7C7B;"><strong>CODING FOUNDATIONS · PASSPORT CHECKPOINT {spec.checkpoint}</strong></p>
<h2 style="margin:0 0 10px;font-size:21px;color:#172033;">Add the planning evidence to today's work</h2>
<h3 style="margin:0 0 5px;font-size:18px;color:#172033;">English</h3><p style="margin:0 0 8px;">{html.escape(spec.evidence_en)}</p>
<h3 style="margin:10px 0 5px;font-size:18px;color:#172033;">Español</h3><p style="margin:0 0 8px;">{html.escape(spec.evidence_es)}</p>
{passport_links(course_id, files)}
<p style="margin:10px 0 0;"><strong>Turn in / Entrega:</strong> Keep the current assignment evidence. Add one readable screenshot or photo of the assigned Passport checkpoint.</p>
</div>'''


def overview_block(course_id: int, files: dict[str, dict]) -> str:
    return f'''<div {OVERVIEW_MARKER} style="margin:0 0 18px;padding:18px;border:3px solid #00B8C8;border-radius:14px;background:#F4FBFC;color:#172033;">
<p style="margin:0 0 5px;color:#0E7C7B;"><strong>2027 REQUIRED TECH APPS BRIDGE</strong></p>
<h2 style="margin:0 0 8px;font-size:22px;color:#172033;">Video Game Design now runs four class periods</h2>
<ol style="margin:0 0 10px;padding-left:22px;"><li>Lesson 1: Skillmap</li><li>Lesson 2: Remix</li><li>Lesson 3: Trace, Predict + Repair Text Code</li><li>Lesson 4: Emergency Supply Grid</li></ol>
<p style="margin:0 0 8px;"><strong>Added evidence:</strong> named variables with string, number, and Boolean types; operations on values; and a text-based program with nested loops addressing row and column subproblems.</p>
<p style="margin:0;">{google_copy("presentation", DRIVE_DECK, "Editable Coding Foundations teacher deck")} · {canvas_file_anchor(course_id, files["teacher_deck"], "PowerPoint fallback")}</p>
</div>'''


def bridge_resources(course_id: int, files: dict[str, dict], day: int) -> str:
    source_key = "bug_challenge" if day == 1 else "core_starter"
    source_label = "Bug Challenge starter code" if day == 1 else "Core starter code"
    return (
        f'<p style="margin:0 0 8px;"><a href="https://arcade.makecode.com/" target="_blank"><strong>Open MakeCode Arcade</strong></a> · '
        f'{canvas_file_anchor(course_id, files[source_key], source_label)}</p>'
        + passport_links(course_id, files)
    )


def bridge_student_body(course_id: int, files: dict[str, dict], day: int) -> str:
    if day == 1:
        title = "Lesson 3: Text Code — Trace, Predict + Repair"
        objective = "Students will trace a text program, predict nested-loop results, identify named variable types and operations, and repair one loop bug from evidence."
        teks = ("§126.19(c)(1)(A)", "§126.19(c)(1)(B)", "§126.19(c)(1)(E)", "§126.19(c)(1)(F)", "§126.19(c)(2)(A)", "§126.19(c)(2)(B)", "§126.19(c)(2)(C)")
        steps_en = [
            "Open a new MakeCode Arcade project, name it Emergency Supply Grid, and select JavaScript.",
            "Open the Bug Challenge text file. Copy all of the code into the JavaScript editor.",
            "On Passport Checkpoint 4, identify missionName, rows/columns, priorityMode, and suppliesPlaced. Record each type, purpose, and predicted value.",
            "Predict a 3 × 4 grid and 12 supplies. Run the code. Capture the 3 × 3 result and score 9 before repairing it.",
            "Find the inner-loop condition that uses the wrong boundary. Change one word, run again, and capture the corrected 3 × 4 grid and score 12.",
            "Explain why the inner loop is the column subproblem and the outer loop is the row subproblem.",
        ]
        steps_es = [
            "Abre un proyecto nuevo de MakeCode Arcade, nómbralo Emergency Supply Grid y selecciona JavaScript.",
            "Abre el archivo Bug Challenge y copia todo el código en el editor.",
            "En el Punto de control 4, identifica missionName, rows/columns, priorityMode y suppliesPlaced. Registra tipo, propósito y valor previsto.",
            "Predice una cuadrícula de 3 × 4 y 12 suministros. Ejecuta el código. Captura el resultado de 3 × 3 y la puntuación 9 antes de repararlo.",
            "Encuentra la condición del bucle interior que usa el límite equivocado. Cambia una palabra, ejecuta otra vez y captura 3 × 4 con puntuación 12.",
            "Explica por qué el bucle interior resuelve columnas y el exterior resuelve filas.",
        ]
        evidence = "Passport trace table, before/after screenshots, corrected JavaScript, and a nested-loop explanation."
        screenshot = canvas_image(course_id, files["screenshot_variables"], "MakeCode Arcade JavaScript editor showing named variables and nested loops")
        deck_range = "Slides 15–21"
    else:
        title = "Lesson 4: Text Code — Emergency Supply Grid"
        objective = "Students will use a software design process to modify a text-based real-world program with named data types, operations, and nested loops, then test and explain the result."
        teks = ("§126.19(c)(1)(A)", "§126.19(c)(1)(C)", "§126.19(c)(1)(E)", "§126.19(c)(1)(F)", "§126.19(c)(2)(A)", "§126.19(c)(2)(B)", "§126.19(c)(2)(C)")
        steps_en = [
            "Start from your corrected Day 1 project or the Core Starter text file.",
            "Choose Mission A: 4 rows, 5 columns, xSpacing 28, ySpacing 25; or Mission B: 2 rows, 6 columns, xSpacing 24, ySpacing 50.",
            "Predict the total supplies and one x/y position before Run.",
            "Change missionName and use priorityMode to control the priority route. Keep all work in JavaScript view.",
            "Run, capture the complete grid and visible score, and make one controlled revision if markers overlap or leave the screen.",
            "Submit readable code and simulator screenshots plus the completed Passport trace/test evidence and explanation.",
        ]
        steps_es = [
            "Empieza con tu proyecto corregido del Día 1 o con el archivo Core Starter.",
            "Escoge Misión A: 4 filas, 5 columnas, xSpacing 28, ySpacing 25; o Misión B: 2 filas, 6 columnas, xSpacing 24, ySpacing 50.",
            "Predice el total y una posición x/y antes de ejecutar.",
            "Cambia missionName y usa priorityMode para controlar la ruta de prioridad. Trabaja en la vista JavaScript.",
            "Ejecuta, captura la cuadrícula completa y la puntuación, y haz una revisión controlada si los marcadores se enciman o salen de la pantalla.",
            "Entrega capturas legibles del código y simulador, la evidencia del Pasaporte y tu explicación.",
        ]
        evidence = "Modified JavaScript, grid/score screenshot, prediction and controlled-test evidence, and explanation of how the nested loops address row and column subproblems."
        screenshot = canvas_image(course_id, files["screenshot_result"], "MakeCode Arcade simulator showing a three-row by four-column supply grid and score 12")
        deck_range = "Slides 22–23"
    list_en = "".join(f"<li style=\"margin:0 0 7px;\">{html.escape(value)}</li>" for value in steps_en)
    list_es = "".join(f"<li style=\"margin:0 0 7px;\">{html.escape(value)}</li>" for value in steps_es)
    return f'''<div {MARKER} data-vils-text-code-day="{day}" style="max-width:980px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:#172033;font-size:16px;line-height:1.5;">
<div style="background:#0B1426;border:3px solid #00B8C8;border-radius:16px;padding:20px;color:#fff;"><p style="margin:0;color:#80DEEA;"><strong>TEXT-CODE BRIDGE · DAY {day}</strong></p><h1 style="margin:6px 0;color:#fff;font-size:27px;">{html.escape(title)}</h1><p style="margin:0;">Emergency Supply Grid · MakeCode Arcade JavaScript</p></div>
<div style="margin:16px 0;padding:16px 18px;border:2px solid #274C77;border-radius:12px;background:#F4F8FC;"><h2 style="margin-top:0;">Daily Learning Contract</h2><p><strong>Objective:</strong> {html.escape(objective)}</p><p><strong>TEKS:</strong></p><ul>{exact_teks(teks)}</ul><p><strong>Demonstration of learning:</strong> {html.escape(evidence)}</p></div>
<div style="margin:16px 0;padding:16px;border-left:7px solid #00B8C8;background:#F4FBFC;"><h2 style="margin-top:0;">Open the tools and files</h2>{bridge_resources(course_id, files, day)}</div>
<div style="margin:16px 0;padding:16px;border:2px solid #54B68A;border-radius:12px;"><h2 style="margin-top:0;">English</h2><ol>{list_en}</ol></div>
<div style="margin:16px 0;padding:16px;border:2px solid #A970FF;border-radius:12px;"><h2 style="margin-top:0;">Español</h2><ol>{list_es}</ol></div>
<div style="margin:16px 0;">{screenshot}</div>
<div style="margin:16px 0;padding:16px;border:2px solid #FFD166;border-radius:12px;background:#FFFBE8;"><h2 style="margin-top:0;">Turn in / Entrega</h2><p style="margin:0;">{html.escape(evidence)} Upload screenshots or files through this assignment. Do not submit your school password, personal email, or a public profile.</p></div>
</div>'''


def bridge_teacher_body(course_id: int, files: dict[str, dict], day: int, student_title: str) -> str:
    if day == 1:
        objective = "Students will trace a text program, predict its output, identify named data types and operations, and repair one nested-loop boundary bug from evidence."
        evidence = "Passport trace table, before/after simulator screenshots, corrected JavaScript, and row/column explanation."
        slides = "15–21"
        checks = ["Students predict 12 before Run.", "The bugged code produces 9 because the inner loop uses rows.", "The repaired inner loop uses columns and produces 12.", "Students can name string, number, and Boolean variables plus an operation on values."]
    else:
        objective = "Students will modify and test a text-based real-world program with named variables, multiple data types, operations, and nested loops."
        evidence = "Modified JavaScript, grid/score screenshot, prediction, controlled revision, and explanation of the row and column subproblems."
        slides = "22–23"
        checks = ["The student remains in JavaScript view.", "Two nested loops are visible in submitted code.", "The chosen dimensions and spacing keep every marker on screen.", "The explanation connects outer rows and inner columns to distinct subproblems."]
    checklist = "".join(f"<li>{html.escape(value)}</li>" for value in checks)
    return f'''<div {MARKER} data-vils-text-code-guide="{day}" style="max-width:980px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:#172033;font-size:16px;line-height:1.5;">
<div style="background:#0B1426;border:3px solid #00B8C8;border-radius:16px;padding:20px;color:#fff;"><p style="margin:0;color:#80DEEA;"><strong>TEACHER ONLY · TEXT-CODE BRIDGE DAY {day}</strong></p><h1 style="margin:6px 0;color:#fff;font-size:27px;">{html.escape(student_title)}</h1><p style="margin:0;">One class period · keep the student page as the independent and absence route.</p></div>
<div style="margin:16px 0;padding:16px 18px;border:2px solid #274C77;border-radius:12px;background:#F4F8FC;"><h2 style="margin-top:0;">Daily Learning Contract</h2><p><strong>Objective:</strong> {html.escape(objective)}</p><p><strong>Demonstration of learning:</strong> {html.escape(evidence)}</p><p><strong>Exact standards:</strong></p><ul>{exact_teks(("§126.19(c)(2)(A)", "§126.19(c)(2)(B)", "§126.19(c)(2)(C)"))}</ul></div>
<div style="margin:16px 0;padding:16px;border-left:7px solid #00B8C8;background:#F4FBFC;"><h2 style="margin-top:0;">Before class</h2><p>{google_copy("presentation", DRIVE_DECK, f"Open editable teacher deck, slides {slides}")} · {canvas_file_anchor(course_id, files["teacher_deck"], "PowerPoint fallback")}</p>{bridge_resources(course_id, files, day)}<p><strong>Student route:</strong> {html.escape(student_title)}</p></div>
<div style="margin:16px 0;padding:16px;border:2px solid #54B68A;border-radius:12px;"><h2 style="margin-top:0;">What to check</h2><ul>{checklist}</ul><p><strong>Support:</strong> Provide the complete starter text, a printed/Google Passport, and tested configuration choices before reducing the explanation. Students may explain orally when the teacher records the same evidence.</p></div>
<div style="margin:16px 0;padding:16px;border:2px solid #FFD166;border-radius:12px;background:#FFFBE8;"><h2 style="margin-top:0;">Recovery route</h2><p>When a project is lost, create a new project and paste the starter text again. No account, share link, or imported project file is required. When code will not run, check the exact line marker and brackets before replacing the program.</p></div>
</div>'''


def quiz_description() -> str:
    return f'''<div {MARKER} style="max-width:900px;margin:0 auto;font-size:16px;line-height:1.5;"><div style="background:#0B1426;border:3px solid #00B8C8;border-radius:14px;padding:18px;color:#fff;"><h2 style="margin:0;color:#fff;">Checkpoint: Text Code + Nested Loops</h2><p style="margin:6px 0 0;">Eight questions · unlimited attempts · highest score kept</p></div><p>Use your Emergency Supply Grid code and Passport. Read the feedback, return to the exact line, and retry.</p><p><strong>TEKS:</strong> §126.19(c)(2)(A)–(C)</p></div>'''


QUIZ_QUESTIONS = (
    ("Q1 Pseudocode", "Why is pseudocode useful before coding?", ("It documents a precise human-readable plan that can be tested and revised.", "It makes the program run faster.", "It replaces all executable code.", "It chooses colors for the project."), 0),
    ("Q2 Nested loop count", "A grid uses rows = 3 and columns = 4. How many times should the inner loop place a supply?", ("7", "9", "12", "16"), 2),
    ("Q3 String type", "Which variable stores a string?", ("missionName", "rows", "priorityMode", "suppliesPlaced"), 0),
    ("Q4 Boolean type", "Which variable stores a Boolean value?", ("columns", "missionName", "priorityMode", "suppliesPlaced"), 2),
    ("Q5 Operation", "What does suppliesPlaced += 1 do?", ("Resets the value to 1.", "Adds 1 to the current value.", "Compares the value with 1.", "Turns the value into text."), 1),
    ("Q6 Boundary bug", "The inner loop uses column < rows instead of column < columns. With rows = 3 and columns = 4, what is the likely result?", ("A 3 × 3 grid with 9 supplies.", "A 4 × 4 grid with 16 supplies.", "No code runs at all.", "The string variable changes."), 0),
    ("Q7 Meaningful variable", "Which name best communicates the number of supplies already placed?", ("x", "thing", "suppliesPlaced", "variable1"), 2),
    ("Q8 Subproblems", "How do the nested loops address different subproblems?", ("Both loops do exactly the same job.", "The outer loop advances through rows while the inner loop completes the columns in each row.", "The outer loop stores text while the inner loop stores a Boolean.", "The loops only change the background color."), 1),
)


def encode_multipart(fields: dict[str, str], file_path: Path, content_type: str) -> tuple[bytes, str]:
    boundary = f"----VILS{uuid.uuid4().hex}"
    chunks: list[bytes] = []
    for key, value in fields.items():
        chunks.extend((f"--{boundary}\r\n".encode(), f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode(), str(value).encode(), b"\r\n"))
    chunks.extend((
        f"--{boundary}\r\n".encode(),
        f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'.encode(),
        f"Content-Type: {content_type}\r\n\r\n".encode(),
        file_path.read_bytes(),
        b"\r\n",
        f"--{boundary}--\r\n".encode(),
    ))
    return b"".join(chunks), boundary


def upload_canvas_file(canvas: Canvas, course_id: int, file_path: Path) -> dict:
    search = urllib.parse.quote(file_path.name)
    matches = canvas.paged(f"/courses/{course_id}/files?search_term={search}&per_page=100")
    exact = [
        row
        for row in matches
        if row.get("display_name") == file_path.name
        and int(row.get("size") or 0) == file_path.stat().st_size
    ]
    if exact:
        return max(exact, key=lambda row: int(row["id"]))
    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    init, _ = canvas.request("POST", f"/courses/{course_id}/files", {
        "name": file_path.name,
        "size": str(file_path.stat().st_size),
        "content_type": content_type,
        "parent_folder_path": "coding-foundations-retrofit",
        "on_duplicate": "overwrite",
    })
    if init.get("id"):
        return init
    body, boundary = encode_multipart({str(k): str(v) for k, v in (init.get("upload_params") or {}).items()}, file_path, content_type)
    request = urllib.request.Request(init["upload_url"], data=body, method="POST", headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(request, timeout=300) as response:
        payload = response.read()
    result = json.loads(payload) if payload else {}
    if isinstance(result, dict) and result.get("attachments"):
        result = result["attachments"][0]
    if not result.get("id"):
        raise RuntimeError(f"Canvas file upload did not return a file id for {file_path.name}: {result}")
    return result


def all_module_items(canvas: Canvas, course_id: int, module_id: int) -> list[dict]:
    return canvas.paged(f"/courses/{course_id}/modules/{module_id}/items?per_page=100")


def all_pages(canvas: Canvas, course_id: int) -> dict[str, dict]:
    return {row["title"]: row for row in canvas.paged(f"/courses/{course_id}/pages?per_page=100")}


def all_assignments(canvas: Canvas, course_id: int) -> dict[str, dict]:
    return {row["name"]: row for row in canvas.paged(f"/courses/{course_id}/assignments?per_page=100")}


def all_quizzes(canvas: Canvas, course_id: int) -> dict[str, dict]:
    return {row["title"]: row for row in canvas.paged(f"/courses/{course_id}/quizzes?per_page=100")}


def update_existing(canvas: Canvas, course_id: int, spec: ExistingSpec, files: dict[str, dict], apply: bool):
    if spec.kind == "page":
        live = canvas.get(f"/courses/{course_id}/pages/{spec.identity}")
        body = live.get("body") or ""
        title = live.get("title")
        block = existing_teacher_block(spec, course_id, files)
    else:
        live = canvas.get(f"/courses/{course_id}/assignments/{spec.identity}")
        body = live.get("description") or ""
        title = live.get("name")
        block = existing_student_block(spec, course_id, files)
    if title != spec.title:
        raise RuntimeError(f"Identity/title mismatch for {spec.kind} {spec.identity}: {title!r}")
    if MARKER not in body and digest(body) != spec.expected_sha256:
        raise RuntimeError(f"Live body drifted before retrofit: {spec.title}")
    new_body = upsert_block(body, MARKER, block)
    print(("APPLY" if apply else "DRY"), "UPDATE", spec.title, digest(body)[:10], "->", digest(new_body)[:10])
    if apply and new_body != body:
        if spec.kind == "page":
            canvas.request("PUT", f"/courses/{course_id}/pages/{spec.identity}", {"wiki_page[body]": new_body, "wiki_page[notify_of_update]": "false"})
        else:
            canvas.request("PUT", f"/courses/{course_id}/assignments/{spec.identity}", {"assignment[description]": new_body, "assignment[notify_of_update]": "false"})


def preflight_existing(canvas: Canvas, course_id: int):
    """Fail before any upload or content write if a protected source drifted."""
    for spec in EXISTING:
        if spec.kind == "page":
            live = canvas.get(f"/courses/{course_id}/pages/{spec.identity}")
            body = live.get("body") or ""
            title = live.get("title")
        else:
            live = canvas.get(f"/courses/{course_id}/assignments/{spec.identity}")
            body = live.get("description") or ""
            title = live.get("name")
        if title != spec.title:
            raise RuntimeError(f"Identity/title mismatch for {spec.kind} {spec.identity}: {title!r}")
        if MARKER not in body and digest(body) != spec.expected_sha256:
            raise RuntimeError(f"Live body drifted before retrofit: {spec.title}")
    print("PREFLIGHT", len(EXISTING), "protected Canvas bodies match their identity locks")


def ensure_page(canvas: Canvas, course_id: int, title: str, body: str, apply: bool) -> dict | None:
    page = all_pages(canvas, course_id).get(title)
    if not apply:
        print("DRY", "UPDATE PAGE" if page else "CREATE PAGE", title)
        return page
    if page:
        canvas.request("PUT", f"/courses/{course_id}/pages/{page['url']}", {"wiki_page[body]": body, "wiki_page[published]": "false", "wiki_page[editing_roles]": "teachers", "wiki_page[notify_of_update]": "false"})
        return canvas.get(f"/courses/{course_id}/pages/{page['url']}")
    created, _ = canvas.request("POST", f"/courses/{course_id}/pages", {"wiki_page[title]": title, "wiki_page[body]": body, "wiki_page[published]": "false", "wiki_page[editing_roles]": "teachers", "wiki_page[notify_of_update]": "false"})
    return created


def ensure_assignment(canvas: Canvas, course_id: int, title: str, body: str, day: int, apply: bool) -> dict | None:
    assignment = all_assignments(canvas, course_id).get(title)
    params = {
        "assignment[name]": title,
        "assignment[description]": body,
        "assignment[points_possible]": "25" if day == 1 else "100",
        "assignment[grading_type]": "points",
        "assignment[assignment_group_id]": str(MINOR_GROUP_ID if day == 1 else MAJOR_GROUP_ID),
        "assignment[submission_types][]": ["online_upload", "online_text_entry"] if day == 1 else ["online_upload", "online_text_entry", "online_url"],
        "assignment[allowed_attempts]": "-1",
        "assignment[published]": "false",
        "assignment[notify_of_update]": "false",
    }
    if not apply:
        print("DRY", "UPDATE ASSIGNMENT" if assignment else "CREATE ASSIGNMENT", title)
        return assignment
    if assignment:
        updated, _ = canvas.request("PUT", f"/courses/{course_id}/assignments/{assignment['id']}", params)
        return updated
    created, _ = canvas.request("POST", f"/courses/{course_id}/assignments", params)
    return created


def ensure_rubric(canvas: Canvas, course_id: int, assignment: dict, apply: bool):
    live = canvas.get(f"/courses/{course_id}/assignments/{assignment['id']}?include[]=rubric&include[]=rubric_settings") if assignment else None
    if live and live.get("rubric"):
        print("RUBRIC EXISTS", live.get("rubric_settings", {}).get("title"))
        return
    if not apply:
        print("DRY CREATE RUBRIC", "Emergency Supply Grid Rubric")
        return
    params: dict[str, object] = {
        "rubric[title]": "Emergency Supply Grid Rubric",
        "rubric[free_form_criterion_comments]": "false",
        "rubric_association[association_id]": str(assignment["id"]),
        "rubric_association[association_type]": "Assignment",
        "rubric_association[use_for_grading]": "true",
        "rubric_association[purpose]": "grading",
    }
    criteria = (
        ("Text Code + Nested Loops", "Readable JavaScript uses an outer row loop and inner column loop to solve distinct subproblems."),
        ("Named Data Types + Operations", "Meaningful string, number, and Boolean variables are used with visible operations on their values."),
        ("Testing + Revision", "Prediction, screenshot, one controlled change, and observed result show a software design process."),
        ("Explanation + Evidence", "The student explains how the nested loops address the real context and submits code/simulator evidence."),
    )
    ratings = (("Exceeds", 25, "Complete, accurate, independently explained, and purposefully extended."), ("Meets", 21, "Complete and accurate with the required evidence."), ("Approaches", 19, "Partially complete or correct; one required element or explanation is weak."), ("Needs Improvement", 15, "Major required evidence is missing or the program does not demonstrate the criterion."))
    for ci, (description, long_description) in enumerate(criteria):
        prefix = f"rubric[criteria][{ci}]"
        params[f"{prefix}[description]"] = description
        params[f"{prefix}[long_description]"] = long_description
        params[f"{prefix}[points]"] = "25"
        for ri, (rating, points, rating_long) in enumerate(ratings):
            rprefix = f"{prefix}[ratings][{ri}]"
            params[f"{rprefix}[description]"] = rating
            params[f"{rprefix}[long_description]"] = rating_long
            params[f"{rprefix}[points]"] = str(points)
    canvas.request("POST", f"/courses/{course_id}/rubrics", params)


def ensure_quiz(canvas: Canvas, course_id: int, apply: bool) -> dict | None:
    title = "Checkpoint: Text Code + Nested Loops"
    quiz = all_quizzes(canvas, course_id).get(title)
    params = {
        "quiz[title]": title,
        "quiz[description]": quiz_description(),
        "quiz[quiz_type]": "assignment",
        "quiz[assignment_group_id]": str(MINOR_GROUP_ID),
        "quiz[points_possible]": "8",
        "quiz[allowed_attempts]": "-1",
        "quiz[scoring_policy]": "keep_highest",
        "quiz[shuffle_answers]": "true",
        "quiz[published]": "false",
    }
    if not apply:
        print("DRY", "UPDATE QUIZ" if quiz else "CREATE QUIZ", title)
        return quiz
    if quiz:
        quiz, _ = canvas.request("PUT", f"/courses/{course_id}/quizzes/{quiz['id']}", params)
    else:
        quiz, _ = canvas.request("POST", f"/courses/{course_id}/quizzes", params)
    questions = canvas.paged(f"/courses/{course_id}/quizzes/{quiz['id']}/questions?per_page=100")
    by_name = {row.get("question_name"): row for row in questions}
    for name, question_text, answers, correct in QUIZ_QUESTIONS:
        if name in by_name:
            continue
        qparams: dict[str, object] = {
            "question[question_name]": name,
            "question[question_text]": question_text,
            "question[question_type]": "multiple_choice_question",
            "question[points_possible]": "1",
        }
        for index, answer in enumerate(answers):
            qparams[f"question[answers][{index}][answer_text]"] = answer
            qparams[f"question[answers][{index}][answer_weight]"] = "100" if index == correct else "0"
        canvas.request("POST", f"/courses/{course_id}/quizzes/{quiz['id']}/questions", qparams)
    # Classic Quiz question points do not reliably populate the linked
    # assignment's total through the quiz endpoint. Set the gradebook total on
    # the assignment identity Canvas created for the quiz.
    quiz = canvas.get(f"/courses/{course_id}/quizzes/{quiz['id']}")
    if quiz.get("assignment_id"):
        canvas.request(
            "PUT",
            f"/courses/{course_id}/assignments/{quiz['assignment_id']}",
            {
                "assignment[points_possible]": "8",
                "assignment[published]": "false",
                "assignment[notify_of_update]": "false",
            },
        )
    return quiz


def ensure_module_item(canvas: Canvas, course_id: int, module_id: int, title: str, item_type: str, content_id: int | None, page_url: str | None, apply: bool) -> dict | None:
    item = next((row for row in all_module_items(canvas, course_id, module_id) if row.get("title") == title), None)
    if not apply:
        print("DRY", "KEEP MODULE ITEM" if item else "CREATE MODULE ITEM", title)
        return item
    if item:
        return item
    params: dict[str, object] = {"module_item[type]": item_type, "module_item[title]": title, "module_item[published]": "false"}
    if page_url:
        params["module_item[page_url]"] = page_url
    if content_id:
        params["module_item[content_id]"] = str(content_id)
    created, _ = canvas.request("POST", f"/courses/{course_id}/modules/{module_id}/items", params)
    return created


def set_module_order(canvas: Canvas, course_id: int, module_id: int, ordered_titles: list[str], apply: bool):
    items = all_module_items(canvas, course_id, module_id)
    by_title = {row["title"]: row for row in items}
    missing = [title for title in ordered_titles if title not in by_title]
    if missing:
        if apply:
            raise RuntimeError(f"Cannot order missing module items: {missing}")
        print("DRY ORDER AFTER CREATION", ordered_titles)
        return
    for position, title in enumerate(ordered_titles, start=1):
        if apply:
            canvas.request("PUT", f"/courses/{course_id}/modules/{module_id}/items/{by_title[title]['id']}", {"module_item[position]": str(position)})
    print(("APPLY" if apply else "DRY"), "ORDER", " | ".join(ordered_titles))


def verify(canvas: Canvas, course_id: int, files: dict[str, dict]):
    for spec in EXISTING:
        if spec.kind == "page":
            row = canvas.get(f"/courses/{course_id}/pages/{spec.identity}")
            body = row.get("body") or ""
            assert row.get("published") is False
        else:
            row = canvas.get(f"/courses/{course_id}/assignments/{spec.identity}")
            body = row.get("description") or ""
            expected_published = spec.identity == 1183265
            assert bool(row.get("published")) is expected_published
        assert MARKER in body and f'data-vils-checkpoint="{spec.checkpoint}"' in body, spec.title
    module = canvas.get(f"/courses/{course_id}/modules/{VIDEO_MODULE_ID}")
    assert module.get("name") == "SW3 · Video Game Design + Text Code"
    items = sorted(all_module_items(canvas, course_id, VIDEO_MODULE_ID), key=lambda row: row["position"])
    titles = [row["title"] for row in items]
    expected_tail = [
        "Text-Code Bridge (2 days)",
        "Teacher Guide: Text-Code Bridge Day 1 — Trace, Predict + Repair",
        "Lesson 3: Text Code — Trace, Predict + Repair",
        "Teacher Guide: Text-Code Bridge Day 2 — Change the Grid with Purpose",
        "Lesson 4: Text Code — Emergency Supply Grid",
        "Checkpoint: Text Code + Nested Loops",
    ]
    assert titles[-6:] == expected_tail, titles
    for title in expected_tail:
        row = next(item for item in items if item["title"] == title)
        assert row.get("published") is False
    assignments = all_assignments(canvas, course_id)
    day2 = canvas.get(f"/courses/{course_id}/assignments/{assignments['Lesson 4: Text Code — Emergency Supply Grid']['id']}?include[]=rubric&include[]=rubric_settings")
    assert len(day2.get("rubric") or []) == 4
    quiz = all_quizzes(canvas, course_id)["Checkpoint: Text Code + Nested Loops"]
    questions = canvas.paged(f"/courses/{course_id}/quizzes/{quiz['id']}/questions?per_page=100")
    assert len(questions) == 8
    quiz_assignment = canvas.get(f"/courses/{course_id}/assignments/{quiz['assignment_id']}")
    assert float(quiz_assignment.get("points_possible") or 0) == 8
    for key, row in files.items():
        live = canvas.get(f"/files/{row['id']}")
        assert live.get("display_name") == ASSETS[key].name
        assert int(live.get("size") or 0) == ASSETS[key].stat().st_size
    print(json.dumps({"verified_existing_retrofits": len(EXISTING), "verified_new_tail": expected_tail, "verified_files": {key: row["id"] for key, row in files.items()}, "quiz_questions": len(questions)}, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    course_id = env_course_id(COURSE_ID)
    if course_id != COURSE_ID:
        raise RuntimeError(f"This sprint is identity-locked to Canvas course {COURSE_ID}; got {course_id}")
    for name, path in ASSETS.items():
        if not path.exists() or path.stat().st_size == 0:
            raise RuntimeError(f"Missing reviewed asset {name}: {path}")
    canvas = Canvas()
    preflight_existing(canvas, course_id)
    files: dict[str, dict] = {}
    if args.apply:
        for key, path in ASSETS.items():
            files[key] = upload_canvas_file(canvas, course_id, path)
            print("UPLOADED", key, files[key]["id"], path.name)
    else:
        # Read-only placeholder rows allow complete body generation and SHA checks.
        files = {key: {"id": 900000 + index} for index, key in enumerate(ASSETS, start=1)}
        for key, path in ASSETS.items():
            print("DRY UPLOAD", key, path.name, path.stat().st_size)

    for spec in EXISTING:
        update_existing(canvas, course_id, spec, files, args.apply)

    overview = canvas.get(f"/courses/{course_id}/pages/unit-at-a-glance-video-game-design")
    overview_body = upsert_prefixed_block(overview.get("body") or "", OVERVIEW_MARKER, overview_block(course_id, files))
    print(("APPLY" if args.apply else "DRY"), "UPDATE", overview.get("title"), digest(overview_body)[:10])
    if args.apply:
        canvas.request("PUT", f"/courses/{course_id}/pages/unit-at-a-glance-video-game-design", {"wiki_page[body]": overview_body, "wiki_page[notify_of_update]": "false"})
        canvas.request("PUT", f"/courses/{course_id}/modules/{VIDEO_MODULE_ID}", {"module[name]": "SW3 · Video Game Design + Text Code"})

    guide1_title = "Teacher Guide: Text-Code Bridge Day 1 — Trace, Predict + Repair"
    assignment1_title = "Lesson 3: Text Code — Trace, Predict + Repair"
    guide2_title = "Teacher Guide: Text-Code Bridge Day 2 — Change the Grid with Purpose"
    assignment2_title = "Lesson 4: Text Code — Emergency Supply Grid"
    guide1 = ensure_page(canvas, course_id, guide1_title, bridge_teacher_body(course_id, files, 1, assignment1_title), args.apply)
    assignment1 = ensure_assignment(canvas, course_id, assignment1_title, bridge_student_body(course_id, files, 1), 1, args.apply)
    guide2 = ensure_page(canvas, course_id, guide2_title, bridge_teacher_body(course_id, files, 2, assignment2_title), args.apply)
    assignment2 = ensure_assignment(canvas, course_id, assignment2_title, bridge_student_body(course_id, files, 2), 2, args.apply)
    ensure_rubric(canvas, course_id, assignment2, args.apply)
    quiz = ensure_quiz(canvas, course_id, args.apply)

    ensure_module_item(canvas, course_id, VIDEO_MODULE_ID, "Text-Code Bridge (2 days)", "SubHeader", None, None, args.apply)
    if args.apply:
        ensure_module_item(canvas, course_id, VIDEO_MODULE_ID, guide1_title, "Page", None, guide1["url"], True)
        ensure_module_item(canvas, course_id, VIDEO_MODULE_ID, assignment1_title, "Assignment", assignment1["id"], None, True)
        ensure_module_item(canvas, course_id, VIDEO_MODULE_ID, guide2_title, "Page", None, guide2["url"], True)
        ensure_module_item(canvas, course_id, VIDEO_MODULE_ID, assignment2_title, "Assignment", assignment2["id"], None, True)
        ensure_module_item(canvas, course_id, VIDEO_MODULE_ID, "Checkpoint: Text Code + Nested Loops", "Quiz", quiz["id"], None, True)
    else:
        for title, item_type in ((guide1_title, "Page"), (assignment1_title, "Assignment"), (guide2_title, "Page"), (assignment2_title, "Assignment"), ("Checkpoint: Text Code + Nested Loops", "Quiz")):
            ensure_module_item(canvas, course_id, VIDEO_MODULE_ID, title, item_type, None, None, False)

    ordered_titles = [
        "Unit at a Glance: Video Game Design",
        "Facilitator Guide: Video Game Design Lesson 1 — Skillmap, Sign-in + Save",
        "Lesson 1: Skillmap",
        "Facilitator Guide: Video Game Design Lesson 2 — Remix, Test + Explain",
        "Lesson 2: Remix",
        "Text-Code Bridge (2 days)",
        guide1_title,
        assignment1_title,
        guide2_title,
        assignment2_title,
        "Checkpoint: Text Code + Nested Loops",
    ]
    set_module_order(canvas, course_id, VIDEO_MODULE_ID, ordered_titles, args.apply)
    if args.apply:
        verify(canvas, course_id, files)


if __name__ == "__main__":
    main()
