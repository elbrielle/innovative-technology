# Xello Week 1 Parity — Four-Lens Review

Review date: 2026-08-24

Review status: GO FOR MERGE; CANVAS ITEMS REMAIN UNPUBLISHED

Teacher implementation: GO
District curriculum: GO
Student experience: GO
Design and language: GO
Consensus: GO

## Reviewed scope

- live Canvas course 23402, Week 1 module 72564, assignment 1183431, and assignment module item 2633997;
- new teacher-only Canvas page and module item 2665839, slug facilitator-guide-xello-matchmaker-personality-style-and-learning-style;
- 19-slide teacher deck 1zWB_nVYGl8bEv7ls6zyJbdZeAu1NwEyJvFgeQxn8U6A, revision hDb3P0xbfqk_Zg;
- 16-slide student walkthrough 1MtqwOTdRikzDPNTy_6gUEyg7VgTH8GUJxUTXxKWH868, revision oardIRvZQoMNdQ;
- bilingual Canvas student assignment, complete teacher facilitator guide, five-point scoring contract, privacy-safe screenshot/upload route, pacing, recovery, absence, and accommodation routes;
- Canvas-first apply/readback script, unit tests, daily-learning-contract ledger, generated public mirror, and live parity verification.

Both decks are shared as district-domain reader files for irvingisd.net. The student deck physically excludes the teacher route and stop cards.

## Independent findings

### Teacher implementation

The first review returned HOLD: the deck could imply two reflections, the multi-day route did not account for the rest of each period, five points lacked an allocation, and screenshot/login recovery was incomplete. After those fixes, the reviewer found one remaining privacy-critical error: Ctrl + Show windows captures a Chromebook full screen rather than a selected region.

Final decision: GO. The package now uses Shift + Ctrl + Show windows / Mayús + Ctrl + Mostrar ventanas, collects exactly three result screenshots and one surprise-or-confirmation reflection, assigns all five points, names retained Ready Set Design work, and provides complete access, capture, upload, recovery, accommodation, and absence routes.

### District curriculum

The first review returned HOLD: the proposed guide used a noncanonical learning-contract marker, UDL action/expression lacked an equivalent route, the apply path did not fail closed on assignment settings, scoring was underdefined, and the student link opened a teacher-only slide.

Final decision: GO. The guide uses the canonical Daily Learning Contract marker, makes no cosmetic Grade 8 Technology Applications TEKS claim, constrains DOK to 1–2, permits teacher-verified and accommodated equivalent evidence, enforces five-point points grading with online upload before and after mutation, and links a separate student-safe deck. The stable guide item is now present in the daily-contract ledger.

### Student experience

The first review returned HOLD: bilingual support stopped short of the visual route, independent learners lacked visible checkpoints, the reflection forced a fabricated surprise, the deck began with teacher language, and purpose/extension were thin.

Final decision: GO. Students receive bilingual visual captions and full text directions, three repeatable assessment → screenshot → checkpoint loops, a resume-at-first-missing-screenshot rule, an honest surprise-or-confirmation stem, a purpose statement, and an optional career question that adds no proficiency evidence. The 16-slide student deck contains no teacher-only cards.

### Design and language

The first final-pass review returned HOLD twice. It first found student-facing production commentary and a code path that could leave a previously exposed facilitator guide visible. After those source fixes, it found stale responsive screenshots that still displayed the removed sentence.

Final decision: GO. The production sentence is absent from source and refreshed 390/1280 renders. Existing and new guides are forced to published=false, hide_from_students=true, editing_roles=teachers, with an unpublished module item and unconditional readback validation. The alleged slide 13 clipping was disproved by native geometry and a complete 1600×900 render. No other clipping, overflow, projection, hierarchy, accessibility, or language-scope defect remains.

## Adversarial consensus

Every evidence-backed HOLD was corrected and rereviewed; no finding was waived by majority vote. The reviewers agreed on one coherent route:

1. Model the three Xello assessments with authentic first-party screens.
2. Save one privacy-safe result screenshot after each assessment.
3. Pause or continue using the same student-visible checkpoints.
4. Submit three screenshots and one honest surprise-or-confirmation reflection.
5. Score the same 3 + 1 + 1 evidence contract across all routes.

The group also agreed that this operational college-and-career check-in should not be presented as independent Grade 8 Technology Applications TEKS mastery.

## Merge gate

The reviewed implementation satisfies the merge gate:

1. Teacher and student artifacts teach the same evidence sequence end to end.
2. The teacher deck retains pacing/stop cards; the student deck removes them.
3. English and Spanish routes require equivalent work and provide point-of-need directions.
4. The guide supplies realistic compressed and multi-day pacing, retained Week 1 work, checks, misconceptions, recovery, scoring, UDL, differentiation, and DOK restraint.
5. Screenshot capture is privacy-safe on Chromebook and Windows, with equivalent accommodated evidence routes.
6. Assignment settings fail closed at 5 points, points grading, and online upload.
7. The guide is hidden, teacher-editable, and unpublished; the guide module item is unpublished.
8. The assignment and its module item remain unpublished.
9. Canvas, the snapshot, generated HTML, site manifest, daily-contract ledger, public assets, and live verification agree.
10. All four final reviewers returned GO.

## Safe publication-stage deferrals

- signed-in Canvas Student View on a managed student Chromebook;
- managed-device Xello login, screenshot, and upload rehearsal;
- embedded-video playback/caption rehearsal under student filtering;
- teacher timing rehearsal and a small student engagement/timing pilot.

These are publication and pilot gates. This review does not publish the assignment or facilitator guide.

## Fixes and final rereview

- Canvas apply created hidden/unpublished guide item 2665839 at position 6 and moved the preserved unpublished assignment item 2633997 to position 7.
- Live readback confirms assignment 1183431 remains unpublished, worth 5 points, uses points grading, and accepts online file upload.
- Live readback confirms the guide page is unpublished, hidden from students, teacher-editable, and its module item is unpublished.
- Native deck reread confirms 19 teacher slides and 16 student slides at the reviewed revisions; both have district-domain reader permissions.
- Five unit tests pass, including fail-closed assignment settings and four exposed-guide regression cases.
- Responsive QA passes at 390px and 1280px with zero horizontal overflow; refreshed screenshots contain no authoring-language leak.
- sync_course.py passes Canvas export, site build, verify_site.py, and verify_live.py: 34 modules, 510 items, 445 item pages, 201 public files, 157 facilitator-guide contracts, and zero unresolved links.
- Final rereview decisions: teacher GO; district GO; student GO; design/language GO; consensus GO.
