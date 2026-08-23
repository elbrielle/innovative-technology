# Coding Foundations Retrofit — Implementation Record

Implementation date: 2026-08-22  
Canvas course: `23402`  
Status: implemented in unpublished Canvas staging; classroom pilot and signed-in Student View remain

## What changed

Pseudocode was folded into five existing learning moments instead of becoming a separate unit:

1. Intro to CS Day 1 — decompose a goal and literal-test precise pseudocode.
2. Intro to CS Day 2 — identify patterns, iteration, variables, data types, and operations.
3. Intro to CS Day 3 — predict, test, change one element, and revise pseudocode.
4. Video Game Design Lesson 2 — plan a feature with `WHEN` and `SHOULD` logic before editing.
5. RVR Day 1 — assign roles, build a timeline, literal-test robot pseudocode, revise, and transfer the process.

Each teacher guide and student assignment was updated in place. Existing points, submission routes, publication state, assignment groups, rubrics, IDs, and module positions were preserved.

## Explicit text-code bridge

The Video Game Design module is now named **SW3 · Video Game Design + Text Code** and contains an unpublished six-item tail:

1. Text-Code Bridge (2 days)
2. Teacher Guide: Text-Code Bridge Day 1 — Trace, Predict + Repair
3. Lesson 3: Text Code — Trace, Predict + Repair
4. Teacher Guide: Text-Code Bridge Day 2 — Change the Grid with Purpose
5. Lesson 4: Text Code — Emergency Supply Grid
6. Checkpoint: Text Code + Nested Loops

Students work in MakeCode Arcade JavaScript. Day 1 requires a prediction of a `3 × 4` grid, observation of the intentional `3 × 3`/score `9` boundary bug, one-word repair, and proof of the corrected `3 × 4`/score `12` result. Day 2 requires a purposeful grid modification using meaningful string, number, and Boolean variables, operations on values, and nested loops that address row and column subproblems.

The Day 2 assignment has a four-criterion, 100-point rubric. The Classic Quiz has eight one-point questions, unlimited attempts, highest score kept, and remains unpublished.

## Teacher and student assets

- English Google Passport: `1fJGKVRLazdLojOlnwIUrpb9xfv5X9ukQRYdUPjRtuGc`
- Spanish Google Passport: `1pcosaTw_XiBPEq8G4j1YoyoF6ZhLHTA_pX3yq2hveYE`
- Editable Google Slides teacher deck: `1oi0ZohdSAbD5q0gtJlWyse3yTv-qbzLKumGedSkgA0s`
- Canvas files: `3229477`–`3229487`

The Passports are also available as DOCX/PDF fallbacks, the deck as PPTX, and the text-code bridge as plain-text starter files. The MakeCode recovery route requires no account or imported project file: create a new project, switch to JavaScript, paste the starter text, and run.

## Verification completed

- All 10 protected existing bodies matched their locked preimplementation checksums before mutation.
- Canvas reread verified all 10 marked retrofits and preserved publication states.
- The new module tail is in the intended order and all six items are unpublished.
- The Day 2 rubric contains four criteria; the checkpoint contains eight questions.
- All 11 Canvas upload records match the reviewed source filenames and byte sizes.
- English and Spanish Passports were rendered and visually reviewed page by page; accessibility audits reported no findings.
- The 26-slide teacher deck was rendered and visually reviewed slide by slide; overflow testing passed.
- The live MakeCode program compiled and displayed the expected `3 × 4` grid and score `12`.
- `sync_course.py` passed snapshot, generated-site, public-file, and live-Canvas parity with zero unresolved links.
- Signed-in Canvas teacher view rendered both assignments, the linked Canvas/Google resources, the loaded MakeCode images, Day 2's 100-point value, all four rubric criteria and rating levels, and the 8-point quiz settings.
- Signed-in Canvas Student View confirmed that the unpublished SW3 staging module and both new lessons are hidden from students.

## Remaining pilot gates

- When the owner approves publication, publish the module/items and immediately repeat signed-in Student View on both new lessons before assigning them.
- Confirm the starter-download, Google `/copy`, image, submission, rubric, and quiz routes on a managed Chromebook.
- Run one teacher rehearsal and one small student pilot; record timing, misconceptions, accessibility issues, and recovery failures.
- Publish only after those checks pass. Do not alter the intentionally preserved publication state of the existing RVR assignment.
