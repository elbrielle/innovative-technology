# Coding Foundations Retrofit — Implementation Record

Original staging date: 2026-08-22

Consensus source revision: 2026-08-23

Canvas course: `23402`

Current release decision: **HOLD — final four-lens rereview in progress**

## Current-state boundary

The first 2026-08-22 staging build failed all four independent review lenses because several TEKS claims exceeded student authorship, the new teacher guides were not end to end, grading and quiz evidence were invalid or ambiguous, promised scaffolds were absent, and student/Spanish surfaces were incomplete.

On 2026-08-23, the consensus correction was rebuilt and applied to the same Drive and Canvas identities. The six new Text-Code Bridge module items remain **unpublished**, and the existing RVR publication state remains unchanged. The normal course sync regenerated the public-safe snapshot and mirror and passed live readback. This is corrected staging, not a publication decision: the PR remains draft and the review decision remains HOLD until all four final rereviews return GO or GO WITH FIXES.

## Seven-checkpoint evidence model

The replacement Passport sequence separates evidence that the first five-page version combined:

1. Decompose + literal-test before blocks.
2. Analyze a shared route pattern, explain iteration, and generalize; use Hour of Code only for transfer, not as a guaranteed variable/data-type source.
3. Predict, run controlled tests, and revise code plus pseudocode.
4. Game Plan: feature goal, WHEN/SHOULD statement, pseudocode, first test result, and evidence-based revision.
5. Trace + Repair: read supplied text code, predict the full nested-loop result, diagnose one boundary error, and repair it.
6. Create + Improve: document the emergency-layout problem and constraints, author/complete typed variables and operations, complete both nested loops, test, and make a required improvement.
7. RVR Team Plan: problem, two possible solutions, selected solution, roles, timeline, and pseudocode. The existing RVR mission sheet separately retains the sketch, robot ID, first/final runs, revision, and reflection.

The same response must not be duplicated across Passport 7 and the RVR mission sheet.

## Defensible TEKS status

| Learning moment | Demonstrated | Practiced | Evidence boundary |
| --- | --- | --- | --- |
| Intro Day 1 / Passport 1 | (1)(E) | (1)(A) | The Code.org route is not automatically a real-world problem, so (1)(A) remains practice. |
| Intro Day 2 / Passport 2 | (1)(F) through the shared example | (1)(B), (1)(C) | Do not claim variables/data types from an arbitrary Hour of Code choice. |
| Intro Day 3 / Passport 3 | (1)(E), (2)(C) | — | Requires three complete controlled-test records and a matching pseudocode revision. |
| Game Remix / Passport 4 | (2)(C), (3)(B) | (1)(E) | Requires the recorded feature test and revision, not planning alone. |
| Text Code Day 1 / Passport 5 | (2)(C) | (2)(A), (2)(B) | Identifying supplied variables and loops is practice; the independent repair demonstrates improvement. |
| Text Code Day 2 / Passport 6 | (2)(A), (2)(B), (2)(C) when every threshold is met | (1)(A), (1)(E) | Supplied sprite/API code earns no authorship credit. Students must author typed declarations/operations and both complete loop structures, then show a required revision. |
| RVR / Passport 7 + mission sheet | (1)(D), (1)(E), (2)(C) only through combined evidence | — | Passport supplies the collaborative plan; mission sheet supplies physical-run and revision evidence. |

## Source behavior encoded in the replacement apply script

- Student bridge pages use bilingual **Topic / I can / Show Your Learning / Now / Next / Done** language. They contain no statutory lists or third-person curriculum wording.
- Teacher bridge guides contain Topic, objective, exact essential/supporting TEKS, I/P/D evidence status, DOL threshold, prerequisite, a timed 50–55 minute sequence, expected answers, misconceptions, scaffolds, recovery, and absence route.
- Day 1 remains a 25-point minor assignment with five explicit five-point evidence categories.
- Day 2 remains a 100-point major assignment. `Meets` earns the full 25 points in each criterion; `No Evidence` earns zero. Optional extension is not required for full credit.
- The Classic Quiz remains an eight-point knowledge check. Every question and feedback route is bilingual. Its description explicitly states that recognition questions do not replace performance evidence for construction or improvement.
- The script removes `online_url` from both bridge assignments and removes full-name/public-share assumptions from the retrofitted Game Remix body and rubric.
- Game Remix retains 100 total points while Passport 4 planning/testing is scored within existing Build and Testing and Screenshot and Reflection criteria.
- Intro and RVR assignments retain existing total points with explicit point-preserving evidence maps.
- Facilitator guides link the Day 1 highlighted bug route, the Day 2 student-authorship scaffold, Passport formats, deck, an explicitly labeled alternate finished teacher solution, and post-diagnosis reference images. Corrected code/results are teacher-only reveals after student work.

