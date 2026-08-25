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
SCOPE_MARKER = 'data-vils-coding-foundations-scope="2026-08-23"'
SCOPE_PAGE_URL = "program-scope-+-sequence"
SCOPE_BODY_SHA256 = "8f424d78c1a533b2fbf3e3b81269dbc7780df4cb05fb8211a63fffc123875b65"

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
    "day1_highlighted": ROOT / "curriculum-assets/coding-foundations/Emergency_Supply_Grid_Day1_Highlighted_Bug_Route.txt",
    "day2_scaffold": ROOT / "curriculum-assets/coding-foundations/Emergency_Supply_Grid_Day2_Student_Authorship_Scaffold.txt",
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
    ExistingSpec(INTRO_MODULE_ID, "page", "facilitator-guide-code-+-web-day-1-algorithm-+-first-program", "Facilitator Guide: Code + Web Day 1 — Algorithm + First Program", "8fc94f73bb21e425acfddb364add70cdb8bf7cdce38dc0e79cf051e87996fb84", 1, "15–20 minutes inside the current period", "Slides 3–7", "Passport Checkpoint 1: goal, inputs/outputs, three subproblems, first pseudocode draft, and literal partner test.", "Punto de control 1: meta, entradas/salidas, tres subproblemas, primer borrador de pseudocódigo y prueba literal."),
    ExistingSpec(INTRO_MODULE_ID, "assignment", 1183240, "Day 1: Your First Code", "4479d0362d42b4594f0923ae05f63b4d25476ce370fe505162a6d9c714a20ec5", 1, "15–20 minutes", "Slides 3–7", "Complete Passport Checkpoint 1 before the Code.org blocks, then submit one readable Passport screenshot with the existing evidence.", "Completa el Punto de control 1 antes de los bloques de Code.org y entrega una captura legible junto con la evidencia existente."),
    ExistingSpec(INTRO_MODULE_ID, "page", "facilitator-guide-code-+-web-day-2-choice-coding-+-patterns", "Facilitator Guide: Code + Web Day 2 — Choice Coding + Patterns", "495de271db81e828635ddd5d678ec562180304d565618280680892e414cfd8b6", 2, "10–15 minutes inside the current period", "Slides 8–12", "Passport Checkpoint 2: analyze the shared route example for its smallest repeated group, explain the benefit of iteration, and generalize the route with one variable or reusable procedure; then identify one sequence, loop, or event in the selected Hour of Code activity. Do not require variables or data types from an activity that does not expose them.", "Punto de control 2: analiza el ejemplo común de la ruta para encontrar el grupo repetido más pequeño, explica el beneficio de la iteración y generaliza la ruta con una variable o un procedimiento reutilizable; luego identifica una secuencia, un bucle o un evento en la actividad de Hour of Code. No se requieren variables ni tipos de datos si la actividad no los muestra."),
    ExistingSpec(INTRO_MODULE_ID, "assignment", 1183242, "Day 2: Hour of Code", "1bbae9da126641023f7006a82ae52bc5edf19b5a3816d524dd77d5191d37be17", 2, "10–15 minutes", "Slides 8–12", "Complete Passport Checkpoint 2 with the shared route example first. Then transfer the idea by naming one sequence, loop, or event from your chosen Hour of Code activity and explaining its effect.", "Completa primero el Punto de control 2 con el ejemplo común de la ruta. Luego transfiere la idea al nombrar una secuencia, un bucle o un evento de tu actividad de Hour of Code y explicar su efecto."),
    ExistingSpec(INTRO_MODULE_ID, "page", "facilitator-guide-code-+-web-day-3-predict-debug-+-log", "Facilitator Guide: Code + Web Day 3 — Predict, Debug + Log", "1950346e2594a5129585ee83318d97b5e55ddca4f541c290d86edeb1467341ff", 3, "10–15 minutes inside the current period", "Slides 13–17", "Passport Checkpoint 3: three prediction/observation/change/result records, revised pseudocode, and an improvement claim.", "Punto de control 3: tres registros de predicción/observación/cambio/resultado, pseudocódigo revisado y una afirmación de mejora."),
    ExistingSpec(INTRO_MODULE_ID, "assignment", 1183246, "Day 3: Debugging Detective", "f2e048ffe09aee06e80d34c5c2602bbb0c4c4c52b99bb915e81417078d1035fe", 3, "10–15 minutes", "Slides 13–17", "Use Passport Checkpoint 3 as the three-bug log. Revise the matching pseudocode after each successful repair and submit a readable checkpoint screenshot.", "Usa el Punto de control 3 como registro de tres errores. Revisa el pseudocódigo correspondiente después de cada reparación y entrega una captura legible."),
    ExistingSpec(VIDEO_MODULE_ID, "page", "facilitator-guide-video-game-design-lesson-2-remix-test-+-explain", "Facilitator Guide: Video Game Design Lesson 2 — Remix, Test + Explain", "f34268145bd0b206dd5f0681d209d68651eb1ec8c66d41fe65fd75788a99a802", 4, "10–15 minutes before students edit and after the feature test", "Slides 18–22", "Passport Checkpoint 4 — Game Plan: feature goal, WHEN/SHOULD statement, feature pseudocode, first test result, and one evidence-based revision. Score the plan and test within the existing Build and Testing criterion and the submitted checkpoint within Screenshot and Reflection; do not add points.", "Punto de control 4 — Plan del juego: meta de la función, enunciado CUANDO/DEBE, pseudocódigo, primer resultado de prueba y una revisión basada en evidencia. Califica el plan y la prueba dentro del criterio existente Construcción y pruebas, y el punto de control entregado dentro de Captura y reflexión; no agregues puntos."),
    ExistingSpec(VIDEO_MODULE_ID, "assignment", 1183360, "Lesson 2: Remix", "71c31b86768f5d830804faca8500b86fea422a447b872363816df74f627f2c4f", 4, "10–15 minutes", "Slides 18–22", "Plan one required feature in Passport Checkpoint 4 before adding it. After testing, record what happened and one revision. Use a class-safe alias, not your full name, and test with a partner on the same device instead of creating a public share link.", "Planea una función requerida en el Punto de control 4 antes de agregarla. Después de probarla, registra qué pasó y una revisión. Usa un alias seguro de la clase, no tu nombre completo, y prueba con un compañero en el mismo dispositivo sin crear un enlace público."),
    ExistingSpec(RVR_MODULE_ID, "page", "facilitator-guide-rvr-day-1-draw-plan-program-prove", "Facilitator Guide: RVR Day 1 — Draw, Plan, Program, Prove", "873e42bb4597b283af6f7aba86b5132b5ebe5af686b84939393200d96941bc42", 7, "15–20 minutes distributed across plan, first run, and close", "Slides 52–57", "Combined evidence across two artifacts: Passport Checkpoint 7 records the problem, two possible solutions, selected solution, roles, timeline, and pseudocode. The existing mission sheet records the drawing sketch, robot ID, first/final run, revision, and reflection. Do not copy the same response into both tools.", "Evidencia combinada en dos documentos: el Punto de control 7 registra el problema, dos soluciones posibles, la solución elegida, roles, cronograma y pseudocódigo. La hoja de misión existente registra el boceto, ID del robot, primera/última prueba, revisión y reflexión. No copies la misma respuesta en los dos documentos."),
    ExistingSpec(RVR_MODULE_ID, "assignment", 1183265, "Day 1 · Drawing Mission: Plan, Program, Prove", "7d791169b3dd066e62d4a3cfa0a0a8fceb465bee5aec194eb1b08d505b87eadf", 7, "15–20 minutes distributed across the period", "Slides 52–57", "Complete Passport Checkpoint 7 with the team problem, two possible solutions, selection, roles, timeline, and pseudocode. Use the existing mission sheet for the drawing sketch, robot ID, first/final run, revision, and reflection. Submit both without duplicating answers.", "Completa el Punto de control 7 con el problema del equipo, dos soluciones posibles, la selección, roles, cronograma y pseudocódigo. Usa la hoja de misión existente para el boceto, ID del robot, primera/última prueba, revisión y reflexión. Entrega ambos sin duplicar respuestas."),
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
    """Replace/move an existing marked block so the controlling notice is first."""
    found = find_marked_div(body, marker)
    if found:
        body = body[: found[0]] + body[found[1] :]
    return block + (body or "")


def apply_game_privacy_corrections(body: str) -> str:
    """Remove full-name and public-share directions from the retrofitted game task."""
    body = body.replace("[Your Name] Remix", "[Class Alias] Remix")
    body = body.replace("[Tu Nombre] Remix", "[Alias de clase] Remix")
    body = body.replace("with your name plus the word Remix", "with a class-safe alias plus the word Remix")
    body = body.replace("name does not include your name", "name does not include a class-safe alias")
    body = body.replace(
        '• Hit <strong style="color: #ffcf40;">Share</strong> and swap game links with a partner',
        "• Test with a partner on the same device. Do not create a public share link.",
    )
    body = body.replace(
        '• Presiona <strong style="color: #ffcf40;">Share</strong> y cambia juegos con un compañero',
        "• Prueba con un compañero en el mismo dispositivo. No crees un enlace público.",
    )
    body = body.replace(
        '(<strong>en inglés</strong>)',
        "(en inglés o español / in English or Spanish)",
    )
    return body


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


