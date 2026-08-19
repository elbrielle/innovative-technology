#!/usr/bin/env python3
"""Create missing daily facilitator guides for late-course VILS modules.

Canvas is the instructional source. This script only creates unpublished teacher
pages and adds them immediately before their matching student items in course
23402. It deliberately leaves existing lesson-specific guide/material routes
alone and does not touch the Parked Alternates module.

Run without --apply to perform the live preflight. Run with --apply only after
reviewing the printed targets. Re-running is safe: each page is identified by
its stable page URL and a course-specific marker.
"""

from __future__ import annotations

import argparse
import html
from dataclasses import dataclass

from canvas_api import Canvas, env_course_id


COURSE_ID = env_course_id()
MARKER = 'data-vils-lesson-guide="2026-08-19"'


@dataclass(frozen=True)
class Guide:
    module_id: int
    module_name: str
    before_item_id: int
    target: str
    title: str
    slug: str
    topic: str
    objective: str
    essential: tuple[tuple[str, str], ...]
    supporting: tuple[tuple[str, str], ...]
    evidence: str
    scope: str
    prep: tuple[str, ...]
    flow: tuple[tuple[str, str], ...]
    check: str
    support: str


TEKS = {
    "§126.19(c)(1)(E)": "develop, compare, and improve algorithms for a specific task to solve a problem;",
    "§126.19(c)(3)(B)": "discuss and implement a design process that includes planning, selecting digital tools to develop, test, and evaluate design limitations, and refining a prototype or model;",
    "§126.19(c)(4)(C)": "transfer current knowledge to the learning of newly encountered technologies.",
    "§126.19(c)(5)(B)": "apply appropriate search strategies, including keywords, Boolean operators, and limiters, to achieve a specified outcome that includes a variety of file formats.",
    "§126.19(c)(8)(B)": "create and publish a formal digital communication for a global audience using appropriate digital etiquette;",
    "§126.19(c)(9)(C)": "create citations and cite sources for a variety of digital forms of intellectual property;",
    "§126.19(c)(11)(A)": "combine various file formats for a specific project or audience; and",
    "§126.19(c)(11)(B)": "share and seek feedback on files in various formats, including text, raster and vector graphics, video, and audio files.",
    "§126.19(c)(12)(F)": "apply appropriate troubleshooting techniques and seek technical assistance as needed;",
    "§126.19(c)(12)(H)": "select and use productivity tools found in spread sheet, word processing, and publication applications to create digital artifacts, including reports, graphs, and charts, with increasing complexity.",
}


def standards(codes: tuple[tuple[str, str], ...]) -> str:
    if not codes:
        return "<p style=\"margin:6px 0 0;\">None claimed for this preparation or operational item. The student product does not independently demonstrate a TEKS expectation.</p>"
    rows = "".join(
        f"<li style=\"margin:0 0 7px;\"><strong>{html.escape(code)}</strong> — {html.escape(TEKS[code])}</li>"
        for code, _ in codes
    )
    return f"<ul style=\"margin:7px 0 0;padding-left:22px;\">{rows}</ul>"


def bullets(items: tuple[str, ...]) -> str:
    return "".join(f"<li style=\"margin:0 0 7px;\">{html.escape(item)}</li>" for item in items)


def guide_body(guide: Guide) -> str:
    flow = "".join(
        f"<li style=\"margin:0 0 10px;\"><strong>{html.escape(label)}:</strong> {html.escape(detail)}</li>"
        for label, detail in guide.flow
    )
    return f'''<div {MARKER} style="font-family:'Segoe UI',Arial,sans-serif;color:#172B4D;font-size:16px;line-height:1.55;max-width:980px;">
  <div style="background:#173F5F;border-radius:14px;padding:20px 22px;margin:0 0 16px;color:#FFFFFF;">
    <p style="margin:0 0 5px;font-size:14px;"><strong>TEACHER ONLY · DAILY FACILITATOR GUIDE</strong></p>
    <h2 style="margin:0;font-size:27px;color:#FFFFFF;">{html.escape(guide.title.replace('Teacher Guide: ', ''))}</h2>
  </div>
  <div style="background:#F4F8FC;border:2px solid #274C77;border-radius:12px;padding:16px 18px;margin:0 0 16px;">
    <h3 style="margin:0 0 10px;color:#10223B;font-size:21px;">Daily Learning Contract</h3>
    <p style="margin:0 0 8px;"><strong>Topic:</strong> {html.escape(guide.topic)}</p>
    <p style="margin:0 0 8px;"><strong>Student objective:</strong> Students will {html.escape(guide.objective)}</p>
    <div style="margin:0 0 8px;"><strong>Essential TEKS:</strong>{standards(guide.essential)}</div>
    <div style="margin:0 0 8px;"><strong>Supporting TEKS:</strong>{standards(guide.supporting)}</div>
    <p style="margin:0 0 8px;"><strong>Demonstration of learning:</strong> {html.escape(guide.evidence)}</p>
    <p style="margin:0;"><strong>Scope:</strong> {html.escape(guide.scope)}</p>
  </div>
  <div style="display:block;background:#FFFFFF;border:1px solid #B8C8D8;border-radius:12px;padding:16px 18px;margin:0 0 16px;">
    <h3 style="margin:0 0 8px;color:#173F5F;font-size:20px;">Before class</h3>
    <ul style="margin:0;padding-left:22px;">{bullets(guide.prep)}</ul>
  </div>
  <div style="background:#FFF9E8;border:1px solid #D6B656;border-radius:12px;padding:16px 18px;margin:0 0 16px;">
    <h3 style="margin:0 0 8px;color:#624A00;font-size:20px;">Five-part lesson flow</h3>
    <ol style="margin:0;padding-left:23px;">{flow}</ol>
  </div>
  <div style="background:#EEF8F5;border:1px solid #5C9B87;border-radius:12px;padding:16px 18px;margin:0 0 16px;">
    <h3 style="margin:0 0 8px;color:#1E5A49;font-size:20px;">Check before students leave</h3>
    <p style="margin:0;">{html.escape(guide.check)}</p>
  </div>
  <div style="background:#F8F2FA;border:1px solid #9563A5;border-radius:12px;padding:16px 18px;">
    <h3 style="margin:0 0 8px;color:#633D70;font-size:20px;">Support without lowering the thinking</h3>
    <p style="margin:0;">{html.escape(guide.support)}</p>
  </div>
</div>'''