## Rerun behavior

The previous script skipped an existing Day 2 rubric and existing quiz questions. The revised source:

- resolves the rubric id from the assignment's `rubric_settings`, reads that exact rubric with associations, then updates all four criteria and ratings in place;
- refuses ambiguous criterion/rating-count drift instead of creating a duplicate rubric;
- updates the existing eight quiz questions by stable `Q1` through `Q8` positions, including answers and feedback;
- refuses duplicate, unnumbered, or unexpected stale questions;
- keeps module/page/assignment identities and publication states;
- rereads and verifies rubric points, submission types, bilingual feedback, privacy corrections, ordering, scope-and-sequence wording, publication state, and file sizes after each live apply.

The feedback fields follow the current Canvas Classic Quiz API: `question[correct_comments]`, `question[incorrect_comments]`, `question[neutral_comments]`, and answer-level `answer_comments`. Existing questions use the documented `PUT /courses/:course_id/quizzes/:quiz_id/questions/:id` route. Existing rubrics use the documented `PUT /courses/:course_id/rubrics/:id` route with the rubric-association identity.

Current primary references:

- [Canvas Quiz Questions API](https://canvas.instructure.com/doc/api/quiz_questions.html)
- [Canvas Rubrics API](https://developerdocs.instructure.com/services/canvas/resources/rubrics)
- [TEA Chapter 126, Subchapter B](https://tea.texas.gov/laws-and-rules/sboe-rules-tac/sboe-tac-currently-effect/ch126b.pdf)

## Completed staging verification

- `python3 -m py_compile scripts/apply_coding_foundations_retrofit.py`
- deterministic HTML assertions for both student and teacher bridge bodies;
- assertions that student bridge bodies contain all required plain-language sections and no statutory codes/`Students will` wording;
- rubric payload assertions for four criteria, `Meets = 25`, and `No Evidence = 0`;
- bilingual quiz tuple/feedback assertions;
- assertions that `online_url` is absent from both bridge assignments and the retrofitted Game Remix assignment, whose rubric now uses only a class-safe alias.
- English and Spanish Passports rebuilt to 10 pages each, rendered page by page, and audited at zero high/medium/low accessibility findings.
- 57-slide PowerPoint rebuilt with the final C1–C7 navigation, neutral pre-investigation loop model, student-authored Day 2 loops, equal-evidence support routes, and delayed Day 1 reveal. It was rendered and inspected slide by slide, passed the overflow test, retained actual PPTX alt text, and contains `[Sources]` in 57/57 speaker-note records.
- The same Drive IDs were updated in place. Connector readback found 249 paragraphs and Checkpoint 7 in each Passport and 57 slides in the native Google deck. Native Slides alt text was restored with `updatePageElementAltText` and verified on both image object IDs. Exported Drive PDFs rendered as 10 English pages, 10 Spanish pages, and 57 slides without conversion defects.
- Canvas apply verified 10 protected retrofits, the ordered six-item unpublished tail, 11 reviewed current asset identities, privacy-safe Game Remix grading/upload, four Day 2 rubric criteria, and eight bilingual quiz questions with feedback.
- Program Scope + Sequence now names the two-period Skillmap/Remix arc and two-period Text-Code Bridge. The daily-contract ledger now includes both new facilitator guides, and the site verifier accounts for 156 guides.
- `python3 scripts/sync_course.py` passed snapshot, generated-site, public-asset, and live-Canvas agreement: 34 modules, 509 items, 201 public files, and zero unresolved links.
- Desktop and 390 px browser checks found one curriculum body per new page, no student-facing statutory TEKS on student routes, and no horizontal overflow.

## Remaining merge gate

1. Complete the independent final teacher, district, student, and design/language rereviews against the rendered Drive, Canvas-snapshot, and generated-site state.
2. Record their evidence and consensus in `docs/reviews/coding-foundations-retrofit-2026-08-23.md`.
3. Require every decision to be `GO` or `GO WITH FIXES`, then pass `scripts/verify_curriculum_review_gate.py` and CI before requesting merge.

## Publication-only gates

After a corrected source merge and unpublished Canvas staging pass, publication still requires a managed-Chromebook rehearsal, teacher rehearsal, small student pilot, and signed-in Student View verification of the published routes. Those gates do not authorize changing the intentionally preserved publication state of the existing RVR assignment.