EXISTING_ALIGNMENT = {
    1: {
        "topic": "Decomposition and literal testing before block code",
        "objective": "Students will decompose a route into precise pseudocode, literal-test the plan, and use program evidence to improve the algorithm.",
        "essential": ("§126.19(c)(1)(E)",),
        "supporting": ("§126.19(c)(1)(A)",),
        "status": "Demonstrated: (1)(E). Practiced: (1)(A), because the Code.org route is not by itself a real-world problem.",
        "threshold": "The checkpoint names the goal, inputs/outputs, at least three subproblems, precise pseudocode, the literal-test failure point, and a revision connected to the program result.",
        "budget": "5 minutes model + 8 minutes plan/literal test + current Code.org work + 2-minute close. Do not add a second worksheet.",
        "scoring": "Keep 5 points: 2 progress evidence, 2 complete Passport plan/literal test, 1 evidence-based improvement reflection.",
    },
    2: {
        "topic": "Patterns, iteration, and generalization",
        "objective": "Students will analyze a shared route pattern, explain why iteration helps, generalize the route, and transfer one pattern idea to a chosen coding activity.",
        "essential": ("§126.19(c)(1)(F)",),
        "supporting": ("§126.19(c)(1)(B)", "§126.19(c)(1)(C)"),
        "status": "Demonstrated: (1)(F) through the shared example. Practiced: (1)(B) and (1)(C). Do not claim variable/data-type evidence from an arbitrary Hour of Code activity.",
        "threshold": "The student brackets the smallest repeated group in the common example, explains a loop benefit, writes one generalized pseudocode procedure, and identifies one sequence, loop, or event in the selected activity.",
        "budget": "5 minutes shared route + 5–10 minutes Passport + remaining period in the selected Hour of Code activity.",
        "scoring": "Keep 5 points: 2 completion evidence, 2 shared-example pattern/generalization, 1 transfer explanation.",
    },
    3: {
        "topic": "Controlled debugging and plan revision",
        "objective": "Students will predict program behavior, change one instruction at a time, and revise both executable code and its pseudocode from test evidence.",
        "essential": ("§126.19(c)(1)(E)", "§126.19(c)(2)(C)"),
        "supporting": (),
        "status": "Demonstrated: (1)(E) and (2)(C) when all three cause-and-effect records and the matching pseudocode revision are present.",
        "threshold": "Three records each include a prediction, observed result, one exact change, and result after change; the final claim names what improved and why.",
        "budget": "3 minutes model + current debugging work with the Passport used as the bug log + 3-minute close.",
        "scoring": "Keep 5 points: 1 progress evidence, 3 complete controlled-test records, 1 pseudocode revision and improvement claim.",
    },
    4: {
        "topic": "Game-feature planning, testing, and revision",
        "objective": "Students will plan one purposeful feature in pseudocode, implement it in a working remix, test it, and revise from the result.",
        "essential": ("§126.19(c)(2)(C)", "§126.19(c)(3)(B)"),
        "supporting": ("§126.19(c)(1)(E)",),
        "status": "Demonstrated: (2)(C) and (3)(B). Practiced: (1)(E). A plan without the recorded test result is incomplete.",
        "threshold": "Checkpoint 4 includes a feature goal, WHEN/SHOULD statement, pseudocode, observed test result, and one revision; the final game contains the tested feature.",
        "budget": "5–8 minutes before editing + 5 minutes after the first feature test; preserve the existing full-period build.",
        "scoring": "Keep 100 points: score the plan/test within Build and Testing and the submitted checkpoint within Screenshot and Reflection. No additional points or public share link.",
    },
    7: {
        "topic": "Collaborative robot-algorithm planning and revision",
        "objective": "Students will compare possible robot-drawing solutions, document a team plan and timeline in pseudocode, then revise the algorithm from a literal run.",
        "essential": ("§126.19(c)(1)(D)", "§126.19(c)(1)(E)", "§126.19(c)(2)(C)"),
        "supporting": (),
        "status": "Demonstrated only through the combined evidence: Passport 7 supplies the collaborative problem/solutions/selection/roles/timeline/pseudocode, and the mission sheet supplies sketch/ID/first-final runs/revision/reflection.",
        "threshold": "The Passport proves the collaborative plan; the mission sheet proves the drawing sketch, robot ID, first/final run, revision, and reflection. Duplicate responses do not count as two pieces of evidence.",
        "budget": "8 minutes team plan before programming + current build/run + 7–12 minutes revision and transfer close.",
        "scoring": "Keep 5 points: 1 team plan/pseudocode, 1 mission sketch/robot ID, 1 first/final run evidence, 1 revision, 1 explanation/transfer.",
    },
}


EXISTING_STUDENT_LANGUAGE = {
    1: {
        "topic_en": "Plan precise directions before block code",
        "topic_es": "Planear instrucciones precisas antes del código por bloques",
        "can_en": "I can break a route into smaller jobs, write precise pseudocode, and improve it after a literal test.",
        "can_es": "Puedo dividir una ruta en trabajos pequeños, escribir pseudocódigo preciso y mejorarlo después de una prueba literal.",
        "now_en": "Complete Passport 1 before moving the Code.org blocks.",
        "now_es": "Completa el Pasaporte 1 antes de mover los bloques de Code.org.",
        "next_en": "Have a partner follow only the written plan; mark and revise the first unclear line, then build and test it in Code.org.",
        "next_es": "Pide a un compañero que siga solamente el plan escrito; marca y revisa la primera línea poco clara, luego constrúyela y pruébala en Code.org.",
        "done_en": "Submit the progress screenshot, Passport 1, and the improvement reflection.",
        "done_es": "Entrega la captura de avance, el Pasaporte 1 y la reflexión sobre la mejora.",
        "score_en": "5 points: progress 2; plan/literal test 2; improvement reflection 1.",
        "score_es": "5 puntos: avance 2; plan/prueba literal 2; reflexión de mejora 1.",
    },
    2: {
        "topic_en": "Find and reuse coding patterns",
        "topic_es": "Encontrar y reutilizar patrones de programación",
        "can_en": "I can identify a repeated group, explain why a loop helps, and generalize the idea.",
        "can_es": "Puedo identificar un grupo repetido, explicar por qué ayuda un bucle y generalizar la idea.",
        "now_en": "Use the shared route example for Passport 2. Do not search your Hour of Code activity for variables it does not show.",
        "now_es": "Usa el ejemplo común de la ruta para el Pasaporte 2. No busques variables que tu actividad de Hour of Code no muestra.",
        "next_en": "Choose an Hour of Code activity and name one sequence, loop, or event plus what it controls.",
        "next_es": "Escoge una actividad de Hour of Code y nombra una secuencia, un bucle o un evento junto con lo que controla.",
        "done_en": "Submit the completion evidence, Passport 2, and the transfer explanation.",
        "done_es": "Entrega la evidencia de finalización, el Pasaporte 2 y la explicación de transferencia.",
        "score_en": "5 points: completion 2; shared pattern/generalization 2; transfer explanation 1.",
        "score_es": "5 puntos: finalización 2; patrón/generalización 2; explicación de transferencia 1.",
    },
    3: {
        "topic_en": "Use controlled tests to repair code",
        "topic_es": "Usar pruebas controladas para reparar código",
        "can_en": "I can predict, change one thing, observe the result, and revise the matching pseudocode.",
        "can_es": "Puedo predecir, cambiar una sola cosa, observar el resultado y revisar el pseudocódigo correspondiente.",
        "now_en": "Use Passport 3 as the three-bug log; predict before every run.",
        "now_es": "Usa el Pasaporte 3 como registro de tres errores; predice antes de cada ejecución.",
        "next_en": "After each repair, copy the matching pseudocode line and revise it.",
        "next_es": "Después de cada reparación, copia la línea correspondiente del pseudocódigo y revísala.",
        "done_en": "Submit the progress screenshot, three complete test records, and improvement claim.",
        "done_es": "Entrega la captura de avance, tres registros completos de prueba y la afirmación de mejora.",
        "score_en": "5 points: progress 1; three test records 3; revision/claim 1.",
        "score_es": "5 puntos: avance 1; tres registros 3; revisión/afirmación 1.",
    },
    4: {
        "topic_en": "Plan, test, and improve one game feature",
        "topic_es": "Planear, probar y mejorar una función del juego",
        "can_en": "I can turn a WHEN/SHOULD plan into a working feature and revise it from a test result.",
        "can_es": "Puedo convertir un plan CUANDO/DEBE en una función que funcione y revisarla a partir de una prueba.",
        "now_en": "Use Passport 4 to plan one required feature before editing. Name the project with a class-safe alias, not your full name.",
        "now_es": "Usa el Pasaporte 4 para planear una función requerida antes de editar. Nombra el proyecto con un alias seguro de la clase, no con tu nombre completo.",
        "next_en": "Build and test the feature, record what happened, and revise one exact block or value. Test with a partner on the same device; do not create a public share link.",
        "next_es": "Construye y prueba la función, registra lo que pasó y revisa un bloque o valor exacto. Prueba con un compañero en el mismo dispositivo; no crees un enlace público.",
        "done_en": "Submit the existing remix evidence plus readable Passport 4 evidence showing the test and revision.",
        "done_es": "Entrega la evidencia existente del remix y el Pasaporte 4 legible con la prueba y la revisión.",
        "score_en": "The assignment stays 100 points; Passport planning/testing is scored inside the existing Build and Testing and Screenshot and Reflection criteria.",
        "score_es": "La tarea sigue valiendo 100 puntos; el plan y la prueba del Pasaporte se califican dentro de los criterios existentes Construcción y pruebas y Captura y reflexión.",
    },
    7: {
        "topic_en": "Plan and revise a robot drawing as a team",
        "topic_es": "Planear y revisar un dibujo del robot en equipo",
        "can_en": "I can compare solutions, document a team algorithm and timeline, and revise it after the robot follows it literally.",
        "can_es": "Puedo comparar soluciones, documentar un algoritmo y cronograma del equipo y revisarlo después de que el robot lo siga literalmente.",
        "now_en": "Use Passport 7 for the problem, two possible solutions, selected plan, roles, timeline, and pseudocode.",
        "now_es": "Usa el Pasaporte 7 para el problema, dos soluciones posibles, el plan elegido, los roles, el cronograma y el pseudocódigo.",
        "next_en": "Use the mission sheet for the drawing sketch, robot ID, first/final run evidence, revision, and reflection. Keep Passport 7 as the team planning record.",
        "next_es": "Usa la hoja de misión para el boceto, ID del robot, evidencia de la primera y última prueba, revisión y reflexión. Conserva el Pasaporte 7 como registro de planificación del equipo.",
        "done_en": "Submit both files without copying the same response twice, then complete the transfer reflection.",
        "done_es": "Entrega ambos archivos sin copiar la misma respuesta dos veces y completa la reflexión de transferencia.",
        "score_en": "5 points: team plan 1; mission sketch/ID 1; runs 1; revision 1; explanation/transfer 1.",
        "score_es": "5 puntos: plan del equipo 1; boceto/ID 1; pruebas 1; revisión 1; explicación/transferencia 1.",
    },
}