G = Guide
GUIDES: tuple[Guide, ...] = (
    G(72586, "SW6 · Augmented Reality with MergeCube", 2634251, "2634251 EdPuzzle | Augmented Reality (AR) and 2634252 Activity: Lesson 1 The Basics of AR with MergeCube", "Teacher Guide: AR Lesson 1 — AR Basics and the MergeCube", "teacher-guide-ar-lesson-1-ar-basics-and-the-mergecube", "AR basics", "distinguish AR from VR and build and view a personalized AR name-tag cube in Delightex.", (("§126.19(c)(4)(C)", "essential"),), (), "Completed EdPuzzle questions and a Delightex link or file upload showing the astronaut name-tag with colors/materials, text, 3D models, a picture, and every cube side customized.", "Introduced", ("Reconnect and test the EdPuzzle with the class code.", "Have Delightex accounts signed in through Microsoft; prepare Merge Cubes or folded printable paper cubes.", "Check camera permission and install/open Merge Object Viewer and Delightex EDU before students arrive."), (("Launch", "Run the EdPuzzle and collect the one distinction the unit rests on: AR adds to the room; VR replaces it."), ("Model", "Sign in, open the cube viewer, and add text, one model, and one image to a sample face."), ("Build", "Students customize their cube faces while you solve account and camera-access problems early."), ("Test", "Partners view one another’s cube and name one AR element anchored to the cube."), ("Evidence", "Students submit the required share link or screenshot and use the every-side checklist.")), "A student can open or show the build and can point to every required customized cube side.", "Keep an AR/VR T-chart projected. Give students a labeled face-by-face planning box before they begin; accept a partner read-aloud of labels while preserving the same build requirements."),
    G(72586, "SW6 · Augmented Reality with MergeCube", 2634254, "2634254 Lesson 2: AR Worlds", "Teacher Guide: AR Lesson 2 — AR Worlds", "teacher-guide-ar-lesson-2-ar-worlds", "worldbuilding in AR", "plan and construct two related AR scenes, including a planet description and invented language.", (("§126.19(c)(4)(C)", "essential"),), (), "The paper planning worksheet and the Lesson 2 Canvas link or file upload showing two Delightex scenes. Sand Land and its SandLa language remain the worked example.", "Practiced", ("Print one planet/language planning worksheet per student.", "Open the Sand Land/SandLa example and Delightex before class.", "Have pencils and a projected scene-switching example ready."), (("Launch", "Inspect the worked example and name the details that make a world coherent."), ("Plan", "Students complete planet name, description, and invented-language planning before opening devices."), ("Model", "Build one planned object or label and explain how the two scenes stay connected."), ("Build and test", "Students construct both scenes; peers check that language and world details are visible."), ("Evidence", "Students submit the assigned evidence and use the two-scene checklist.")), "Both scenes exist, relate to one another, and visibly carry the planned world and language details.", "Use a word bank for setting, terrain, community, and language. Let students rehearse a world description orally or draw labeled plans before writing; do not let planning disappear because a student starts building early."),
    G(72586, "SW6 · Augmented Reality with MergeCube", 2634256, "2634256 Lesson 3: AR Shopping Apps", "Teacher Guide: AR Lesson 3 — Interactive AR Shopping", "teacher-guide-ar-lesson-3-interactive-ar-shopping", "interactive AR coding", "use CoBlocks to build a three-scene shopping experience in which a customer can click to buy or continue browsing.", (("§126.19(c)(1)(E)", "essential"),), (("§126.19(c)(4)(C)", "supporting"),), "Lesson 3 Canvas link or file upload showing three item scenes and functioning click behavior. A welcome screen, cart counter, and totals remain optional extensions.", "Practiced", ("Open a teacher-built click-to-buy example in Delightex/CoBlocks.", "Prepare a short visible vocabulary bank: scene, click, event, action.", "Have students identify product images/models before they build."), (("Launch", "Compare a display with an interaction: what changes after the customer clicks?"), ("Model", "Trace one click event from an item to the next scene or action."), ("Plan", "Students sketch three products/scenes and the customer path before coding."), ("Build and debug", "Students build, peer-test, and repair click-to-buy or browse behavior."), ("Evidence", "Students submit and have a partner demonstrate every click route.")), "A partner can follow the intended customer path without getting stranded in a scene.", "Keep an event-to-action sentence stem visible: ‘When the customer clicks ____, the app ____.’ Offer a three-box scene map; do not replace the student’s interaction logic with teacher code."),
    G(72586, "SW6 · Augmented Reality with MergeCube", 2634258, "2634258 Lesson 4: Interactive AR Games", "Teacher Guide: AR Lesson 4 — Interactive AR Game Design", "teacher-guide-ar-lesson-4-interactive-ar-game-design", "physics-based AR games", "create a playable AR game with a clear goal, physics, and at least ten purposeful parts.", (("§126.19(c)(1)(E)", "essential"),), (("§126.19(c)(12)(F)", "supporting"),), "Lesson 4 Canvas link or file upload showing a pinball game, marble maze, or approved arcade idea with physics, ten or more parts, and a clear goal. Space Pinball remains the target example.", "Demonstrated", ("Open the Space Pinball or comparable example.", "Project the required Physics.realTime = true; line for the script editor.", "Prepare Merge Cubes, Delightex/CoBlocks, and a game-design checklist."), (("Launch", "Play or inspect the example and name the goal, player action, rule, and feedback."), ("Model", "Add the real-time physics line and test one moving object."), ("Plan", "Students choose pinball, maze, or an approved idea and list ten parts plus a win condition."), ("Build and playtest", "Students build, play in pairs, and troubleshoot physics or collision failures."), ("Evidence", "Students submit working evidence and verify goal, physics, parts, and playability.")), "The game runs when tested, its goal is understandable without explanation, and the player can observe the physics behavior.", "Give students labeled boxes for goal, player action, rule, and feedback. Let a student explain a plan orally while a peer records labels; keep the physics troubleshooting line visible for everyone."),
    G(72587, "SW6 · Virtual Reality in Delightex", 2634260, "2634260 Lesson 1: The Basics of Delightex", "Teacher Guide: VR Lesson 1 — Delightex Basics", "teacher-guide-vr-lesson-1-delightex-basics", "VR scene construction", "build a Delightex world with five or more objects, one animated feature, a moving camera, a floor, and text labels.", (("§126.19(c)(4)(C)", "essential"),), (), "Lesson 1 Delightex share link or file upload showing the required world elements.", "Introduced", ("Confirm Delightex accounts through Microsoft and open the two example worlds.", "Prepare a projected object/animation/camera vocabulary bank.", "Have phones or headsets ready only if students will view their builds in VR mode."), (("Launch", "Compare the two example worlds and notice the required scene features."), ("Model", "Create an object, floor, label, simple animation, and camera move."), ("Build", "Students create their own world from a visible feature checklist."), ("Test", "Partners navigate a build and confirm the animation and camera work."), ("Evidence", "Students submit share link or file evidence and self-check all required features.")), "The submitted world contains every named feature and a partner can locate the animation and camera movement.", "Keep the five-feature checklist projected and pair a confident navigator with a student who needs support finding tool panels. Let students use labeled screenshots to plan before building."),
    G(72587, "SW6 · Virtual Reality in Delightex", 2634263, "2634263 Lesson 3: VR Novel", "Teacher Guide: VR Lesson 3 — VR Novel Retelling", "teacher-guide-vr-lesson-3-vr-novel-retelling", "narrative design in VR", "storyboard and build a three-scene VR retelling of a novel they actually read, then share it for feedback.", (("§126.19(c)(3)(B)", "essential"),), (("§126.19(c)(11)(B)", "supporting"),), "Storyboard worksheet plus Delightex link or file upload: three scenes from an ELAR novel, each with 6–7 objects, two animated objects, one path animation, dialogue, background, and sound; peer feedback at the showcase.", "Demonstrated", ("Print storyboard sheets and confirm an ELAR novel or a teacher-approved short list for each student.", "Open Delightex examples and prepare headphones; provide phones/headsets if available.", "Prepare a simple peer-feedback protocol and per-scene requirement checklist."), (("Launch", "Confirm a real novel and identify a three-scene narrative arc."), ("Plan", "Students storyboard on Day 1; approve the book and scenes before anyone builds."), ("Model", "Demonstrate a scene’s objects, path animation, dialogue, background, and sound."), ("Build and revise", "Across Days 2–4, students build and conference against the per-scene checklist."), ("Showcase", "On Day 5, peers give feedback; students revise and submit storyboard plus VR evidence.")), "Each scene advances the selected novel, and the final submission includes both an accessible planning artifact and the working VR evidence.", "Offer sentence stems for narrative transitions and a storyboard that permits sketches, labels, or dictated planning. A student may choose a teacher-approved familiar novel; do not turn book selection into a multi-day barrier."),
    G(72588, "SW6 · Pitching and Presenting", 2634265, "2634265 EdPuzzle | The Art of Logo Design", "Teacher Guide: Pitching Lesson 0 — Logo Design Launch", "teacher-guide-pitching-lesson-0-logo-design-launch", "logo design principles", "identify design choices they will apply to a personal logo.", (), (), "EdPuzzle completion (0 points). The current Canvas assignment has no student-facing description, so this guide supplies the facilitation context rather than claiming independent TEKS evidence.", "Preparation lesson; no TEKS claim", ("Reconnect and test the EdPuzzle with the class code; turn on captions and preview the questions.", "Project two recognizable, simple logos and prepare the three-color constraint for tomorrow.", "Keep the current module guide’s EdPuzzle fallback available if the external tool is unavailable."), (("Launch", "Show one recognizable logo and ask what it communicates without words."), ("Frame", "Explain why the video comes before making a personal logo and preview tomorrow’s name, icon, and three-color rule."), ("Watch and respond", "Students complete the video questions with captions and rewind available."), ("Debrief", "Connect two video design choices to the personal-logo criteria."), ("Evidence", "Verify EdPuzzle completion and collect one design intention for the next lesson.")), "Every student has completed the video or has a documented fallback path and can name one choice they will make in their own logo.", "Use captioning, replay, and a visual logo comparison. Allow a student to say or draw the design intention rather than requiring a written sentence."),
    G(72588, "SW6 · Pitching and Presenting", 2634266, "2634266 Lesson 1: Personal Logo and Brand in Adobe Express", "Teacher Guide: Pitching Lesson 1 — Personal Logo and Brand", "teacher-guide-pitching-lesson-1-personal-logo-and-brand", "personal visual identity", "design a personal logo with their name, one meaningful icon, and no more than three colors.", (("§126.19(c)(12)(H)", "essential"),), (), "Completed Google Docs worksheet plus Adobe Express share link. This is the current 5-point minor assignment.", "Practiced", ("Test Adobe Express through ClassLink and the Google Docs worksheet hand-back path.", "Open a few logo examples and prepare a personal-icon brainstorm/word bank.", "Have a paper sketch option ready before students search the asset library."), (("Launch", "Identify the name, icon, and color choices in an earlier career or identity example."), ("Model", "Sketch then create a simple name, meaningful icon, and three-color logo in Adobe Express."), ("Plan", "Students select an icon tied to themselves and rough-sketch before opening assets."), ("Create and conference", "Students build while you check relevance and stop sticker-library drift."), ("Evidence", "Students paste the share link in the worksheet, submit, and peer-check name/icon/color limits.")), "The teacher can open the submitted share link, and the logo meets the name, meaning, and three-color requirements.", "Keep a personal-trait word bank and the stem ‘My icon represents ____ because ____.’ Allow sketching, shapes, labels, or speech-to-text; do not grade drawing skill."),
    G(72588, "SW6 · Pitching and Presenting", 2634267, "2634267 Lesson 2: Personal Brand Video", "Teacher Guide: Pitching Lesson 2 — Personal Brand Video", "teacher-guide-pitching-lesson-2-personal-brand-video", "personal narrative and presentation", "create a seven-or-more-slide personal-brand video using their logo, meaningful images, chosen music, and ten ‘I am…’ statements.", (("§126.19(c)(11)(A)", "essential"),), (("§126.19(c)(12)(H)", "supporting"),), "Google Docs worksheet with a share link to the finished Adobe Express or Canva video. This is the current 100-point major assignment.", "Demonstrated", ("Provide headphones, the Lesson 1 logo, the ‘I am…’ brainstorm, and checked student examples.", "Test Adobe Express, Canva, the Google Docs worksheet, and a non-owner share-link opening.", "State music-use expectations and remind students to replace any default track."), (("Launch", "View one student example and identify how image, music, and text work together."), ("Model", "Import a logo, make one meaningful slide, replace default music, and publish a shareable result."), ("Plan", "Students sequence ten statements and choose images/music before building."), ("Create and revise", "Students build across two periods while you conference for slide count, meaningful images, and changed music."), ("Evidence", "Test one submitted share link as a viewer, then submit through the worksheet.")), "The link opens for the teacher and the video contains seven or more slides, the student’s logo, meaningful images, chosen music, and ten identity statements.", "Give a slide-planning grid and sentence stems for ‘I am…’ statements. Students may record or select text-supported music choices, but the evidence remains a coherent digital composition."),
    G(72589, "SW6 · Capstone", 2634269, "2634269 Tech for Good Capstone", "Teacher Guide: Tech for Good Capstone — Research, Build, Test, and Showcase", "teacher-guide-tech-for-good-capstone-research-build-test-and-showcase", "project-dependent technology-for-good solution", "research a cause, plan, create, test, refine, and present one chosen technology project.", (("§126.19(c)(3)(B)", "essential"),), (("§126.19(c)(5)(B)", "supporting"), ("§126.19(c)(9)(C)", "supporting")), "Selected project artifacts and portfolio record: one of six builds (MakeCode Arcade, ThingLink 360, TinkerCAD print, Adobe Express/Canva campaign, Delightex AR, or Piskel animation), research evidence, and final reflection/submission.", "Demonstrated", ("Decide which of the six options the class can genuinely support before Day 1.", "Test matching portfolio Google Doc copy links, Research Helper, Newsela/Britannica logins, and tool access.", "Book showcase space; confirm printer queue or AR/cube access if those options remain open."), (("Launch and choose", "Days 1–2: introduce the cause/project menu, name tool limits honestly, choose a project, and use the Research Helper for credible-source notes."), ("Plan", "Days 3–4: model a project-specific plan and approve scope, sources, and artifact list."), ("Build", "Days 5–8: use protected work blocks, tool-specific mini-conferences, and documented troubleshooting."), ("Test and refine", "Day 9: gather peer or user feedback against project criteria and revise the product."), ("Showcase and evidence", "Day 10: present, complete portfolio/reflection, and verify that artifact links open.")), "Each student has an approved scope, real-source evidence, a working artifact or documented limitation, and a final link/file that opens for the teacher.", "Offer a short menu rather than six unsupported choices. Use research stems and a source-record table; permit students to plan with sketches, audio notes, or labeled screenshots while holding the same research, build, test, and reflection expectations."),
    G(72589, "SW6 · Capstone", 2634271, "2634271 Xello Check-in: Scholarship Profile", "Teacher Run Card: Capstone Close — Scholarship Profile Check-in", "teacher-run-card-capstone-close-scholarship-profile-check-in", "scholarship exploration", "complete the Xello Scholarship profile, filter matches by grade, and document the result.", (), (), "Screenshot of filtered scholarship matches uploaded to Canvas. This is an operational check-in, not an independent TEKS demonstration.", "Operational check-in; no TEKS claim", ("Test Xello through ClassLink and prepare one projected navigation example.", "Demonstrate a screenshot and upload without displaying student personal information to the class.", "Reserve approximately 20 minutes after the capstone work is complete."), (("Launch", "Explain that this is a short closing check-in, not a capstone product or grade."), ("Model", "Navigate Goals & Plans, complete the profile, and filter matches by grade."), ("Do", "Students complete and filter independently."), ("Verify", "Check a filtered-results screen, not a student’s private responses, before upload."), ("Evidence", "Students upload a screenshot and resolve missing-profile or account issues.")), "The Canvas submission contains a readable screenshot of grade-filtered Xello matches.", "Provide a click-path card with screenshots and seat students so private search results are not projected. Read navigation steps aloud and allow a trusted adult to help with account access without completing the profile for the student."),
    G(72590, "SW6 · Closing: ePortfolio and Post Survey", 2634273, "2634273 Create an ePortfolio", "Teacher Guide: Closing Lesson 1 — Publish the ePortfolio", "teacher-guide-closing-lesson-1-publish-eportfolio", "digital portfolio publishing", "curate and publish one Adobe Express portfolio page that communicates their work to an authentic audience.", (("§126.19(c)(8)(B)", "essential"),), (("§126.19(c)(11)(A)", "supporting"), ("§126.19(c)(11)(B)", "supporting"), ("§126.19(c)(12)(H)", "supporting")), "Published Adobe Express webpage share link with name/title and meaningful image, short introduction, a photo or link and description for every project, and the personal logo from Pitching and Presenting.", "Demonstrated", ("Gather portfolio work from Week 0, Portfolio Part 2, Capstone, and the personal-logo lesson.", "Test Adobe Express through ClassLink and open student ePortfolio examples.", "Prepare a published-versus-draft-link demonstration and a submission checklist."), (("Launch", "Open an example and identify audience, evidence, and visual choices."), ("Model", "Create a title, introduction, and project entry; publish and contrast a published URL with a private draft link."), ("Curate", "Students gather work and plan page sections before building."), ("Build and check", "Students create pages while you open an early link as a non-owner to catch unpublished sharing."), ("Evidence", "Students submit a published link and check every required portfolio element.")), "The submitted page opens for the teacher and contains the required introduction, evidence/descriptions, and personal logo.", "Use a portfolio checklist with icons and a model project entry. Allow students to dictate an introduction or use short labeled captions, but require them to choose and explain their own evidence."),
    G(72590, "SW6 · Closing: ePortfolio and Post Survey", 2634274, "2634274 Student: Post-Survey", "Teacher Run Card: Closing Lesson 2 — Post-Survey", "teacher-run-card-closing-lesson-2-post-survey", "year-end reflection and data collection", "complete the post-survey accurately and independently.", (), (), "Completed ungraded Canvas post-survey. It is a course-measurement activity, not an independent TEKS demonstration.", "Operational check-in; no TEKS claim", ("Test the survey on a student device and reserve protected in-class time.", "Prepare a brief privacy and purpose statement.", "Use a completion tracker that does not expose survey responses."), (("Launch", "Explain why the survey matters and that it is not graded."), ("Orient", "Show where to open it and state the expected completion time."), ("Respond", "Students complete it independently."), ("Verify", "Check completion status, not individual answers."), ("Close", "Thank students and give unfinished respondents a clear completion path before they leave.")), "Canvas records a completed survey submission; no response content is publicly discussed or graded.", "Read directions aloud, provide quiet time, and offer accessibility support for navigation. Preserve privacy: adults may help students access the survey but should not influence their responses."),
    G(72591, "Enrichment · Stop Motion", 2634275, "2634275 Storytelling | Stop Motion", "Teacher Guide: Stop Motion Overview — Six-Day Film Project", "teacher-guide-stop-motion-overview-six-day-film-project", "stop-motion production", "plan, animate, edit, and submit a 30–60 second original film.", (("§126.19(c)(3)(B)", "essential"),), (("§126.19(c)(11)(A)", "supporting"), ("§126.19(c)(11)(B)", "supporting")), "Final .mp4 or .mov, plot diagram, storyboard, and the current 40-point rubric evidence for structure, storyboard, technical quality, creativity, and effort.", "Optional route — demonstrated when assigned", ("Confirm Stop Motion Studio, devices/cameras, storage, and the upload route.", "Show a short exemplar and prepare a 6–7-day calendar.", "Set material, safety, and cleanup expectations for props, lighting, and sound."), (("Launch", "Show a short exemplar and unpack the final rubric."), ("Frame", "Map the six-day sequence and production roles/material expectations."), ("Plan", "Students choose genre, characters, and a manageable conflict."), ("Produce", "Establish daily checkpoints for planning, storyboarding, filming, editing, and submission."), ("Evidence", "Confirm final video format and milestone dates before work begins.")), "Students can name the required intermediate artifacts and final video format before beginning production.", "Keep the rubric visible and allow clay, paper, recycled items, toys, collage, or digital labels. Make material complexity optional; the assessed evidence is story and production quality, not access to expensive props."),
    G(72591, "Enrichment · Stop Motion", 2634276, "2634276 EdPuzzle | Intro to Stop Motion Process", "Teacher Guide: Stop Motion Lesson 0 — Process Video and Setup", "teacher-guide-stop-motion-lesson-0-process-video-and-setup", "stop-motion workflow", "identify the production process before planning their own film.", (), (), "Completed 10-question EdPuzzle; captions and rewind are permitted and there is no separate file upload. This is preparation, not an independent TEKS demonstration.", "Optional route — preparation lesson; no TEKS claim", ("Reconnect the external-tool EdPuzzle, select the reusable video, set captions/skipping, and test it in Student View.", "Remove the teacher-only setup box from the student assignment before the route is published.", "Keep the original video and question list ready as a fallback."), (("Launch", "State the production question students should answer while watching."), ("Teacher setup", "Confirm the external-tool assignment actually opens for a student before releasing it."), ("Watch and respond", "Students complete the 10 questions with captions and rewind available."), ("Debrief", "Map the video process to plan, plot, storyboard, film, and final edit."), ("Evidence", "Verify EdPuzzle completion and collect one filming-quality takeaway.")), "Every assigned student can access the player or the documented fallback and has completed the response activity.", "Turn captions on by default and allow replay. Give students a pictured process strip so language load does not hide the production sequence."),
    G(72591, "Enrichment · Stop Motion", 2634277, "2634277 1. Plan Your Story", "Teacher Guide: Stop Motion Day 1 — Story Plan", "teacher-guide-stop-motion-day-1-story-plan", "story ideation", "define a genre, character, setting, conflict, and resolution for an animatable story.", (("§126.19(c)(3)(B)", "essential"),), (), "Paragraph, list, or mind map. The current checkpoint requires a clear main character, setting/conflict, and timely upload.", "Optional route — practiced when assigned", ("Prepare genre/plot prompt cards, a story-plan template, and a filmable-scope example.", "Keep language stems visible for character, setting, conflict, and resolution.", "Confirm the preferred Canvas submission route."), (("Launch", "Compare a filmable story idea with one that is too large for a short animation."), ("Model", "Fill a sample plan with character, setting, conflict, and resolution."), ("Plan", "Students draft in a paragraph, list, or mind-map format."), ("Conference", "Narrow scope and verify a visible conflict and resolution."), ("Evidence", "Students submit the plan and use the checkpoint before Day 2.")), "Every plan identifies a character, setting, conflict, and resolution that can be shown in a short film.", "Use the stem ‘My character wants ____, but ____.’ Allow speech-to-text, a labeled sketch, or a mind map; preserve the need for a complete story decision."),
    G(72591, "Enrichment · Stop Motion", 2634278, "2634278 2. Plot Diagram Story", "Teacher Guide: Stop Motion Day 2 — Plot Diagram", "teacher-guide-stop-motion-day-2-plot-diagram", "narrative structure", "map exposition, rising action, climax, falling action, and resolution.", (("§126.19(c)(3)(B)", "essential"),), (), "Plot diagram submitted as a photo, Google Slides/Docs, or text. The current checkpoint requires all five parts, a coherent conflict, and a beginning, middle, and end.", "Optional route — practiced when assigned", ("Prepare a five-part plot visual, a familiar-story model, and paper or Google template options.", "Post bilingual plot vocabulary and sentence stems where students work.", "Check the current external-tool submission path if using a template."), (("Launch", "Retell a familiar story using the five plot parts."), ("Model", "Complete one plot diagram from the prior day’s story plan."), ("Map", "Students draft all five stages."), ("Partner check", "Partners identify the climax and test the conflict sequence."), ("Evidence", "Students submit in one allowed format and flag revisions for the storyboard.")), "The submission names all five plot parts and shows a coherent beginning, middle, and end.", "Use a color-coded plot mountain and offer word/phrase cards. Let students explain the plot orally before recording it; do not accept a storyboard in place of the explicit five-part structure."),
    G(72591, "Enrichment · Stop Motion", 2634279, "2634279 3. Storyboard Scenes", "Teacher Guide: Stop Motion Day 3 — Storyboard", "teacher-guide-stop-motion-day-3-storyboard", "visual sequencing", "plan 6–12 ordered scenes with actions, props, and movement notes.", (("§126.19(c)(3)(B)", "essential"),), (), "A 6–12-scene storyboard. The current checkpoint requires ordered scenes and clear notes about what happens.", "Optional route — practiced when assigned", ("Prepare storyboard frames, an exemplar, pencils/markers, and action/movement vocabulary.", "Offer a typed, dictated, or labeled-sketch storyboard route.", "Plan a materials-list check before filming begins."), (("Launch", "Notice how a storyboard predicts camera and action changes."), ("Model", "Turn one plot moment into two or three scenes."), ("Storyboard", "Students map 6–12 ordered scenes."), ("Conference", "Check order, prop needs, and manageable movement."), ("Evidence", "Students submit the storyboard and generate a materials list.")), "The storyboard has at least six ordered scenes and makes the action, movement, and materials understandable to a production partner.", "Give students a frame-by-frame template with word bank and arrows for movement. Drawing skill is not the measure; labels, photos, stick figures, or dictated descriptions are valid planning evidence."),
    G(72591, "Enrichment · Stop Motion", 2634280, "2634280 4. Film", "Teacher Guide: Stop Motion Days 4–6 — Film, Edit, and Submit", "teacher-guide-stop-motion-days-4-6-film-edit-and-submit", "animation production", "create, edit, and publish a readable stop-motion film with stable, well-lit imagery and sound or titles as appropriate.", (("§126.19(c)(11)(A)", "essential"),), (("§126.19(c)(11)(B)", "supporting"),), "Final 30–60 second .mp4 or .mov. The project rubric assesses technical quality, story, creativity, and effort.", "Optional route — demonstrated when assigned", ("Prepare Stop Motion Studio, charged devices, tripods/books, sets/props, and consistent lighting.", "Set up a quiet voiceover area and approved sound options.", "Test final export/upload and keep the rubric visible throughout production."), (("Launch", "Demonstrate stable framing and a small movement increment."), ("Model", "Capture a short sequence, add sound or title, and export."), ("Produce", "Students build sets and film with daily frame and quality checks."), ("Review and revise", "Peers check stability, lighting, story clarity, and sound; students re-shoot where needed."), ("Evidence", "Students export, upload the final film, and self-score against the rubric.")), "The submitted video opens, runs 30–60 seconds, and gives the teacher enough evidence to score story and technical-quality criteria.", "Provide stable-camera stations and a shot checklist. Students may use simple props, still captions instead of voiceover, and a peer camera assistant; keep story clarity and technical stability as the common standard."),
)


