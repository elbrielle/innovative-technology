# Coding Foundations Retrofit — Four-Lens Review

Review date: 2026-08-23

Pull request: `#5`

Reviewed implementation commit: `500b6fb`

Review status: GO FOR MERGE; CANVAS PUBLICATION NOT AUTHORIZED

Teacher implementation: GO
District curriculum: GO
Student experience: GO
Design and language: GO
Consensus: GO

## Reviewed scope

- seven Coding Foundations Passport checkpoints folded into the existing Intro to CS, Video Game Design, Text-Code Bridge, and RVR routes;
- 10-page English and 10-page Spanish Passports in editable DOCX, PDF, and same-ID native Google Docs;
- 57-slide teacher deck in PPTX and same-ID native Google Slides, including C1–C7 navigation, teacher-only stop points, speaker notes, and two accessible screenshots;
- facilitator guides `2661807` and `2661809`, student assignments `2661808` and `2661810`, Day 1 scoring, Day 2 rubric, and eight-question bilingual knowledge check `2661811`;
- Day 1 highlighted bug route `3229498`, Day 2 student-authorship scaffold `3229499`, teacher exemplar `3229500`, final Passports `3229508`–`3229511`, and final deck `3229512`;
- Program Scope + Sequence, daily-contract ledger, TEKS audit, implementation record, Drive, unpublished Canvas staging, and generated public mirror.

## Independent findings

### Teacher implementation

The first review returned `HOLD`: the original Passport omitted required artifacts, the bridge guides were resource indexes rather than complete one-period guides, the deck revealed the repair before investigation, and existing lessons lacked workable timing/scoring routes.

Final decision: `GO`. Both facilitator guides now provide complete 50–55 minute delivery with prerequisites, materials, modeling, guided practice, checks for understanding, expected answers, misconceptions, scaffolds, troubleshooting, recovery, absence routes, scoring, submission, and closure. Day 1 preserves prediction → observed `3 × 3 / 9` → diagnosis → repair → `3 × 4 / 12`; Day 2 preserves full student authorship across every support route.

### District curriculum

The first review returned `HOLD`: standards claims exceeded student authorship, Topic/objective/DOL and introduced/practiced/demonstrated status were incomplete, and the original rubric, quiz, ledgers, and scope claims could not support closure.

Final decision: `GO`. Day 1 demonstrates §126.19(c)(2)(C) while treating supplied variables/loops as practice for (2)(A)/(B). Day 2 conditionally demonstrates (2)(A)–(C) through authored typed variables and operations, both complete nested loops, real constraints, first-run evidence, required revision, and explanation. The final route includes authentic DOK progression, UDL, bilingual access, differentiation that preserves the evidence threshold, operational scoring, and privacy-safe submission.

### Student experience

The first review returned `HOLD`: contradictory directions, executive-function load, incomplete multilingual access, ambiguous Passport routing, limited agency, and curriculum language made the route harder to follow than the lesson required.

Final decision: `GO`. Students receive short bilingual Now / Next / Done routes, mission choice, visible success moments, privacy-safe recovery, and the same evidence target across support levels. The Passport separates planning from full-code evidence, Day 1 discovery is not spoiled, and student pages say directly what students write or repair and submit for credit.

### Design and language

The first review returned `HOLD`: the Passports had rendering/Spanish defects, the deck was incomplete and repetitive, screenshot emphasis was inaccurate, and planning language leaked onto projected/student surfaces.

The final review challenged five remaining details before returning `GO`: slide 28's projected teacher-process subtitle, Passport metadata wrapping, the Spanish Checkpoint 6 continuation title/footer, curriculum-evidence jargon on both student pages, and the final C7 navigation instruction. All were corrected in the reviewed state. Final Drive renders are 10 + 10 pages and 57 slides; DOCX accessibility audits report zero high/medium/low findings; slide overflow QA passes; both screenshots carry accurate native Slides and actual PPTX picture alt text; and all 57 speaker-note records include `[Sources]`.

## Adversarial consensus

All four first-round lenses agreed on `HOLD`. The challenge round rejected two overreaches: a decorative wholesale redesign was unnecessary, and exact Passport numbering was a design choice rather than an instructional requirement. Reviewers instead agreed on truthful authorship, complete teacher orchestration, usable response space, delayed reveal, valid assessment, plain student language, bilingual parity, privacy, accessibility, and Canvas/Drive/mirror agreement.

The final challenge round also proved the gate was not ceremonial: the design reviewer found a projected teacher-talk leak after the other three lenses had returned GO. The wording was corrected, restaged, rendered, and narrowly rereviewed by all four lenses before consensus moved to GO.

## Merge gate

The reviewed implementation satisfies the merge gate:

1. Every required artifact has a labeled response/submission location.
2. Day 1 preserves prediction, observation, diagnosis, repair, and corrected evidence without an early reveal.
3. Day 2 requires meaningful string/number/Boolean variables and operations, both complete nested loops, prediction, first run, required revision, and explanation.
4. Both facilitator guides are complete end-to-end 50–55 minute guides.
5. Existing Intro/Game/RVR timing and scoring explicitly absorb the Passport evidence.
6. Day 1 and Day 2 scoring award full proficiency and allow zero for missing evidence.
7. The bilingual quiz is bounded as a knowledge check, not construction evidence.
8. Every advertised core/support resource exists and is linked.
9. Student surfaces use plain bilingual Topic / I can / Show Your Learning and Now / Next / Done language.
10. Spanish, rendering, projection, alt text, non-color-only meaning, and code accessibility pass review.
11. Coding submissions use class-safe aliases, cropped evidence, upload/text-entry routes, and no public-share requirement.
12. Scope, ledgers, audit, implementation record, Drive, unpublished Canvas staging, and public mirror agree.
13. All four final decisions are `GO` on implementation commit `500b6fb`.

## Safe publication-stage deferrals

- managed-Chromebook rehearsal;
- teacher timing rehearsal;
- small student timing/engagement pilot;
- final signed-in Student View after deliberate publication.

These are publication gates. This review does not authorize publishing the six new Canvas items or changing the preserved RVR publication state.

## Fixes and final rereview

- Final Canvas/public assets `3229508`–`3229512` hash-match the reviewed source binaries; code routes `3229498`–`3229500` also match source.
- The six-item Text-Code Bridge tail `2661806`–`2661811` remains unpublished.
- Same-ID Drive readback confirms both revised Passports, 57 native slides, the corrected final navigation, and accurate image title/description fields.
- `slides_test.py` passes with no overflow; both DOCX a11y audits are `0 high / 0 medium / 0 low`.
- `sync_course.py` passes snapshot, generated site, public assets, and live Canvas agreement: 34 modules, 509 items, 201 public files, 156 facilitator-guide contracts, and zero unresolved links.
- Final rereview decisions: teacher `GO`; district `GO`; student `GO`; design/language `GO`; consensus `GO`.