def existing_teacher_block(spec: ExistingSpec, course_id: int, files: dict[str, dict]) -> str:
    alignment = EXISTING_ALIGNMENT[spec.checkpoint]
    supporting = f'<p style="margin:8px 0 4px;"><strong>Supporting standards:</strong></p><ul>{exact_teks(alignment["supporting"])}</ul>' if alignment["supporting"] else ""
    return f'''<div {MARKER} data-vils-checkpoint="{spec.checkpoint}" style="margin:18px 0;padding:16px 18px;border:3px solid #00B8C8;border-radius:14px;background:#F4FBFC;color:#172033;">
<p style="margin:0 0 5px;color:#0E7C7B;"><strong>CODING FOUNDATIONS RETROFIT · PASSPORT CHECKPOINT {spec.checkpoint}</strong></p>
<h2 style="margin:0 0 8px;font-size:21px;color:#172033;">Alignment and scoring correction for this added evidence</h2>
<p style="margin:0 0 8px;"><strong>This block controls the retrofit evidence and supersedes any conflicting Coding Foundations wording below.</strong></p>
<p style="margin:0 0 6px;"><strong>Topic:</strong> {html.escape(alignment["topic"])}</p>
<p style="margin:0 0 8px;"><strong>Objective:</strong> {html.escape(alignment["objective"])}</p>
<p style="margin:8px 0 4px;"><strong>Essential standards:</strong></p><ul>{exact_teks(alignment["essential"])}</ul>{supporting}
<p style="margin:0 0 8px;"><strong>Evidence status:</strong> {html.escape(alignment["status"])}</p>
<p style="margin:0 0 8px;"><strong>Required evidence:</strong> {html.escape(spec.evidence_en)}</p>
<p style="margin:0 0 8px;"><strong>Meets the threshold when:</strong> {html.escape(alignment["threshold"])}</p>
<p style="margin:0 0 8px;"><strong>Period budget:</strong> {html.escape(alignment["budget"])}<br><strong>Point-preserving scoring:</strong> {html.escape(alignment["scoring"])}</p>
<p style="margin:0 0 8px;"><strong>Projectable support:</strong> {google_copy("presentation", DRIVE_DECK, f"Editable retrofit deck, {spec.slide_range}")} · {canvas_file_anchor(course_id, files["teacher_deck"], "PowerPoint fallback")}</p>
{passport_links(course_id, files)}
<p style="margin:10px 0 0;"><strong>Teacher move:</strong> Use the Passport as the named planning/test evidence inside the current lesson and current point total. Do not create a duplicate worksheet or count completion alone as mastery.</p>
</div>'''


def existing_student_block(spec: ExistingSpec, course_id: int, files: dict[str, dict]) -> str:
    language = EXISTING_STUDENT_LANGUAGE[spec.checkpoint]
    return f'''<div {MARKER} data-vils-checkpoint="{spec.checkpoint}" style="margin:18px 0;padding:16px 18px;border:3px solid #00B8C8;border-radius:14px;background:#F4FBFC;color:#172033;">
<p style="margin:0 0 5px;color:#0E7C7B;"><strong>PASSPORT {spec.checkpoint} / PASAPORTE {spec.checkpoint}</strong></p>
<h2 style="margin:0 0 8px;font-size:21px;color:#172033;">{html.escape(language["topic_en"])} / {html.escape(language["topic_es"])}</h2>
<p><strong>I can:</strong> {html.escape(language["can_en"])}</p><p><strong>Puedo:</strong> {html.escape(language["can_es"])}</p>
<div style="margin:12px 0;padding:12px;border-left:6px solid #274C77;background:#fff;"><h3 style="margin:0 0 6px;">Show Your Learning / Demuestra lo aprendido</h3><p style="margin:0 0 6px;">{html.escape(spec.evidence_en)}</p><p style="margin:0;">{html.escape(spec.evidence_es)}</p></div>
<ol style="padding-left:24px;"><li><strong>Now / Ahora:</strong> {html.escape(language["now_en"])}<br>{html.escape(language["now_es"])}</li><li><strong>Next / Después:</strong> {html.escape(language["next_en"])}<br>{html.escape(language["next_es"])}</li><li><strong>Done / Al terminar:</strong> {html.escape(language["done_en"])}<br>{html.escape(language["done_es"])}</li></ol>
{passport_links(course_id, files)}
<p style="margin:10px 0 0;"><strong>Points / Puntos:</strong> {html.escape(language["score_en"])}<br>{html.escape(language["score_es"])}</p>
<p style="margin:8px 0 0;"><strong>Privacy / Privacidad:</strong> Crop names, email addresses, and profile details from screenshots. / Recorta nombres, correos electrónicos y datos del perfil de las capturas.</p>
</div>'''


def overview_block(course_id: int, files: dict[str, dict]) -> str:
    return f'''<div {OVERVIEW_MARKER} style="margin:0 0 18px;padding:18px;border:3px solid #00B8C8;border-radius:14px;background:#F4FBFC;color:#172033;">
<p style="margin:0 0 5px;color:#0E7C7B;"><strong>2027 REQUIRED TECH APPS BRIDGE</strong></p>
<h2 style="margin:0 0 8px;font-size:22px;color:#172033;">Video Game Design now runs four class periods</h2>
<ol style="margin:0 0 10px;padding-left:22px;"><li>Lesson 1: Skillmap</li><li>Lesson 2: Remix + Passport 4 Game Plan</li><li>Lesson 3: Passport 5 Trace, Predict + Repair Text Code</li><li>Lesson 4: Passport 6 Create + Improve Emergency Supply Grid</li></ol>
<p style="margin:0 0 8px;"><strong>Evidence boundary:</strong> Day 1 practices reading supplied variables and nested loops and demonstrates code improvement. Day 2 independently demonstrates constructed string/number/Boolean variables, operations, completed text-code nested loops for row/column subproblems, and a required evidence-based revision when every rubric threshold is met.</p>
<p style="margin:0;">{google_copy("presentation", DRIVE_DECK, "Editable Coding Foundations teacher deck")} · {canvas_file_anchor(course_id, files["teacher_deck"], "PowerPoint fallback")}</p>
</div>'''


def bridge_resources(course_id: int, files: dict[str, dict], day: int) -> str:
    source_key = "day1_highlighted" if day == 1 else "day2_scaffold"
    source_label = "Day 1 highlighted bug route" if day == 1 else "Day 2 student-authorship scaffold"
    return (
        f'<p style="margin:0 0 8px;"><a href="https://arcade.makecode.com/" target="_blank"><strong>Open MakeCode Arcade</strong></a> · '
        f'{canvas_file_anchor(course_id, files[source_key], source_label)}</p>'
        + passport_links(course_id, files)
    )


def bridge_teacher_resources(course_id: int, files: dict[str, dict], day: int) -> str:
    slides = "23–37" if day == 1 else "38–51"
    source_key = "day1_highlighted" if day == 1 else "day2_scaffold"
    source_label = "Day 1 highlighted bug route" if day == 1 else "Day 2 student-authorship scaffold"
    references = (
        f'{canvas_file_anchor(course_id, files["screenshot_code"], "Teacher-only code reference")} · '
        f'{canvas_file_anchor(course_id, files["screenshot_result"], "Teacher-only result reference")}'
    )
    return (
        f'<p>{google_copy("presentation", DRIVE_DECK, f"Editable teacher deck, slides {slides}")} · '
        f'{canvas_file_anchor(course_id, files["teacher_deck"], "PowerPoint fallback")}</p>'
        f'<p><a href="https://arcade.makecode.com/" target="_blank"><strong>MakeCode Arcade</strong></a> · '
        f'{canvas_file_anchor(course_id, files[source_key], source_label)} · '
        f'{canvas_file_anchor(course_id, files["exemplar"], "Teacher exemplar — alternate finished solution; do not use as the starter")}</p>'
        f'<p><strong>Reveal only after student diagnosis/work:</strong> {references}</p>'
        + passport_links(course_id, files)
    )