def course_modules(canvas: Canvas) -> dict[int, dict]:
    return {row["id"]: row for row in canvas.paged(f"/courses/{COURSE_ID}/modules?per_page=100")}


def item_map(canvas: Canvas, module_id: int) -> dict[int, dict]:
    return {
        row["id"]: row
        for row in canvas.paged(f"/courses/{COURSE_ID}/modules/{module_id}/items?per_page=100")
    }


def pages_by_title(canvas: Canvas) -> dict[str, dict]:
    """Use Canvas's returned URL, rather than trying to reproduce its slugifier.

    Canvas preserves ordinary words such as ``the`` and normalizes punctuation in
    ways that are not part of the public Pages API contract. Title is unique for
    this managed guide set, and the returned URL is the stable page identifier.
    """
    return {page["title"]: page for page in canvas.paged(f"/courses/{COURSE_ID}/pages?per_page=100")}


def preflight(canvas: Canvas) -> None:
    course = canvas.get(f"/courses/{COURSE_ID}")
    if course.get("name") != "Irving ISD VILS 2027 Template":
        raise RuntimeError(f"Refusing unexpected course: {course.get('id')} {course.get('name')!r}")
    modules = course_modules(canvas)
    for guide in GUIDES:
        module = modules.get(guide.module_id)
        if not module or module.get("name") != guide.module_name:
            raise RuntimeError(f"Refusing unexpected module for {guide.title}")
        target = item_map(canvas, guide.module_id).get(guide.before_item_id)
        if not target:
            raise RuntimeError(f"Missing target item {guide.before_item_id} for {guide.title}")
    print(f"PRE-FLIGHT course {course['id']} {course['name']}: {len(GUIDES)} guide targets verified")


