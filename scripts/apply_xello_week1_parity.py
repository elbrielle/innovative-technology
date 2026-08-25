#!/usr/bin/env python3
"""Stage the Week 1 Xello deck, student route, and teacher guide in Canvas.

Canvas is the authoring source.  Run without ``--apply`` for a read-only live
preflight.  ``--offline-preview`` renders the two proposed Canvas bodies
without requiring a Canvas token.  The full public mirror is regenerated only
after a successful Canvas apply and readback.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from canvas_api import Canvas, env_course_id


COURSE_ID = 23402
MODULE_ID = 72564
ASSIGNMENT_ID = 1183431
ASSIGNMENT_ITEM_ID = 2633997
ASSIGNMENT_TITLE = "Xello Check-in: Matchmaker, Personality Style, and Learning Style"
GUIDE_TITLE = "Facilitator Guide: Xello — Matchmaker, Personality Style, and Learning Style"
GUIDE_SLUG = "facilitator-guide-xello-matchmaker-personality-learning-style"
DECK_ID = "1zWB_nVYGl8bEv7ls6zyJbdZeAu1NwEyJvFgeQxn8U6A"
STUDENT_DECK_ID = "1MtqwOTdRikzDPNTy_6gUEyg7VgTH8GUJxUTXxKWH868"
DECK_EDIT = f"https://docs.google.com/presentation/d/{DECK_ID}/edit"
DECK_PRESENT = f"https://docs.google.com/presentation/d/{STUDENT_DECK_ID}/present"
DECK_COPY = f"https://docs.google.com/presentation/d/{DECK_ID}/copy"
STUDENT_MARKER = 'data-vils-xello-week1-student="2026-08-24-v1"'
GUIDE_MARKER = 'data-vils-xello-week1-guide="2026-08-24-v1"'


def student_body() -> str:
    return f'''<div {STUDENT_MARKER} style="max-width:900px;margin:0 auto;color:#1f2430;font-size:16px;line-height:1.55;">
  <div style="background:#37474f;border-left:10px solid #00838f;padding:20px 22px;margin:0 0 18px;">
    <p style="margin:0 0 6px;color:#b2ebf2;font-family:monospace;"><strong>WEEK 1 · XELLO CHECK-IN · 5 POINTS</strong></p>
    <h1 style="margin:0 0 8px;color:#fff;font-size:28px;">Matchmaker, Personality Style, and Learning Style</h1>
    <p style="margin:0;color:#fff;">Complete the assessments in order, save each result, and explain one result that surprised you or confirmed what you already knew. / Completa las evaluaciones en orden, guarda cada resultado y explica un resultado que te sorprendió o confirmó lo que ya sabías.</p>
  </div>

  <div data-vils-student-learning-block="2026-08-24-xello" style="background:#f4f8fc;border:2px solid #1b6f7a;border-radius:12px;padding:15px 17px;margin:0 0 18px;">
    <p style="margin:0 0 7px;"><strong>Topic / Tema:</strong> Xello assessment results / Resultados de las evaluaciones de Xello</p>
    <p style="margin:0 0 7px;"><strong>I can / Puedo:</strong> Complete three Xello assessments in order and explain one result that surprised me or confirmed what I already knew. / Completar tres evaluaciones de Xello en orden y explicar un resultado que me sorprendió o confirmó lo que ya sabía.</p>
    <p style="margin:0 0 7px;"><strong>Why this matters / Por qué importa:</strong> These results are clues for exploring careers and learning strategies—not labels or permanent decisions. / Estos resultados son pistas para explorar carreras y estrategias de aprendizaje, no etiquetas ni decisiones permanentes.</p>
    <p style="margin:0;"><strong>Show your learning / Demuestra tu aprendizaje:</strong> Three readable result screenshots and one honest reflection sentence. / Tres capturas legibles de resultados y una oración de reflexión honesta.</p>
  </div>

  <div style="background:#fff5cc;border:2px solid #d49b00;border-radius:10px;padding:14px 16px;margin:0 0 18px;">
    <h2 style="margin:0 0 7px;color:#6b4700;font-size:20px;">Visual walkthrough / Guía visual</h2>
    <p style="margin:0 0 8px;"><a href="{DECK_PRESENT}" target="_blank"><strong>Open the Xello visual walkthrough</strong></a> / <a href="{DECK_PRESENT}" target="_blank"><strong>Abre la guía visual de Xello</strong></a>.</p>
    <p style="margin:0 0 8px;">Use slides <strong>1–6</strong> for Matchmaker, <strong>7–11</strong> for Personality Style, and <strong>12–15</strong> for Learning Style. Slide 16 is the final submission check.</p>
    <p style="margin:0;">The screenshots use the Xello labels students see on screen. If Google Slides does not open, use the complete text directions below. / Las capturas usan las etiquetas que aparecen en Xello. Usa las instrucciones completas en español a continuación; si Google Slides no abre, esta ruta de texto contiene los mismos pasos.</p>
  </div>

  <div class="enhanceable_content tabs">
    <ul style="display:flex;gap:0;padding-left:0;margin:0 0 -1px;">
      <li style="list-style:none;background:#fff;border:1px solid #b0bec5;border-bottom:1px solid #fff;border-radius:8px 8px 0 0;"><a style="display:block;padding:10px 24px;color:#00838f;" href="#en-xello-w1">English</a></li>
      <li style="list-style:none;background:#fff;border:1px solid #b0bec5;border-bottom:1px solid #fff;border-radius:8px 8px 0 0;margin-left:-1px;"><a style="display:block;padding:10px 24px;color:#00838f;" href="#es-xello-w1">Español</a></li>
    </ul>

    <div id="en-xello-w1" style="background:#fff;border:1px solid #b0bec5;border-radius:0 8px 8px 8px;padding:22px;">
      <p style="margin-top:0;"><strong>Resume rule:</strong> Start with the first screenshot you are missing. Complete one assessment → capture its result → check it off → stop or continue.</p>
      <h2 style="color:#006d75;">1. Matchmaker · about 20–30 minutes</h2>
      <ol>
        <li>Open <strong>ClassLink</strong> and select <strong>Xello</strong>. Use the district route so your work saves to the correct account.</li>
        <li>Complete <strong>Matchmaker</strong>. If it is locked, set your <strong>After high school goal</strong>, then return.</li>
        <li>Open the completed result and capture a readable screenshot. Check off <strong>Matchmaker result saved</strong>.</li>
      </ol>

      <h2 style="color:#006d75;">2. Personality Style · about 10–20 minutes</h2>
      <ol>
        <li>Open <strong>About Me → Personality Style</strong>. Matchmaker must be finished first.</li>
        <li>Complete the questions, open the result, and capture a readable screenshot. Check off <strong>Personality Style result saved</strong>.</li>
      </ol>

      <h2 style="color:#006d75;">3. Learning Style · about 8–15 minutes</h2>
      <ol>
        <li>Open <strong>About Me → Learning Style</strong> and complete the questions.</li>
        <li>Open the result and capture a readable screenshot. Check off <strong>Learning Style result saved</strong>.</li>
      </ol>
      <p><strong>Need to stop?</strong> Choose <strong>Done</strong> so Xello saves your answers. Return through <strong>About Me</strong>. Use <strong>Review My Answers</strong> if you need to change an earlier response. Do not reset Matchmaker unless your teacher tells you to.</p>

      <h2 style="color:#006d75;">Capture, name, and upload the files</h2>
      <ol>
        <li><strong>Chromebook:</strong> press <strong>Shift + Ctrl + Show windows</strong>, then drag around only the result panel. This captures a selected area and crops out your name, email address, and profile details before the file is saved.</li>
        <li><strong>Windows:</strong> press <strong>Windows + Shift + S</strong> and drag around only the result panel.</li>
        <li>Find the images in <strong>Files → Downloads</strong>. Rename them <strong>Matchmaker</strong>, <strong>Personality</strong>, and <strong>Learning</strong>.</li>
        <li>In Canvas choose <strong>Submit Assignment → File Upload → Choose File</strong>, select the three images from Downloads, add the reflection in the submission comment, and submit.</li>
      </ol>

      <h2 style="color:#006d75;">Reflect once</h2>
      <p>Write this sentence in the submission comments: <strong>One result that surprised me or confirmed what I already knew was ____ because ____.</strong></p>
      <p><strong>Word bank:</strong> interest · career match · personality style · learning style · result · surprised</p>
      <div style="background:#e0f2f1;border:2px solid #00838f;padding:12px 14px;margin-bottom:14px;"><strong>You are done when:</strong> three readable screenshots are attached, private profile details are cropped out, and one honest reflection sentence is in the comments.</div>
      <div style="background:#f4f8fc;border:2px solid #1b6f7a;padding:12px 14px;margin-bottom:14px;"><strong>How the 5 points work:</strong> 1 point for each completed result screenshot (3); 1 point when all three are readable and privacy-safe; 1 point for the reflection. An unreadable or privacy-unsafe image is returned for correction before the grade is finalized.</div>
      <p><strong>Optional when finished:</strong> Open one career match that interests you and write one question you would ask someone in that career. Do not upload extra evidence.</p>
    </div>

    <div id="es-xello-w1" lang="es" style="background:#fff;border:1px solid #b0bec5;border-radius:0 8px 8px 8px;padding:22px;">
      <p style="margin-top:0;"><strong>Regla para continuar:</strong> Empieza con la primera captura que te falte. Completa una evaluación → captura el resultado → márcala → detente o continúa.</p>
      <h2 style="color:#006d75;">1. Matchmaker · aproximadamente 20–30 minutos</h2>
      <ol>
        <li>Abre <strong>ClassLink</strong> y selecciona <strong>Xello</strong>. Usa el acceso del distrito para que tu trabajo se guarde en la cuenta correcta.</li>
        <li>Completa <strong>Matchmaker</strong>. Si está bloqueado, escoge tu <strong>After high school goal</strong> y regresa.</li>
        <li>Abre el resultado completo y toma una captura legible. Marca <strong>Resultado de Matchmaker guardado</strong>.</li>
      </ol>

      <h2 style="color:#006d75;">2. Personality Style · aproximadamente 10–20 minutos</h2>
      <ol>
        <li>Abre <strong>About Me → Personality Style</strong>. Primero debes terminar Matchmaker.</li>
        <li>Completa las preguntas, abre el resultado y toma una captura legible. Marca <strong>Resultado de Personality Style guardado</strong>.</li>
      </ol>

      <h2 style="color:#006d75;">3. Learning Style · aproximadamente 8–15 minutos</h2>
      <ol>
        <li>Abre <strong>About Me → Learning Style</strong> y completa las preguntas.</li>
        <li>Abre el resultado y toma una captura legible. Marca <strong>Resultado de Learning Style guardado</strong>.</li>
      </ol>
      <p><strong>¿Necesitas detenerte?</strong> Selecciona <strong>Done</strong> para guardar tus respuestas. Regresa por <strong>About Me</strong>. Usa <strong>Review My Answers</strong> para cambiar una respuesta anterior. No reinicies Matchmaker a menos que tu maestro te lo indique.</p>

      <h2 style="color:#006d75;">Captura, nombra y sube los archivos</h2>
      <ol>
        <li><strong>Chromebook:</strong> presiona <strong>Mayús + Ctrl + Mostrar ventanas</strong> y arrastra alrededor de solamente el panel de resultados. Así capturas un área seleccionada y recortas tu nombre, correo y detalles del perfil antes de guardar.</li>
        <li><strong>Windows:</strong> presiona <strong>Windows + Shift + S</strong> y arrastra alrededor de solamente el panel de resultados.</li>
        <li>Busca las imágenes en <strong>Archivos → Descargas</strong>. Cámbiales el nombre a <strong>Matchmaker</strong>, <strong>Personality</strong> y <strong>Learning</strong>.</li>
        <li>En Canvas selecciona <strong>Entregar tarea → Carga de archivo → Elegir archivo</strong>, selecciona las tres imágenes de Descargas, agrega la reflexión en el comentario y entrega.</li>
      </ol>

      <h2 style="color:#006d75;">Reflexiona una vez</h2>
      <p>Escribe esta oración en los comentarios de la entrega: <strong>Un resultado que me sorprendió o confirmó lo que ya sabía fue ____ porque ____.</strong></p>
      <p><strong>Banco de palabras:</strong> interés · coincidencia de carrera · estilo de personalidad · estilo de aprendizaje · resultado · sorprendió</p>
      <div style="background:#e0f2f1;border:2px solid #00838f;padding:12px 14px;margin-bottom:14px;"><strong>Terminas cuando:</strong> adjuntaste tres capturas legibles, recortaste los detalles privados del perfil y escribiste una oración de reflexión honesta en los comentarios.</div>
      <div style="background:#f4f8fc;border:2px solid #1b6f7a;padding:12px 14px;margin-bottom:14px;"><strong>Cómo funcionan los 5 puntos:</strong> 1 punto por cada captura de resultado completo (3); 1 punto cuando las tres capturas son legibles y protegen tu privacidad; 1 punto por la reflexión. Una imagen ilegible o con información privada se devuelve para corregirla antes de finalizar la calificación.</div>
      <p><strong>Opcional cuando termines:</strong> Abre una carrera que te interese y escribe una pregunta que le harías a alguien con esa carrera. No subas evidencia adicional.</p>
    </div>
  </div>

  <div style="margin-top:18px;border-top:1px solid #b0bec5;padding-top:12px;font-size:14px;color:#455a64;">
    <p style="margin:0 0 5px;"><strong>Sources:</strong> Xello student assessments and official Xello visual resources.</p>
    <p style="margin:0;"><a href="https://help.xello.world/en-us/Content/Knowledge-Base/Xello-6-12/Assessments/Students-Matchmaker.htm" target="_blank">Matchmaker support</a> · <a href="https://help.xello.world/en-us/Content/Knowledge-Base/Xello-6-12/Assessments/Students-Personality-Style.htm" target="_blank">Personality Style support</a> · <a href="https://help.xello.world/en-us/content/Resources/PDFs/Guides/Stu_Assessments.pdf" target="_blank">Assessments in Xello student guide</a></p>
  </div>
</div>'''


def teacher_body() -> str:
    return f'''<div {GUIDE_MARKER} data-vils-target-module-item="{ASSIGNMENT_ITEM_ID}" style="max-width:900px;margin:0 auto;color:#1f2430;font-size:16px;line-height:1.55;">
  <div style="background:#10233f;border-left:10px solid #ef3340;padding:20px 22px;margin:0 0 18px;">
    <p style="margin:0 0 6px;color:#ffd34e;font-family:monospace;"><strong>TEACHER ONLY · WEEK 1 · XELLO</strong></p>
    <h1 style="margin:0 0 8px;color:#fff;font-size:29px;">Matchmaker, Personality Style, and Learning Style</h1>
    <p style="margin:0;color:#e7eef8;">Use the projected Xello deck to model the exact route, pause between assessments when needed, and collect three privacy-safe result screenshots plus one reflection.</p>
  </div>

  <div data-vils-daily-learning-contract="2026-08-21-semantic-audit-v1" style="background:#f4f8fc;border:2px solid #1b6f7a;border-radius:12px;padding:16px 18px;margin:0 0 18px;">
    <h2 style="margin:0 0 10px;font-size:22px;color:#1b6f7a;">Daily Learning Contract</h2>
    <p style="margin:0 0 7px;"><strong>Topic:</strong> Xello assessment results and career self-knowledge</p>
    <p style="margin:0 0 7px;"><strong>Student objective:</strong> Students will complete Matchmaker, Personality Style, and Learning Style in the required order and explain one result that surprised them or confirmed what they already knew.</p>
    <p style="margin:0 0 7px;"><strong>Essential TEKS:</strong> None. This is an operational college-and-career-readiness check-in; it does not independently demonstrate a Grade 8 Technology Applications TEKS expectation.</p>
    <p style="margin:0 0 7px;"><strong>Supporting TEKS:</strong> None claimed. Students practice digital navigation, file capture, and privacy decisions without treating ordinary tool use as standards evidence.</p>
    <p style="margin:0 0 7px;"><strong>Demonstration of learning:</strong> Three readable, privacy-safe result screenshots and one honest sentence explaining a result that surprised the student or confirmed prior self-knowledge.</p>
    <p style="margin:0;"><strong>Alignment status:</strong> Not applicable — operational Xello check-in.</p>
  </div>

  <div style="background:#fff5cc;border:2px solid #d49b00;border-radius:10px;padding:14px 16px;margin:0 0 18px;">
    <h2 style="margin:0 0 7px;color:#6b4700;font-size:20px;">Project the complete visual route</h2>
    <p style="margin:0 0 8px;"><a href="{DECK_EDIT}" target="_blank"><strong>Open the live Xello deck</strong></a> · <a href="{DECK_COPY}" target="_blank">Make a teacher copy</a></p>
    <p style="margin:0 0 8px;"><a href="{DECK_PRESENT}" target="_blank"><strong>Open the 16-slide student walkthrough</strong></a>. This copy removes teacher-only route and stop cards.</p>
    <p style="margin:0 0 6px;"><strong>Matchmaker:</strong> slides 2–7; slide 8 is the teacher stop card.</p>
    <p style="margin:0 0 6px;"><strong>Personality Style:</strong> slides 9–13; slide 14 is the teacher stop card.</p>
    <p style="margin:0;"><strong>Learning Style:</strong> slides 15–18; slide 19 checks the final submission.</p>
  </div>

  <h2 style="color:#b4232d;">Choose the pacing route before class</h2>
  <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:12px;margin:0 0 18px;">
    <div style="border:2px solid #93a4b8;padding:14px 16px;">
      <h3 style="margin:0 0 7px;">One assessment per day</h3>
      <p style="margin:0 0 6px;"><strong>Day 1 (35–45 min Xello):</strong> 5-minute launch; 20–30-minute Matchmaker; 5-minute result capture/check; 5-minute close at slide 8. Use remaining minutes to finish or revise the existing <em>Activity: Ready, Set, Design</em> evidence.</p>
      <p style="margin:0 0 6px;"><strong>Day 2 (25–35 min Xello):</strong> 5-minute relaunch; 10–20-minute Personality Style; 5-minute result capture/check; 5-minute close at slide 14. Use remaining minutes for the existing Ready, Set, Design activity or worksheet route; do not add another Xello product.</p>
      <p style="margin:0;"><strong>Day 3 (30–40 min Xello):</strong> 5-minute relaunch; 8–15-minute Learning Style; 5-minute result capture/check; 10-minute single reflection and Canvas upload. Use remaining minutes to finish the existing Week 1 design-thinking evidence or the teacher-assigned current module task.</p>
    </div>
    <div style="border:2px solid #93a4b8;padding:14px 16px;">
      <h3 style="margin:0 0 7px;">Compressed 50–55 minute route</h3>
      <p style="margin:0 0 6px;">Use only when students already have working ClassLink/Xello access and an After high school goal.</p>
      <p style="margin:0;">Launch 5 min · Matchmaker 20 min · Personality Style 10–12 min · Learning Style 8–10 min · screenshots, reflection, and upload 8 min. Unfinished students save and resume in the next work block.</p>
    </div>
  </div>

  <h2 style="color:#b4232d;">Before students begin</h2>
  <ul>
    <li>Test ClassLink → Xello on a student device and open the Canvas assignment in Student View.</li>
    <li>Open the deck and test the embedded Xello video. Enable captions when the player provides them; otherwise keep the complete text route visible and summarize the video aloud.</li>
    <li>Confirm whether students already set an After high school goal. Matchmaker stays locked until that prerequisite is complete.</li>
    <li>Keep the bilingual Canvas assignment open as the accessible, independent, and absence route.</li>
    <li>Do not project a real student's account. The deck uses first-party Xello demonstration screens.</li>
  </ul>

  <h2 style="color:#b4232d;">Teach the route end to end</h2>
  <ol>
    <li><strong>Launch:</strong> Explain that these results are starting points, not labels or permanent decisions. Ask students to answer honestly rather than choosing what sounds impressive.</li>
    <li><strong>Model Matchmaker:</strong> Project slides 2–6. Show where the question-mark help, <em>Done</em>, and <em>Review My Answers</em> controls appear. Students complete the assessment and save one readable result screenshot.</li>
    <li><strong>Checkpoint:</strong> Verify that students have a saved Matchmaker result before they open Personality Style. If this is a one-day route, stop at slide 8.</li>
    <li><strong>Model Personality Style:</strong> Use slides 9–12 to show the About Me route, the six Xello style names, and the result screen. Students save their second screenshot. They do not submit a separate Personality reflection.</li>
    <li><strong>Checkpoint:</strong> Confirm the second screenshot. If this is a second workday, stop at slide 14 after the screenshot is saved.</li>
    <li><strong>Model Learning Style:</strong> Use slides 15–17. Emphasize that a result can be a mix and that students can try methods from every category.</li>
    <li><strong>Close:</strong> Project slides 18–19. Students crop private profile details, attach three screenshots, and write one final sentence about a result that surprised them or confirmed what they already knew.</li>
  </ol>

  <h2 style="color:#b4232d;">Checks, expected responses, and misconceptions</h2>
  <ul>
    <li><strong>Check:</strong> “Which assessment must be complete before Personality Style opens?” <strong>Expected:</strong> Matchmaker.</li>
    <li><strong>Check:</strong> “What should you do if time ends during a quiz?” <strong>Expected:</strong> Choose Done, then return through About Me.</li>
    <li><strong>Check:</strong> “Does Learning Style limit you to one way of learning?” <strong>Expected:</strong> No. It shows a current mix of preferences; students can use several strategies.</li>
    <li><strong>Misconception:</strong> A career or learning result is a final decision. <strong>Response:</strong> Frame it as evidence for exploration, not a label.</li>
    <li><strong>Misconception:</strong> A screenshot of the quiz questions counts. <strong>Response:</strong> Require the completed result screen.</li>
  </ul>

  <h2 style="color:#b4232d;">UDL, differentiation, and DOK scaffolds</h2>
  <ul>
    <li><strong>Representation:</strong> projected authentic Xello screens, embedded video with available captions or a teacher summary, bilingual text route, alt text, and a printable slide view.</li>
    <li><strong>Action and expression:</strong> students may complete the assessments in one block or across separate days. When screenshot capture is inaccessible, an adult may guide the device controls without choosing answers, or the teacher may privately verify the completed result screens and record completion without storing private profile data. When an accommodation permits oral or dictated response, accept the same reflection sentence and record it in a private Canvas grading comment or other district-approved accommodation channel.</li>
    <li><strong>Executive-function support:</strong> use the stop cards, confirm one screenshot before moving on, and provide a three-item upload checklist.</li>
    <li><strong>English learner support:</strong> keep the word bank and complete sentence stem visible when students write the reflection.</li>
    <li><strong>DOK 1:</strong> navigate, complete, save, and capture results. <strong>DOK 2:</strong> interpret one result and explain why it was surprising or why it confirmed prior self-knowledge. Do not claim DOK 3 from this check-in.</li>
  </ul>

  <h2 style="color:#b4232d;">Troubleshooting and recovery</h2>
  <ul>
    <li><strong>ClassLink or Xello will not open:</strong> confirm the network connection, close and reopen ClassLink, and use the district Xello tile—not a personal Google search or new account. Record the exact error and assign a make-up window after access is restored; do not substitute invented assessment results.</li>
    <li><strong>Matchmaker is locked:</strong> set the After high school goal, then return to About Me.</li>
    <li><strong>Personality Style is locked:</strong> finish Matchmaker first.</li>
    <li><strong>A student needs to stop:</strong> choose Done. Xello saves the completed answers.</li>
    <li><strong>A result changed or looks wrong:</strong> use Review My Answers; do not reset Matchmaker unless an adult has confirmed that deleting the assessment answers is appropriate.</li>
    <li><strong>The deck will not open:</strong> use the complete bilingual Canvas directions and the official Xello support links on the student page.</li>
    <li><strong>A student cannot capture or find the images:</strong> use Shift + Ctrl + Show windows on Chromebook or Windows + Shift + S, capture only the result panel, then open Files → Downloads. Rename the files before upload.</li>
    <li><strong>Canvas upload fails:</strong> preserve the three images locally, record which evidence is complete, and use the next class upload window rather than repeating the assessments.</li>
  </ul>

  <h2 style="color:#b4232d;">Evidence and grading</h2>
  <p>Keep the existing assignment settings: <strong>5 points</strong>, file upload, and one reflection in the submission comments. Do not add a second product.</p>
  <ol>
    <li><strong>1 point:</strong> completed Matchmaker result screenshot.</li>
    <li><strong>1 point:</strong> completed Personality Style result screenshot.</li>
    <li><strong>1 point:</strong> completed Learning Style result screenshot.</li>
    <li><strong>1 point:</strong> all three images are readable and crop out names, email addresses, and profile details.</li>
    <li><strong>1 point:</strong> one honest sentence explains a result that surprised the student or confirmed what the student already knew.</li>
  </ol>
  <p>Return an unreadable or privacy-unsafe image for correction before finalizing the grade. Do not retain or display an unnecessary screenshot containing private profile details.</p>

  <div style="background:#e0f2f1;border:2px solid #00838f;padding:14px 16px;margin:0 0 18px;">
    <h2 style="margin:0 0 7px;color:#006d75;font-size:20px;">Absence and independent route</h2>
    <p style="margin:0;">Students open the Canvas assignment, use the linked visual walkthrough, follow the bilingual Now / Next / Then / Done directions, and save after each assessment. A returning student resumes at the first missing screenshot rather than repeating completed assessments.</p>
  </div>

  <div style="border-top:1px solid #b0bec5;padding-top:12px;font-size:14px;color:#455a64;">
    <p style="margin:0 0 5px;"><strong>Sources:</strong> Xello educator Completion Standards resources, official assessment support, official lesson imagery, and the current Canvas assignment.</p>
    <p style="margin:0;"><a href="https://help.xello.world/en-us/Content/Knowledge-Base/Xello-6-12/Assessments/Students-Matchmaker.htm" target="_blank">Matchmaker</a> · <a href="https://help.xello.world/en-us/Content/Knowledge-Base/Xello-6-12/Assessments/Students-Personality-Style.htm" target="_blank">Personality Style</a> · <a href="https://help.xello.world/en-us/content/Resources/PDFs/Guides/Stu_Assessments.pdf" target="_blank">Assessments in Xello</a></p>
  </div>
</div>'''


def preview_document(title: str, body: str) -> str:
    return f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{title}</title><style>body{{margin:0;background:#eef2f5;font-family:Arial,sans-serif}}main{{background:#fff;max-width:980px;margin:24px auto;padding:24px}}a{{color:#006d75}}@media(max-width:700px){{main{{margin:0;padding:14px}}}}</style></head><body><main>{body}</main></body></html>'''


def write_previews(directory: Path) -> None:
    directory.mkdir(parents=True, exist_ok=True)
    (directory / "student.html").write_text(preview_document(ASSIGNMENT_TITLE, student_body()), encoding="utf-8")
    (directory / "teacher.html").write_text(preview_document(GUIDE_TITLE, teacher_body()), encoding="utf-8")
    (directory / "summary.json").write_text(
        json.dumps(
            {
                "student_marker": STUDENT_MARKER,
                "guide_marker": GUIDE_MARKER,
                "deck_id": DECK_ID,
                "student_deck_id": STUDENT_DECK_ID,
                "student_body_chars": len(student_body()),
                "teacher_body_chars": len(teacher_body()),
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


def pages_by_title(canvas: Canvas, course_id: int) -> dict[str, dict]:
    return {row["title"]: row for row in canvas.paged(f"/courses/{course_id}/pages?per_page=100")}


def module_items(canvas: Canvas, course_id: int) -> list[dict]:
    return canvas.paged(f"/courses/{course_id}/modules/{MODULE_ID}/items?per_page=100")


def validate_assignment_contract(assignment: dict) -> None:
    if float(assignment.get("points_possible") or 0) != 5.0:
        raise RuntimeError("Week 1 Xello assignment must remain worth exactly 5 points")
    if assignment.get("grading_type") != "points":
        raise RuntimeError("Week 1 Xello assignment must use points grading")
    if assignment.get("submission_types") != ["online_upload"]:
        raise RuntimeError("Week 1 Xello assignment must remain an online file-upload assignment")


def validate_guide_visibility(page: dict, module_item: dict) -> None:
    if page.get("published"):
        raise RuntimeError("The Xello facilitator guide must remain unpublished")
    if page.get("hide_from_students") is not True:
        raise RuntimeError("The Xello facilitator guide must remain hidden from students")
    if page.get("editing_roles") != "teachers":
        raise RuntimeError("The Xello facilitator guide must remain editable only by teachers")
    if module_item.get("published"):
        raise RuntimeError("The Xello facilitator guide module item must remain unpublished")


def preflight(canvas: Canvas, course_id: int) -> dict:
    course = canvas.get(f"/courses/{course_id}")
    if course["id"] != COURSE_ID:
        raise RuntimeError(f"Expected course {COURSE_ID}, found {course['id']}")
    items = sorted(module_items(canvas, course_id), key=lambda row: row["position"])
    target = next((row for row in items if row["id"] == ASSIGNMENT_ITEM_ID), None)
    if not target or target.get("content_id") != ASSIGNMENT_ID or target.get("type") != "Assignment":
        raise RuntimeError("The immutable Week 1 Xello assignment identity did not match")
    assignment = canvas.get(f"/courses/{course_id}/assignments/{ASSIGNMENT_ID}")
    if assignment.get("name") != ASSIGNMENT_TITLE:
        raise RuntimeError(f"Unexpected assignment title: {assignment.get('name')}")
    validate_assignment_contract(assignment)
    pages = pages_by_title(canvas, course_id)
    guide = pages.get(GUIDE_TITLE)
    if guide:
        live = canvas.get(f"/courses/{course_id}/pages/{guide['url']}")
        if GUIDE_MARKER not in (live.get("body") or ""):
            raise RuntimeError(f"Existing page title conflicts with the Xello guide contract: {GUIDE_TITLE}")
    guide_item = next((row for row in items if guide and row.get("page_url") == guide["url"]), None)
    return {
        "course": {"id": course["id"], "name": course.get("name")},
        "target": {
            "module_item_id": target["id"],
            "content_id": target["content_id"],
            "position": target["position"],
            "published": target.get("published"),
        },
        "assignment": {
            "id": assignment["id"],
            "name": assignment["name"],
            "published": assignment.get("published"),
            "points_possible": assignment.get("points_possible"),
            "grading_type": assignment.get("grading_type"),
            "submission_types": assignment.get("submission_types"),
            "body_has_student_marker": STUDENT_MARKER in (assignment.get("description") or ""),
            "body_has_deck": STUDENT_DECK_ID in (assignment.get("description") or ""),
        },
        "guide": None
        if not guide
        else {
            "title": guide["title"],
            "url": guide["url"],
            "published": guide.get("published"),
            "hide_from_students": guide.get("hide_from_students"),
            "module_item_id": guide_item.get("id") if guide_item else None,
            "position": guide_item.get("position") if guide_item else None,
            "module_item_published": guide_item.get("published") if guide_item else None,
        },
    }


def apply(canvas: Canvas, course_id: int, before: dict) -> dict:
    canvas.request(
        "PUT",
        f"/courses/{course_id}/assignments/{ASSIGNMENT_ID}",
        {
            "assignment[description]": student_body(),
            "assignment[notify_of_update]": "false",
        },
    )

    pages = pages_by_title(canvas, course_id)
    guide = pages.get(GUIDE_TITLE)
    created_guide = guide is None
    if guide is None:
        guide, _ = canvas.request(
            "POST",
            f"/courses/{course_id}/pages",
            {
                "wiki_page[title]": GUIDE_TITLE,
                "wiki_page[body]": teacher_body(),
                "wiki_page[published]": "false",
                "wiki_page[hide_from_students]": "true",
                "wiki_page[editing_roles]": "teachers",
                "wiki_page[notify_of_update]": "false",
            },
        )
    else:
        guide, _ = canvas.request(
            "PUT",
            f"/courses/{course_id}/pages/{guide['url']}",
            {
                "wiki_page[body]": teacher_body(),
                "wiki_page[published]": "false",
                "wiki_page[hide_from_students]": "true",
                "wiki_page[editing_roles]": "teachers",
                "wiki_page[notify_of_update]": "false",
            },
        )

    items = sorted(module_items(canvas, course_id), key=lambda row: row["position"])
    target = next(row for row in items if row["id"] == ASSIGNMENT_ITEM_ID)
    guide_item = next((row for row in items if row.get("page_url") == guide["url"]), None)
    created_item = guide_item is None
    if guide_item is None:
        guide_item, _ = canvas.request(
            "POST",
            f"/courses/{course_id}/modules/{MODULE_ID}/items",
            {
                "module_item[type]": "Page",
                "module_item[page_url]": guide["url"],
                "module_item[position]": str(target["position"]),
                "module_item[published]": "false",
            },
        )
    else:
        items = sorted(module_items(canvas, course_id), key=lambda row: row["position"])
        guide_index = next(index for index, row in enumerate(items) if row["id"] == guide_item["id"])
        target_index = next(index for index, row in enumerate(items) if row["id"] == ASSIGNMENT_ITEM_ID)
        item_update = {"module_item[published]": "false"}
        if guide_index + 1 != target_index:
            item_update["module_item[position]"] = str(items[target_index]["position"])
        guide_item, _ = canvas.request(
            "PUT",
            f"/courses/{course_id}/modules/{MODULE_ID}/items/{guide_item['id']}",
            item_update,
        )

    after = preflight(canvas, course_id)
    assignment = canvas.get(f"/courses/{course_id}/assignments/{ASSIGNMENT_ID}")
    validate_assignment_contract(assignment)
    guide_live = canvas.get(f"/courses/{course_id}/pages/{guide['url']}")
    items_after = sorted(module_items(canvas, course_id), key=lambda row: row["position"])
    guide_index = next(index for index, row in enumerate(items_after) if row.get("page_url") == guide["url"])
    target_index = next(index for index, row in enumerate(items_after) if row["id"] == ASSIGNMENT_ITEM_ID)

    if STUDENT_MARKER not in (assignment.get("description") or "") or STUDENT_DECK_ID not in (assignment.get("description") or ""):
        raise RuntimeError("Student assignment readback failed")
    if GUIDE_MARKER not in (guide_live.get("body") or "") or DECK_ID not in (guide_live.get("body") or ""):
        raise RuntimeError("Teacher guide readback failed")
    if guide_index + 1 != target_index:
        raise RuntimeError("Teacher guide is not immediately before the Xello assignment")
    if assignment.get("published") != before["assignment"]["published"]:
        raise RuntimeError("Assignment publication state changed")
    if items_after[target_index].get("published") != before["target"]["published"]:
        raise RuntimeError("Assignment module-item publication state changed")
    validate_guide_visibility(guide_live, items_after[guide_index])

    return {
        "before": before,
        "after": after,
        "created_guide": created_guide,
        "created_module_item": created_item,
        "verified": {
            "student_marker": True,
            "teacher_marker": True,
            "deck_id": DECK_ID,
            "student_deck_id": STUDENT_DECK_ID,
            "guide_module_item_id": items_after[guide_index]["id"],
            "guide_position": items_after[guide_index]["position"],
            "assignment_position": items_after[target_index]["position"],
            "assignment_publication_preserved": assignment.get("published"),
            "assignment_item_publication_preserved": items_after[target_index].get("published"),
            "guide_published": guide_live.get("published"),
            "guide_item_published": items_after[guide_index].get("published"),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Write the reviewed bodies to Canvas and verify readback.")
    parser.add_argument("--offline-preview", action="store_true", help="Generate local previews without reading Canvas.")
    parser.add_argument("--preview-dir", type=Path, default=Path("tmp/xello-week1-parity"))
    args = parser.parse_args()

    if args.offline_preview:
        write_previews(args.preview_dir)
        print(json.dumps({"offline_preview": True, "preview_dir": str(args.preview_dir), "deck_id": DECK_ID, "student_deck_id": STUDENT_DECK_ID}, indent=2))
        return

    course_id = env_course_id()
    if course_id != COURSE_ID:
        raise RuntimeError(f"This bounded apply supports only course {COURSE_ID}")
    canvas = Canvas()
    before = preflight(canvas, course_id)
    if not args.apply:
        print(json.dumps({"apply": False, "preflight": before, "would_update_assignment": ASSIGNMENT_ID, "would_ensure_guide": GUIDE_TITLE}, indent=2))
        return
    result = apply(canvas, course_id, before)
    print(json.dumps({"apply": True, **result}, indent=2))


if __name__ == "__main__":
    main()