def bridge_student_body(course_id: int, files: dict[str, dict], day: int) -> str:
    if day == 1:
        title = "Lesson 3: Text Code — Trace, Predict + Repair"
        topic_en = "Trace and repair text code"
        topic_es = "Seguir y reparar código de texto"
        can_en = "I can trace nested loops, predict the full output, and use evidence to repair one boundary error."
        can_es = "Puedo seguir bucles anidados, predecir el resultado completo y usar evidencia para reparar un error de límite."
        show_en = "Passport 5 trace/repair record, prediction made before Run, before/after simulator evidence, corrected JavaScript, and a row/column explanation."
        show_es = "Registro de seguimiento/reparación del Pasaporte 5, predicción antes de Ejecutar, evidencia del simulador antes/después, JavaScript corregido y explicación de filas/columnas."
        now_en = [
            "Open a new MakeCode Arcade project, select JavaScript, and paste the Bug Challenge code.",
            "Before Run, use Passport 5 to label the supplied string, number, and Boolean variables and the operations you notice.",
            "Trace one complete row. Record how many placements happen in one inner-loop pass and predict the full 3 × 4 total.",
        ]
        now_es = [
            "Abre un proyecto nuevo de MakeCode Arcade, selecciona JavaScript y pega el código Bug Challenge.",
            "Antes de Ejecutar, usa el Pasaporte 5 para identificar las variables de texto, número y Booleano proporcionadas y las operaciones que observas.",
            "Sigue una fila completa. Registra cuántas colocaciones ocurren en una pasada del bucle interior y predice el total de 3 × 4.",
        ]
        next_en = [
            "Run once and capture the unexpected grid and score before changing code.",
            "Find the loop condition that does not match its counter. Change only that boundary, run again, and capture the repaired result.",
            "Explain how the outer loop handles rows and the inner loop handles columns. The code you identify helps you trace; the one-line repair you make is what you submit for credit.",
        ]
        next_es = [
            "Ejecuta una vez y captura la cuadrícula y puntuación inesperadas antes de cambiar el código.",
            "Encuentra la condición del bucle que no coincide con su contador. Cambia solamente ese límite, ejecuta otra vez y captura el resultado reparado.",
            "Explica cómo el bucle exterior controla las filas y el interior las columnas. El código que identificas te ayuda a seguir el programa; la reparación de una línea que haces es lo que entregas para recibir crédito.",
        ]
        done_en = "Submit Passport 5, the before/after evidence, readable corrected code, and the explanation."
        done_es = "Entrega el Pasaporte 5, la evidencia antes/después, el código corregido legible y la explicación."
        scoring_en = "25 points: trace/types/operations 5; prediction 5; before/after evidence 5; exact repair 5; explanation 5."
        scoring_es = "25 puntos: seguimiento/tipos/operaciones 5; predicción 5; evidencia antes/después 5; reparación exacta 5; explicación 5."
    else:
        title = "Lesson 4: Text Code — Emergency Supply Grid"
        topic_en = "Create and improve an emergency supply-layout program"
        topic_es = "Crear y mejorar un programa de distribución de suministros de emergencia"
        can_en = "I can create meaningful typed variables and nested loops, test the layout against a real screen constraint, and improve the program from evidence."
        can_es = "Puedo crear variables con tipos significativos y bucles anidados, probar la distribución con una restricción real de pantalla y mejorar el programa con evidencia."
        show_en = "Passport 6 problem/constraints and pseudocode; the string, number, and Boolean variables and operations you write; your completed outer and inner loops; prediction; first run; required revision; final code/simulator result; and explanation."
        show_es = "Problema/restricciones y pseudocódigo del Pasaporte 6; variables de texto, número y Booleano creadas por ti con operaciones; bucles exterior e interior completados; predicción; primera prueba; revisión requerida; evidencia final del código/simulador y explicación."
        now_en = [
            "Choose Mission A (4 rows × 5 columns) or Mission B (2 rows × 6 columns). Every supply must remain visible in the 160 × 120 simulator and the priority state must create a visible cue.",
            "In Passport 6, record the shelter/distribution problem, screen constraints, row and column subproblems, and pseudocode before coding.",
            "Open the Day 2 scaffold. Complete every TODO in JavaScript: construct meaningful string, number, and Boolean variables; use arithmetic, comparison, and Boolean operations; and complete both nested loops.",
        ]
        now_es = [
            "Escoge Misión A (4 filas × 5 columnas) o Misión B (2 filas × 6 columnas). Cada suministro debe permanecer visible en el simulador de 160 × 120 y el estado de prioridad debe crear una señal visible.",
            "En el Pasaporte 6, registra el problema del refugio/distribución, las restricciones de pantalla, los subproblemas de filas y columnas y el pseudocódigo antes de programar.",
            "Abre el andamiaje del Día 2. Completa cada PENDIENTE en JavaScript: crea variables significativas de texto, número y Booleano; usa operaciones aritméticas, de comparación y Booleanas; y completa los dos bucles anidados.",
        ]
        next_en = [
            "Predict the total and one x/y position. Run the first draft and capture the result.",
            "Make one required controlled revision to improve visibility, spacing, or the priority cue. Run again and record the observed improvement.",
            "Explain how your outer loop, inner loop, variables, and operations solve the two subproblems. The sprite/API setup is provided; submit the variables, operations, and two complete loops you write yourself for credit.",
        ]
        next_es = [
            "Predice el total y una posición x/y. Ejecuta el primer borrador y captura el resultado.",
            "Haz una revisión controlada obligatoria para mejorar la visibilidad, el espacio o la señal de prioridad. Ejecuta otra vez y registra la mejora observada.",
            "Explica cómo tus bucles exterior e interior, variables y operaciones resuelven los dos subproblemas. La configuración de sprites/API está incluida; entrega las variables, operaciones y los dos bucles completos que escribas para recibir crédito.",
        ]
        done_en = "Submit Passport 6, readable final JavaScript, first/final simulator evidence, the exact revision, and the explanation."
        done_es = "Entrega el Pasaporte 6, el JavaScript final legible, evidencia de la primera/última prueba, la revisión exacta y la explicación."
        scoring_en = "100 points with the attached rubric. Meeting every required criterion earns full credit; optional extension is not required."
        scoring_es = "100 puntos con la rúbrica adjunta. Cumplir cada criterio requerido obtiene la calificación completa; la extensión opcional no es necesaria."
    now_en_html = "".join(f"<li>{html.escape(value)}</li>" for value in now_en)
    now_es_html = "".join(f"<li>{html.escape(value)}</li>" for value in now_es)
    next_en_html = "".join(f"<li>{html.escape(value)}</li>" for value in next_en)
    next_es_html = "".join(f"<li>{html.escape(value)}</li>" for value in next_es)
    return f'''<div {MARKER} data-vils-text-code-day="{day}" style="max-width:980px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:#172033;font-size:16px;line-height:1.5;">
<div style="background:#0B1426;border:3px solid #00B8C8;border-radius:16px;padding:20px;color:#fff;"><p style="margin:0;color:#80DEEA;"><strong>TEXT CODE · DAY {day} / CÓDIGO DE TEXTO · DÍA {day}</strong></p><h2 style="margin:6px 0;color:#fff;font-size:27px;">{html.escape(title)}</h2></div>
<div style="margin:16px 0;padding:16px 18px;border:2px solid #274C77;border-radius:12px;background:#F4F8FC;"><p><strong>Topic / Tema:</strong> {html.escape(topic_en)} / {html.escape(topic_es)}</p><p><strong>I can:</strong> {html.escape(can_en)}</p><p><strong>Puedo:</strong> {html.escape(can_es)}</p><h2>Show Your Learning / Demuestra lo aprendido</h2><p>{html.escape(show_en)}</p><p>{html.escape(show_es)}</p></div>
<div style="margin:16px 0;padding:16px;border-left:7px solid #00B8C8;background:#F4FBFC;"><h2 style="margin-top:0;">Tools / Herramientas</h2>{bridge_resources(course_id, files, day)}</div>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:14px;margin:16px 0;"><div style="padding:16px;border:2px solid #54B68A;border-radius:12px;"><h2 style="margin-top:0;">Now / Ahora</h2><h3>English</h3><ol>{now_en_html}</ol><h3>Español</h3><ol>{now_es_html}</ol></div><div style="padding:16px;border:2px solid #A970FF;border-radius:12px;"><h2 style="margin-top:0;">Next / Después</h2><h3>English</h3><ol>{next_en_html}</ol><h3>Español</h3><ol>{next_es_html}</ol></div></div>
<div style="margin:16px 0;padding:16px;border:2px solid #FFD166;border-radius:12px;background:#FFFBE8;"><h2 style="margin-top:0;">Done / Al terminar</h2><p>{html.escape(done_en)}</p><p>{html.escape(done_es)}</p><p><strong>Points / Puntos:</strong> {html.escape(scoring_en)}<br>{html.escape(scoring_es)}</p><p style="margin-bottom:0;"><strong>Privacy / Privacidad:</strong> Use a class-safe project name. Crop names, email addresses, and profile details from screenshots. Do not submit a public share link. / Usa un nombre seguro para el proyecto. Recorta nombres, correos y datos del perfil. No entregues un enlace público.</p></div>
</div>'''