def apply(canvas: Canvas) -> None:
    pages = pages_by_title(canvas)
    for guide in GUIDES:
        index_row = pages.get(guide.title)
        existing = (
            canvas.get(f"/courses/{COURSE_ID}/pages/{index_row['url']}")
            if index_row is not None
            else None
        )
        if existing is None:
            created, _ = canvas.request(
                "POST",
                f"/courses/{COURSE_ID}/pages",
                {
                    "wiki_page[title]": guide.title,
                    "wiki_page[body]": guide_body(guide),
                    "wiki_page[editing_roles]": "teachers",
                    "wiki_page[published]": "false",
                    "wiki_page[notify_of_update]": "false",
                },
            )
            pages[guide.title] = created
            page_url = created["url"]
            print(f"CREATE PAGE {page_url}")
        elif MARKER not in (existing.get("body") or ""):
            raise RuntimeError(f"Refusing to overwrite non-managed page {existing.get('url')}")
        else:
            page_url = existing["url"]
            print(f"KEEP PAGE {page_url}")

        items = item_map(canvas, guide.module_id)
        target = items[guide.before_item_id]
        if any(item.get("type") == "Page" and item.get("page_url") == page_url for item in items.values()):
            print(f"KEEP MODULE ITEM {page_url}")
            continue
        canvas.request(
            "POST",
            f"/courses/{COURSE_ID}/modules/{guide.module_id}/items",
            {
                "module_item[title]": guide.title,
                "module_item[type]": "Page",
                "module_item[page_url]": page_url,
                "module_item[position]": str(target.get("position", 1)),
            },
        )
        print(f"ADD MODULE ITEM {page_url} before {guide.before_item_id}")


def verify(canvas: Canvas) -> None:
    failures: list[str] = []
    pages = pages_by_title(canvas)
    for guide in GUIDES:
        index_row = pages.get(guide.title)
        page = canvas.get(f"/courses/{COURSE_ID}/pages/{index_row['url']}") if index_row else None
        page_url = page.get("url") if page else guide.slug
        if not page or MARKER not in (page.get("body") or ""):
            failures.append(f"missing or unmanaged page {guide.title}")
            continue
        body = page["body"]
        for code, _ in (*guide.essential, *guide.supporting):
            if code not in body or TEKS[code] not in body:
                failures.append(f"missing TEKS wording {code} in {page_url}")
        items = item_map(canvas, guide.module_id)
        guide_item = next((row for row in items.values() if row.get("page_url") == page_url), None)
        target = items.get(guide.before_item_id)
        if not guide_item or not target or guide_item.get("position", 0) >= target.get("position", 0):
            failures.append(f"bad module placement for {page_url}")
    if failures:
        raise RuntimeError("\n".join(failures))
    print(f"VERIFY {len(GUIDES)} daily guide pages and module placements")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true", help="Create pages and module items after preflight.")
    args = parser.parse_args()
    canvas = Canvas()
    preflight(canvas)
    if args.apply:
        apply(canvas)
        verify(canvas)
    else:
        for guide in GUIDES:
            print(f"DRY-RUN {guide.module_name}: {guide.title} → before {guide.target}")


if __name__ == "__main__":
    main()