def bridge_teacher_body(course_id: int, files: dict[str, dict], day: int, student_title: str) -> str:
    if day == 1:
        topic = "Tracing and repairing a text-based nested-loop program"
        objective = "Students will trace supplied text code, predict its complete output, diagnose one nested-loop boundary error, and modify and implement the code to produce an improved program."
        essential = ("§126.19(c)(2)(C)",)
        supporting = ("§126.19(c)(2)(A)", "§126.19(c)(2)(B)")
        status = "Demonstrated: (2)(C). Practiced: (2)(A) and (2)(B); identifying supplied variables and loops is not independent construction or creation."
        evidence = "Passport 5 trace/repair record, prediction before Run, unexpected-result screenshot, corrected JavaScript, repaired-result screenshot, and row/column explanation."
        threshold = "Meets when the prediction is recorded before Run, the student identifies the mismatched counter/boundary, changes only that condition, reproduces the corrected total, and explains both loop subproblems."
        prerequisite = "Completed block-code Game Remix planning/test evidence; can locate the JavaScript view and distinguish a variable from a loop."
        timeline = [
            ("4 min · Launch", "Show only the mission and intended 3 × 4 requirement. Ask what evidence would prove the program is wrong. Do not display the corrected line or result."),
            ("6 min · Model", "Trace a neutral two-row mini-loop unrelated to the challenge. Model per-row count versus full-program total."),
            ("7 min · Guided practice", "Trace row 0 together in Passport 5; identify supplied types and operations without changing code."),
            ("3 min · CFU", "Ask: How many placements in one inner-loop pass? How many across all outer-loop passes? Expected: 4 and 12."),
            ("20 min · Independent work", "Students paste, predict, run, capture the unexpected result, diagnose, change one boundary, rerun, and explain."),
            ("5 min · Submit", "Check all five 5-point elements before accepting the submission."),
            ("5 min · Close", "Ask one student to connect the exact condition change to the new total. Reveal teacher references only now."),
        ]
        expected = ["missionName is string; rows/columns/suppliesPlaced are numbers; priorityMode is Boolean.", "One inner-loop pass places 4 supplies; all three outer iterations place 12.", "The bug uses column < rows, producing 3 columns per row and 9 total.", "The repair uses column < columns, producing 4 columns per row and 12 total.", "Outer loop = row subproblem; inner loop = complete the columns within each row."]
        misconceptions = ["Answering 4 when asked for the full program total.", "Changing rows or columns instead of the mismatched boundary.", "Claiming supplied variable declarations as independently authored (2)(A) evidence.", "Backfilling the prediction after seeing the result."]
        support = "Read the code aloud by line number; cover the simulator until the prediction is recorded; after the first attempt, point to the two loop headers without naming the replacement. Allow oral explanation recorded by the teacher, but retain the same code and test evidence."
        recovery = "Create a new project, select JavaScript, and paste the Bug Challenge text again. Check brackets and the two loop headers before replacing any additional code."
        absence = "Use the student page, Bug Challenge file, Passport 5, and the same five-part scoring checklist. The student submits both results and the explanation; no live partner is required."
    else:
        topic = "Creating and improving a constrained emergency supply-layout program"
        objective = "Students will use a software design process to construct meaningful variables across string, number, and Boolean types, perform operations on their values, complete a text-based nested-loop program for row and column subproblems, and improve it from test evidence."
        essential = ("§126.19(c)(2)(A)", "§126.19(c)(2)(B)", "§126.19(c)(2)(C)")
        supporting = ("§126.19(c)(1)(A)", "§126.19(c)(1)(E)")
        status = "Demonstrated: (2)(A), (2)(B), and (2)(C) only when the authored TODOs, design record, first run, required revision, and explanation all meet the threshold. Practiced: (1)(A) and (1)(E)."
        evidence = "Passport 6 problem/constraints and pseudocode, student-authored typed variables and operations, student-completed nested loops, prediction, first/final evidence, exact revision, final JavaScript, and explanation."
        threshold = "Meets when the student authors/meaningfully completes string, number, and Boolean variables plus operations; completes both loop structures; keeps the selected mission visible within 160 × 120; records a first run and required improvement; and explains the distinct row/column subproblems. Supplied sprite/API code alone earns no authorship credit."
        prerequisite = "Completed Passport 5 and Day 1 repair; can trace a loop counter and interpret string, number, and Boolean values."
        timeline = [
            ("5 min · Launch", "Present the shelter/distribution need, 160 × 120 screen constraint, and Mission A/B. Ask what could make a grid unusable."),
            ("8 min · Model", "Using a separate two-row example, model one typed declaration and one coordinate calculation. Do not complete the assignment loops."),
            ("8 min · Guided practice", "Complete the Passport 6 problem, constraints, row/column subproblems, and pseudocode. Confirm the selected mission total."),
            ("4 min · CFU", "Students identify which TODO proves string, number, Boolean, arithmetic, comparison, Boolean logic, outer loop, and inner loop."),
            ("20 min · Independent work", "Students complete all scaffold TODOs, run a first draft, make one required controlled improvement, and capture final evidence."),
            ("5 min · Submit", "Use the four rubric criteria; Meets is full credit and optional extension is not required."),
            ("5 min · Close", "Students explain one authored element and how test evidence justified the revision."),
        ]
        expected = ["Mission A total: 20. Mission B total: 12.", "Variables include meaningful string, number, and Boolean declarations authored/completed by the student.", "Operations include coordinate arithmetic, suppliesPlaced increment, expected-total multiplication/comparison, and a Boolean decision.", "The outer loop advances rows; the inner loop completes columns in each row.", "A valid revision improves visible spacing, placement, or the priority cue and is supported by before/after evidence."]
        misconceptions = ["Changing values in a finished exemplar and calling that variable construction.", "Leaving supplied loops unchanged and claiming independent nested-loop creation.", "Treating optional extension as required for full credit.", "Submitting only the final screenshot without the first run, exact revision, or explanation."]
        support = "Use the scaffold that supplies MakeCode APIs and sprite art but leaves typed declarations, operations, and both loop structures as student TODOs. Use the Passport 6 row/column trace and bilingual sentence stems. Allow oral explanation recorded by the teacher without reducing the authored code requirement."
        recovery = "Paste a fresh Day 2 scaffold into a new JavaScript project. Restore only completed TODOs from the last readable screenshot/text entry; do not replace the assignment with the exemplar."
        absence = "Use the student page, Day 2 scaffold, Passport 6, and rubric. The student may choose either tested mission and submit code through upload or text entry; no public URL or account is required."
    timeline_html = "".join(f"<li style=\"margin:0 0 8px;\"><strong>{html.escape(label)}:</strong> {html.escape(move)}</li>" for label, move in timeline)
    expected_html = "".join(f"<li>{html.escape(value)}</li>" for value in expected)
    misconceptions_html = "".join(f"<li>{html.escape(value)}</li>" for value in misconceptions)
    return f'''<div {MARKER} data-vils-text-code-guide="{day}" style="max-width:980px;margin:0 auto;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif;color:#172033;font-size:16px;line-height:1.5;">
<div style="background:#0B1426;border:3px solid #00B8C8;border-radius:16px;padding:20px;color:#fff;"><p style="margin:0;color:#80DEEA;"><strong>TEACHER ONLY · TEXT-CODE BRIDGE DAY {day}</strong></p><h2 style="margin:6px 0;color:#fff;font-size:27px;">{html.escape(student_title)}</h2><p style="margin:0;">One class period · keep the student page as the independent and absence route.</p></div>
<div data-vils-daily-learning-contract="2026-08-21-semantic-audit-v1" style="margin:16px 0;padding:16px 18px;border:2px solid #274C77;border-radius:12px;background:#F4F8FC;"><h2 style="margin-top:0;">Daily Learning Contract</h2><p><strong>Topic:</strong> {html.escape(topic)}</p><p><strong>Objective:</strong> {html.escape(objective)}</p><p><strong>Demonstration of learning:</strong> {html.escape(evidence)}</p><p><strong>Essential TEKS:</strong></p><ul>{exact_teks(essential)}</ul><p><strong>Supporting TEKS:</strong></p><ul>{exact_teks(supporting)}</ul></div>
<div style="margin:16px 0;padding:16px;border:2px solid #A970FF;border-radius:12px;"><p><strong>Meets threshold:</strong> {html.escape(threshold)}</p><p style="margin-bottom:0;"><strong>Evidence status:</strong> {html.escape(status)}</p></div>
<div style="margin:16px 0;padding:16px;border-left:7px solid #00B8C8;background:#F4FBFC;"><h2 style="margin-top:0;">Before class</h2><p><strong>Prerequisite:</strong> {html.escape(prerequisite)}</p>{bridge_teacher_resources(course_id, files, day)}<p><strong>Student route:</strong> {html.escape(student_title)}</p></div>
<div style="margin:16px 0;padding:16px;border:2px solid #54B68A;border-radius:12px;"><h2 style="margin-top:0;">Timed lesson flow</h2><ol>{timeline_html}</ol></div>
<div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(300px,1fr));gap:14px;margin:16px 0;"><div style="padding:16px;border:2px solid #274C77;border-radius:12px;"><h2 style="margin-top:0;">Expected answers</h2><ul>{expected_html}</ul></div><div style="padding:16px;border:2px solid #A970FF;border-radius:12px;"><h2 style="margin-top:0;">Likely misconceptions</h2><ul>{misconceptions_html}</ul></div></div>
<div style="margin:16px 0;padding:16px;border:2px solid #FFD166;border-radius:12px;background:#FFFBE8;"><h2 style="margin-top:0;">Scaffolds, recovery, and absence</h2><p><strong>Scaffolds:</strong> {html.escape(support)}</p><p><strong>Recovery:</strong> {html.escape(recovery)}</p><p><strong>Absence route:</strong> {html.escape(absence)}</p></div>
</div>'''


def quiz_description() -> str:
    return f'''<div {MARKER} style="max-width:900px;margin:0 auto;font-size:16px;line-height:1.5;"><div style="background:#0B1426;border:3px solid #00B8C8;border-radius:14px;padding:18px;color:#fff;"><h2 style="margin:0;color:#fff;">Text Code Knowledge Check / Comprobación de código de texto</h2><p style="margin:6px 0 0;">8 questions / preguntas · unlimited attempts / intentos ilimitados · highest score / puntuación más alta</p></div><p><strong>Topic / Tema:</strong> Variables, operations, and nested-loop reasoning / Variables, operaciones y razonamiento con bucles anidados</p><p><strong>I can / Puedo:</strong> I can use feedback to identify the exact idea or line I need to revisit. / Puedo usar la retroalimentación para identificar la idea o línea exacta que necesito revisar.</p><p><strong>Show Your Learning / Demuestra lo aprendido:</strong> Answer all eight questions, read the feedback, return to your Passport or code, and retry. / Contesta las ocho preguntas, lee la retroalimentación, vuelve a tu Pasaporte o código e intenta otra vez.</p><p><strong>Now / Ahora:</strong> Keep your Passport and final code open. <strong>Next / Después:</strong> Use feedback after each attempt. <strong>Done / Al terminar:</strong> Submit your highest attempt.</p><p><strong>This is a knowledge check, not the proof that you created or improved the program. / Esta es una comprobación de conocimientos, no la prueba de que creaste o mejoraste el programa.</strong></p></div>'''


QUIZ_QUESTIONS = (
    ("Q1 Construct a string variable", "Which line constructs a meaningful string variable? / ¿Qué línea crea una variable de texto significativa?", ('let missionName: string = "Shelter A"', "let rows: number = 4", "let priorityMode: boolean = true", "suppliesPlaced += 1"), 0, "A string variable stores text and has a meaningful name. / Una variable de texto guarda texto y tiene un nombre significativo.", "Review the type after the colon and the quoted starting value. / Revisa el tipo después de los dos puntos y el valor inicial entre comillas."),
    ("Q2 Construct a Boolean variable", "Which line constructs a Boolean variable? / ¿Qué línea crea una variable Booleana?", ('let missionName: string = "Shelter A"', "let rows: number = 4", "let priorityMode: boolean = true", "let suppliesPlaced: number = 0"), 2, "A Boolean stores true or false. / Un Booleano guarda verdadero o falso.", "Look for the boolean type and a true/false value. / Busca el tipo boolean y un valor true/false."),
    ("Q3 Increment operation", "What does suppliesPlaced += 1 do? / ¿Qué hace suppliesPlaced += 1?", ("Resets it to 1. / Lo reinicia a 1.", "Adds 1 to its current value. / Suma 1 a su valor actual.", "Compares it with 1. / Lo compara con 1.", "Turns it into text. / Lo convierte en texto."), 1, "The += operator updates the current number by adding. / El operador += actualiza el número actual mediante una suma.", "Return to the line that runs once for every placed supply. / Vuelve a la línea que se ejecuta una vez por cada suministro colocado."),
    ("Q4 Full nested-loop count", "Across all 3 outer-loop row iterations, the inner loop completes 4 columns per row. How many supplies are placed in the full run? / En las 3 iteraciones de filas del bucle exterior, el bucle interior completa 4 columnas por fila. ¿Cuántos suministros se colocan en total?", ("4", "7", "9", "12"), 3, "Three rows times four columns equals twelve placements. / Tres filas por cuatro columnas son doce colocaciones.", "Separate one inner-loop pass (4) from the full nested-loop run (3 × 4). / Separa una pasada del bucle interior (4) de la ejecución completa (3 × 4)."),
    ("Q5 Boundary bug", "The inner condition is column < rows while rows = 3 and columns = 4. What full result should you expect before repair? / La condición interior es column < rows con rows = 3 y columns = 4. ¿Qué resultado completo debes esperar antes de reparar?", ("3 × 3 with 9 / 3 × 3 con 9", "3 × 4 with 12 / 3 × 4 con 12", "4 × 4 with 16 / 4 × 4 con 16", "No run / No ejecuta"), 0, "The inner loop incorrectly stops after three columns in each of three rows. / El bucle interior se detiene incorrectamente después de tres columnas en cada una de tres filas.", "Trace the inner condition with column values 0, 1, and 2. / Sigue la condición interior con los valores de column 0, 1 y 2."),
    ("Q6 Distinct subproblems", "How do the nested loops address different subproblems? / ¿Cómo resuelven los bucles anidados subproblemas diferentes?", ("Both do the same job. / Ambos hacen el mismo trabajo.", "Outer advances rows; inner completes columns in each row. / El exterior avanza filas; el interior completa columnas en cada fila.", "Outer stores text; inner stores a Boolean. / El exterior guarda texto; el interior guarda un Booleano.", "They only change color. / Solo cambian el color."), 1, "The two counters organize two distinct dimensions. / Los dos contadores organizan dos dimensiones diferentes.", "Point to the row counter and the column counter in your final code. / Señala el contador de filas y el de columnas en tu código final."),
    ("Q7 Meaningful number variable", "Which name best communicates the number already placed? / ¿Qué nombre comunica mejor la cantidad ya colocada?", ("x", "thing", "suppliesPlaced", "variable1"), 2, "The name states the value's purpose. / El nombre comunica el propósito del valor.", "A meaningful name should explain what the number represents. / Un nombre significativo debe explicar qué representa el número."),
    ("Q8 Design-process next step", "Your first run keeps the total correct, but markers overlap. What is the best next step? / La primera prueba mantiene el total correcto, pero los marcadores se enciman. ¿Cuál es el mejor paso siguiente?", ("Change several values at once. / Cambia varios valores a la vez.", "Record the result, revise one spacing value, and run again. / Registra el resultado, revisa un valor de espacio y ejecuta otra vez.", "Delete the loops. / Borra los bucles.", "Submit only the final screenshot. / Entrega solamente la captura final."), 1, "One controlled revision connects a cause to the observed improvement. / Una revisión controlada conecta una causa con la mejora observada.", "Use the Passport test record: first result, one exact change, next result. / Usa el registro de prueba del Pasaporte: primer resultado, un cambio exacto, siguiente resultado."),
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
    if spec.identity == 1183360:
        body = apply_game_privacy_corrections(body)
    new_body = upsert_prefixed_block(body, MARKER, block) if spec.kind == "page" else upsert_block(body, MARKER, block)
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


def ensure_page(canvas: Canvas, course_id: int, title: str, body: str, apply: bool, legacy_title: str | None = None) -> dict | None:
    pages = all_pages(canvas, course_id)
    page = pages.get(title) or (pages.get(legacy_title) if legacy_title else None)
    if not apply:
        print("DRY", "UPDATE PAGE" if page else "CREATE PAGE", title)
        return page
    if page:
        canvas.request("PUT", f"/courses/{course_id}/pages/{page['url']}", {"wiki_page[title]": title, "wiki_page[body]": body, "wiki_page[published]": "false", "wiki_page[editing_roles]": "teachers", "wiki_page[notify_of_update]": "false"})
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
        "assignment[submission_types][]": ["online_upload", "online_text_entry"],
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


DAY2_RUBRIC = (
    (
        "Student-Authored Text Code + Nested Loops",
        "JavaScript completed by the student uses an outer row loop and inner column loop to solve distinct supply-layout subproblems.",
        (
            ("Meets", 25, "Both loop structures and their required bodies are completed by the student, run correctly in JavaScript, and address the row and column subproblems."),
            ("Developing", 18, "Both loops are present, but one header/body, result, or subproblem connection is incomplete or partly incorrect."),
            ("Beginning", 10, "Only one loop is complete, the loops do not run, or the submitted view does not show student completion of the nested structure."),
            ("No Evidence", 0, "No readable student-completed nested-loop JavaScript is submitted."),
        ),
    ),
    (
        "Named Variables, Data Types + Operations",
        "The student constructs or meaningfully completes named string, number, and Boolean variables and uses operations on their values.",
        (
            ("Meets", 25, "Meaningful string, number, and Boolean variables are student-authored/completed and used with arithmetic, comparison, and Boolean operations that affect the program."),
            ("Developing", 18, "Multiple types and operations are present, but one required type, meaningful name, authored TODO, or operation-to-purpose connection is incomplete."),
            ("Beginning", 10, "Variables are mostly copied, generic, unused, or limited to one data type/operation."),
            ("No Evidence", 0, "No readable evidence of student-authored typed variables and operations is submitted."),
        ),
    ),
    (
        "Software Design Process + Required Improvement",
        "The Passport and program show problem/constraints, pseudocode, prediction, first run, one controlled revision, and observed improvement.",
        (
            ("Meets", 25, "The complete design record connects the real constraint to pseudocode, a prediction, first-run evidence, one exact controlled change, and a documented improvement."),
            ("Developing", 18, "The design/test sequence is mostly complete, but one link among constraint, prediction, first result, exact revision, or improvement is weak."),
            ("Beginning", 10, "Only a final result is shown or several design/test stages are missing, so the improvement cannot be traced."),
            ("No Evidence", 0, "No usable design-process or before/after evidence is submitted."),
        ),
    ),
    (
        "Explanation + Privacy-Safe Evidence",
        "The student explains the row/column subproblems and how authored variables/operations support the mission, with readable code and simulator evidence.",
        (
            ("Meets", 25, "The explanation accurately connects both loops, authored variables, operations, and the real constraint; final code/simulator evidence is readable and omits personal information."),
            ("Developing", 18, "Evidence is readable and mostly complete, but one explanation connection or privacy-safe evidence requirement is weak."),
            ("Beginning", 10, "The explanation is generic, one major evidence view is missing, or personal/profile details were not cropped."),
            ("No Evidence", 0, "No readable explanation and final evidence are submitted."),
        ),
    ),
)


def find_assignment_rubric(canvas: Canvas, course_id: int, assignment_id: int) -> tuple[dict, dict] | None:
    # Canvas exposes the rubric id on the assignment, but this tenant does not
    # populate associations on the course-level rubric listing even when the
    # include parameter is present. Resolve the identity from rubric_settings,
    # then request that exact rubric with associations before using a fallback.
    assignment = canvas.get(
        f"/courses/{course_id}/assignments/{assignment_id}?include[]=rubric_settings"
    )
    rubric_id = (assignment.get("rubric_settings") or {}).get("id")
    if rubric_id:
        rubric = canvas.get(f"/courses/{course_id}/rubrics/{rubric_id}?include[]=associations")
        for association in rubric.get("associations") or []:
            if association.get("association_type") == "Assignment" and int(association.get("association_id") or -1) == int(assignment_id):
                return rubric, association
    rubrics = canvas.paged(f"/courses/{course_id}/rubrics?include[]=assignment_associations&per_page=100")
    for rubric in rubrics:
        associations = rubric.get("associations") or rubric.get("assignment_associations") or []
        for association in associations:
            if association.get("association_type") == "Assignment" and int(association.get("association_id") or -1) == int(assignment_id):
                return rubric, association
    return None


def rubric_params(assignment_id: int, criteria: tuple, existing: list[dict] | None = None, association_id: int | None = None) -> dict[str, object]:
    if existing and len(existing) != len(criteria):
        raise RuntimeError(f"Refusing an ambiguous rubric rewrite: expected {len(criteria)} criteria, found {len(existing)}")
    params: dict[str, object] = {
        "rubric[title]": "Emergency Supply Grid Rubric",
        "rubric[free_form_criterion_comments]": "false",
        "rubric[skip_updating_points_possible]": "false",
        "rubric_association[association_id]": str(assignment_id),
        "rubric_association[association_type]": "Assignment",
        "rubric_association[use_for_grading]": "true",
        "rubric_association[purpose]": "grading",
    }
    if association_id is not None:
        params["rubric_association_id"] = str(association_id)
    for ci, (description, long_description, ratings) in enumerate(criteria):
        live_criterion = existing[ci] if existing else None
        prefix = f"rubric[criteria][{ci}]"
        if live_criterion and live_criterion.get("id"):
            params[f"{prefix}[id]"] = str(live_criterion["id"])
        params[f"{prefix}[description]"] = description
        params[f"{prefix}[long_description]"] = long_description
        params[f"{prefix}[points]"] = "25"
        live_ratings = (live_criterion or {}).get("ratings") or []
        if live_ratings and len(live_ratings) != len(ratings):
            raise RuntimeError(f"Refusing an ambiguous rating rewrite for {description}: expected {len(ratings)}, found {len(live_ratings)}")
        for ri, (rating, points, rating_long) in enumerate(ratings):
            rprefix = f"{prefix}[ratings][{ri}]"
            if live_ratings and live_ratings[ri].get("id"):
                params[f"{rprefix}[id]"] = str(live_ratings[ri]["id"])
            params[f"{rprefix}[description]"] = rating
            params[f"{rprefix}[long_description]"] = rating_long
            params[f"{rprefix}[points]"] = str(points)
    return params


def ensure_rubric(canvas: Canvas, course_id: int, assignment: dict, apply: bool):
    if not assignment:
        if not apply:
            print("DRY UPSERT RUBRIC", "Emergency Supply Grid Rubric")
            return
        raise RuntimeError("Day 2 assignment is required before rubric creation")
    live = canvas.get(f"/courses/{course_id}/assignments/{assignment['id']}?include[]=rubric&include[]=rubric_settings")
    existing = live.get("rubric") or []
    if not apply:
        print("DRY", "UPDATE RUBRIC" if existing else "CREATE RUBRIC", "Emergency Supply Grid Rubric", "4 criteria; Meets=25; No Evidence=0")
        return
    if existing:
        located = find_assignment_rubric(canvas, course_id, assignment["id"])
        if not located:
            raise RuntimeError("Assignment has a rubric, but its rubric/association identity could not be resolved safely")
        rubric, association = located
        params = rubric_params(assignment["id"], DAY2_RUBRIC, existing, int(association["id"]))
        canvas.request("PUT", f"/courses/{course_id}/rubrics/{rubric['id']}", params)
        print("UPDATED RUBRIC", rubric["id"], association["id"])
    else:
        params = rubric_params(assignment["id"], DAY2_RUBRIC)
        canvas.request("POST", f"/courses/{course_id}/rubrics", params)
        print("CREATED RUBRIC", "Emergency Supply Grid Rubric")


def ensure_game_remix_rubric_corrections(canvas: Canvas, course_id: int, apply: bool):
    """Keep the 100-point rubric identity while adding C4 evidence and privacy-safe naming."""
    live = canvas.get(f"/courses/{course_id}/assignments/1183360?include[]=rubric&include[]=rubric_settings")
    criteria = live.get("rubric") or []
    if len(criteria) != 4:
        raise RuntimeError(f"Game Remix rubric drifted: expected 4 criteria, found {len(criteria)}")
    if not apply:
        print("DRY UPDATE RUBRIC", "Game Remix: class alias + Passport 4 plan/test evidence; points preserved")
        return
    located = find_assignment_rubric(canvas, course_id, 1183360)
    if not located:
        raise RuntimeError("Game Remix rubric identity could not be resolved safely")
    rubric, association = located
    params: dict[str, object] = {
        "rubric[title]": live.get("rubric_settings", {}).get("title") or "Game Remix Rubric",
        "rubric[free_form_criterion_comments]": "false",
        "rubric[skip_updating_points_possible]": "true",
        "rubric_association_id": str(association["id"]),
        "rubric_association[association_id]": "1183360",
        "rubric_association[association_type]": "Assignment",
        "rubric_association[use_for_grading]": "true",
        "rubric_association[purpose]": "grading",
    }
    for ci, criterion in enumerate(criteria):
        prefix = f"rubric[criteria][{ci}]"
        params[f"{prefix}[id]"] = str(criterion["id"])
        description = criterion.get("description") or ""
        long_description = apply_game_privacy_corrections(criterion.get("long_description") or "")
        if ci == 2 and "Passport Checkpoint 4" not in long_description:
            long_description += " Passport Checkpoint 4 must show the planned feature, first test result, and one evidence-based revision."
        if ci == 3 and "Passport Checkpoint 4" not in long_description:
            long_description += " Submit readable Passport Checkpoint 4 evidence with the existing screenshot and reflection."
        params[f"{prefix}[description]"] = description
        params[f"{prefix}[long_description]"] = long_description.strip()
        params[f"{prefix}[points]"] = str(criterion.get("points") or 25)
        ratings = criterion.get("ratings") or []
        for ri, rating in enumerate(ratings):
            rprefix = f"{prefix}[ratings][{ri}]"
            params[f"{rprefix}[id]"] = str(rating["id"])
            params[f"{rprefix}[description]"] = rating.get("description") or ""
            rating_long = apply_game_privacy_corrections(rating.get("long_description") or "")
            if ci in (2, 3) and "Passport Checkpoint 4" not in rating_long:
                rating_long += " Use the Passport Checkpoint 4 plan/test evidence when selecting this rating."
            params[f"{rprefix}[long_description]"] = rating_long.strip()
            params[f"{rprefix}[points]"] = str(rating.get("points") or 0)
    canvas.request("PUT", f"/courses/{course_id}/rubrics/{rubric['id']}", params)
    canvas.request(
        "PUT",
        f"/courses/{course_id}/assignments/1183360",
        {
            "assignment[submission_types][]": ["online_upload"],
            "assignment[notify_of_update]": "false",
        },
    )
    print("UPDATED RUBRIC", rubric["id"], "Game Remix")


def update_program_scope_sequence(canvas: Canvas, course_id: int, apply: bool):
    """Keep the official pacing surface truthful about the four-period coding arc."""
    page = canvas.get(f"/courses/{course_id}/pages/{SCOPE_PAGE_URL}")
    body = page.get("body") or ""
    if SCOPE_MARKER not in body and digest(body) != SCOPE_BODY_SHA256:
        raise RuntimeError("Program Scope + Sequence drifted before the coding-foundations correction")
    body = body.replace(
        ">Video-game Skillmap<",
        ">Video-game Skillmap + Remix (Passport 4 plan/test)<",
    )
    body = body.replace(
        ">Video-game project<",
        ">Text-Code Bridge: Day 1 Trace/Repair + Day 2 Create/Improve (Passports 5–6)<",
    )
    notice = f'''<div {SCOPE_MARKER} style="margin:0 0 16px;padding:14px 16px;border:3px solid #00B8C8;border-radius:12px;background:#F4FBFC;color:#172033;"><strong>SW3 coding correction:</strong> Video Game Design now uses two periods for Skillmap/Remix and two periods for the Text-Code Bridge. Passport 4 captures the Remix plan/test; Passports 5–6 capture trace/repair and student-authored text-code evidence.</div>'''
    body = upsert_prefixed_block(body, SCOPE_MARKER, notice)
    if "Video-game Skillmap + Remix" not in body or "Text-Code Bridge: Day 1 Trace/Repair" not in body:
        raise RuntimeError("Program Scope + Sequence no longer contains the expected SW3 rows")
    print(("APPLY" if apply else "DRY"), "UPDATE", page.get("title"), digest(body)[:10])
    if apply:
        canvas.request(
            "PUT",
            f"/courses/{course_id}/pages/{SCOPE_PAGE_URL}",
            {
                "wiki_page[body]": body,
                "wiki_page[published]": "false",
                "wiki_page[notify_of_update]": "false",
            },
        )


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
        print("DRY UPSERT", len(QUIZ_QUESTIONS), "bilingual questions with corrective feedback")
        return quiz
    if quiz:
        quiz, _ = canvas.request("PUT", f"/courses/{course_id}/quizzes/{quiz['id']}", params)
    else:
        quiz, _ = canvas.request("POST", f"/courses/{course_id}/quizzes", params)
    questions = canvas.paged(f"/courses/{course_id}/quizzes/{quiz['id']}/questions?per_page=100")
    by_number: dict[int, dict] = {}
    for row in questions:
        match = re.match(r"Q(\d+)\b", row.get("question_name") or "")
        if not match:
            raise RuntimeError(f"Unexpected unnumbered question in identity-locked quiz: {row.get('question_name')!r}")
        number = int(match.group(1))
        if number in by_number:
            raise RuntimeError(f"Duplicate Q{number} in identity-locked quiz")
        by_number[number] = row
    if set(by_number) - set(range(1, len(QUIZ_QUESTIONS) + 1)):
        raise RuntimeError(f"Unexpected stale question numbers: {sorted(set(by_number) - set(range(1, len(QUIZ_QUESTIONS) + 1)))}")
    for position, (name, question_text, answers, correct, correct_feedback, incorrect_feedback) in enumerate(QUIZ_QUESTIONS, start=1):
        existing = by_number.get(position)
        qparams: dict[str, object] = {
            "question[question_name]": name,
            "question[question_text]": question_text,
            "question[question_type]": "multiple_choice_question",
            "question[points_possible]": "1",
            "question[position]": str(position),
            "question[correct_comments]": correct_feedback,
            "question[incorrect_comments]": incorrect_feedback,
            "question[neutral_comments]": "Use the matching Passport/code evidence before retrying. / Usa la evidencia correspondiente del Pasaporte/código antes de intentar otra vez.",
        }
        live_answers = (existing or {}).get("answers") or []
        if live_answers and len(live_answers) != len(answers):
            raise RuntimeError(f"Refusing an ambiguous answer rewrite for Q{position}: expected {len(answers)}, found {len(live_answers)}")
        for index, answer in enumerate(answers):
            if live_answers and live_answers[index].get("id"):
                qparams[f"question[answers][{index}][id]"] = str(live_answers[index]["id"])
            qparams[f"question[answers][{index}][answer_text]"] = answer
            qparams[f"question[answers][{index}][answer_weight]"] = "100" if index == correct else "0"
            qparams[f"question[answers][{index}][answer_comments]"] = correct_feedback if index == correct else incorrect_feedback
        if existing:
            canvas.request("PUT", f"/courses/{course_id}/quizzes/{quiz['id']}/questions/{existing['id']}", qparams)
        else:
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


def ensure_module_item(canvas: Canvas, course_id: int, module_id: int, title: str, item_type: str, content_id: int | None, page_url: str | None, apply: bool, legacy_title: str | None = None) -> dict | None:
    item = next((row for row in all_module_items(canvas, course_id, module_id) if row.get("title") in {title, legacy_title}), None)
    if not apply:
        print("DRY", "KEEP MODULE ITEM" if item else "CREATE MODULE ITEM", title)
        return item
    if item:
        if item.get("title") != title:
            canvas.request(
                "PUT",
                f"/courses/{course_id}/modules/{module_id}/items/{item['id']}",
                {"module_item[title]": title},
            )
            return canvas.get(f"/courses/{course_id}/modules/{module_id}/items/{item['id']}")
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
    scope = canvas.get(f"/courses/{course_id}/pages/{SCOPE_PAGE_URL}")
    scope_body = scope.get("body") or ""
    assert scope.get("published") is False
    assert SCOPE_MARKER in scope_body
    assert "Video-game Skillmap + Remix" in scope_body
    assert "Text-Code Bridge: Day 1 Trace/Repair" in scope_body
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
        if spec.identity == 1183360:
            assert "[Your Name] Remix" not in body and "[Tu Nombre] Remix" not in body
            assert "swap game links" not in body and "cambia juegos" not in body
    module = canvas.get(f"/courses/{course_id}/modules/{VIDEO_MODULE_ID}")
    assert module.get("name") == "SW3 · Video Game Design + Text Code"
    items = sorted(all_module_items(canvas, course_id, VIDEO_MODULE_ID), key=lambda row: row["position"])
    titles = [row["title"] for row in items]
    expected_tail = [
        "Text-Code Bridge (2 days)",
        "Facilitator Guide: Text-Code Bridge Day 1 — Trace, Predict + Repair",
        "Lesson 3: Text Code — Trace, Predict + Repair",
        "Facilitator Guide: Text-Code Bridge Day 2 — Change the Grid with Purpose",
        "Lesson 4: Text Code — Emergency Supply Grid",
        "Checkpoint: Text Code + Nested Loops",
    ]
    assert titles[-6:] == expected_tail, titles
    for title in expected_tail:
        row = next(item for item in items if item["title"] == title)
        assert row.get("published") is False
    assignments = all_assignments(canvas, course_id)
    game_remix = canvas.get(f"/courses/{course_id}/assignments/1183360?include[]=rubric")
    assert set(game_remix.get("submission_types") or []) == {"online_upload"}
    game_rubric_text = json.dumps(game_remix.get("rubric") or [], ensure_ascii=False)
    assert "your name plus the word Remix" not in game_rubric_text
    assert "does not include your name" not in game_rubric_text
    assert "class-safe alias" in game_rubric_text
    day1 = canvas.get(f"/courses/{course_id}/assignments/{assignments['Lesson 3: Text Code — Trace, Predict + Repair']['id']}")
    assert float(day1.get("points_possible") or 0) == 25
    assert set(day1.get("submission_types") or []) == {"online_upload", "online_text_entry"}
    assert "25 points" in (day1.get("description") or "") and "25 puntos" in (day1.get("description") or "")
    day2 = canvas.get(f"/courses/{course_id}/assignments/{assignments['Lesson 4: Text Code — Emergency Supply Grid']['id']}?include[]=rubric&include[]=rubric_settings")
    assert set(day2.get("submission_types") or []) == {"online_upload", "online_text_entry"}
    rubric = day2.get("rubric") or []
    assert len(rubric) == 4
    for criterion in rubric:
        ratings = {rating["description"]: float(rating["points"]) for rating in criterion.get("ratings") or []}
        assert ratings == {"Meets": 25.0, "Developing": 18.0, "Beginning": 10.0, "No Evidence": 0.0}, ratings
    quiz = all_quizzes(canvas, course_id)["Checkpoint: Text Code + Nested Loops"]
    questions = canvas.paged(f"/courses/{course_id}/quizzes/{quiz['id']}/questions?per_page=100")
    assert len(questions) == 8
    for question in questions:
        assert " / " in (question.get("question_text") or "")
        assert question.get("correct_comments") and question.get("incorrect_comments")
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
    ensure_game_remix_rubric_corrections(canvas, course_id, args.apply)
    update_program_scope_sequence(canvas, course_id, args.apply)

    overview = canvas.get(f"/courses/{course_id}/pages/unit-at-a-glance-video-game-design")
    overview_body = upsert_prefixed_block(overview.get("body") or "", OVERVIEW_MARKER, overview_block(course_id, files))
    print(("APPLY" if args.apply else "DRY"), "UPDATE", overview.get("title"), digest(overview_body)[:10])
    if args.apply:
        canvas.request("PUT", f"/courses/{course_id}/pages/unit-at-a-glance-video-game-design", {"wiki_page[body]": overview_body, "wiki_page[notify_of_update]": "false"})
        canvas.request("PUT", f"/courses/{course_id}/modules/{VIDEO_MODULE_ID}", {"module[name]": "SW3 · Video Game Design + Text Code"})

    guide1_legacy = "Teacher Guide: Text-Code Bridge Day 1 — Trace, Predict + Repair"
    guide1_title = "Facilitator Guide: Text-Code Bridge Day 1 — Trace, Predict + Repair"
    assignment1_title = "Lesson 3: Text Code — Trace, Predict + Repair"
    guide2_legacy = "Teacher Guide: Text-Code Bridge Day 2 — Change the Grid with Purpose"
    guide2_title = "Facilitator Guide: Text-Code Bridge Day 2 — Change the Grid with Purpose"
    assignment2_title = "Lesson 4: Text Code — Emergency Supply Grid"
    guide1 = ensure_page(canvas, course_id, guide1_title, bridge_teacher_body(course_id, files, 1, assignment1_title), args.apply, guide1_legacy)
    assignment1 = ensure_assignment(canvas, course_id, assignment1_title, bridge_student_body(course_id, files, 1), 1, args.apply)
    guide2 = ensure_page(canvas, course_id, guide2_title, bridge_teacher_body(course_id, files, 2, assignment2_title), args.apply, guide2_legacy)
    assignment2 = ensure_assignment(canvas, course_id, assignment2_title, bridge_student_body(course_id, files, 2), 2, args.apply)
    ensure_rubric(canvas, course_id, assignment2, args.apply)
    quiz = ensure_quiz(canvas, course_id, args.apply)

    ensure_module_item(canvas, course_id, VIDEO_MODULE_ID, "Text-Code Bridge (2 days)", "SubHeader", None, None, args.apply)
    if args.apply:
        ensure_module_item(canvas, course_id, VIDEO_MODULE_ID, guide1_title, "Page", None, guide1["url"], True, guide1_legacy)
        ensure_module_item(canvas, course_id, VIDEO_MODULE_ID, assignment1_title, "Assignment", assignment1["id"], None, True)
        ensure_module_item(canvas, course_id, VIDEO_MODULE_ID, guide2_title, "Page", None, guide2["url"], True, guide2_legacy)
        ensure_module_item(canvas, course_id, VIDEO_MODULE_ID, assignment2_title, "Assignment", assignment2["id"], None, True)
        ensure_module_item(canvas, course_id, VIDEO_MODULE_ID, "Checkpoint: Text Code + Nested Loops", "Quiz", quiz["id"], None, True)
    else:
        for title, item_type, legacy in ((guide1_title, "Page", guide1_legacy), (assignment1_title, "Assignment", None), (guide2_title, "Page", guide2_legacy), (assignment2_title, "Assignment", None), ("Checkpoint: Text Code + Nested Loops", "Quiz", None)):
            ensure_module_item(canvas, course_id, VIDEO_MODULE_ID, title, item_type, None, None, False, legacy)

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
