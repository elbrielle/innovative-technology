# VILS Four-Lens Curriculum Review Gate

Every pull request that changes instructional content must pass an independent, adversarial curriculum review before merge. A clean render, correct link, or TEKS code is necessary but not sufficient. The review asks whether the materials work as a complete classroom system.

## When the gate applies

Run the gate when a pull request changes any of the following:

- facilitator guides, student guides, assignments, quizzes, rubrics, or module order;
- projected decks, worksheets, exemplars, starter files, or other curriculum assets;
- objectives, demonstrations of learning, standards claims, scope and sequence, or required student evidence;
- Canvas-generated lesson/module pages or the source scripts that create them.

Pure infrastructure, typo-only documentation, and noninstructional repository maintenance may be marked `not applicable` in the pull request with a short reason.

## Independent first round

Use four separate reviewers or agents. They must inspect the same rendered artifact set independently before seeing one another's conclusions.

### 1. Teacher implementation

Judge whether a teacher unfamiliar with the build can teach it end to end without reverse-engineering.

Required checks:

- realistic period budget and what existing work is shortened or retained;
- materials, setup, prerequisites, and exact teacher navigation;
- opening, model, guided practice, formative checks, work time, closure, and submission;
- expected responses, misconceptions, troubleshooting, absence, and recovery routes;
- worksheets, slides, exemplars, scoring tools, and links actually match the required evidence.

### 2. District curriculum

Judge instructional validity rather than the presence of compliance labels.

Required checks:

- Topic, objective, exact TEKS, demonstration of learning, and `introduced` / `practiced` / `demonstrated` status;
- the student artifact actually satisfies the verbs and depth of the claimed standard;
- DOK progression, assessment validity, scoring clarity, and extension-versus-proficiency boundary;
- universal design, differentiation, scaffolds, accommodations, EB access, privacy, and application approval;
- scope-and-sequence, standards ledgers, Canvas, Drive, and public-mirror claims agree.

### 3. Student experience

Review as more than one learner profile: novice, confident student, multilingual learner, and student needing chunking or executive-function support.

Required checks:

- purpose, relevance, agency, challenge, success moments, and extension;
- directions are understandable without teacher-only knowledge;
- cognitive and link load, pacing, grouping labels, and evidence burden;
- accessible recovery, bilingual parity, and a clear `Now / Next / Done` route;
- the lesson is enjoyable and authentic without hiding the learning.

### 4. Design and language

Judge whether the visual and verbal system communicates the lesson intentionally.

Required checks:

- every final DOCX/PDF/PPTX/Google artifact is rendered in its delivery engine and inspected page or slide by page;
- hierarchy, typography, contrast, crops, alt text, non-color-only meaning, and responsive behavior;
- varied, instructionally useful compositions rather than repetitive AI-style card grids;
- projected and student-facing copy is written for students, not curriculum planners;
- statutory wording, pacing notes, differentiation labels, and production commentary stay teacher-facing;
- English/Spanish or EB supports appear at the moment students need them.

## Severity and decisions

Use these severities consistently:

- `blocker`: the lesson cannot be taught as claimed, required evidence is missing, a standards/privacy/access claim is invalid, or an artifact is broken;
- `major`: material confusion, inequity, grading weakness, or orchestration burden that should be fixed before merge;
- `minor`: polish that can safely remain in a tracked follow-up without changing instructional validity;
- `strength`: a feature that should survive revision.

Each lens ends with one decision:

- `GO`: ready for merge within the reviewed scope;
- `GO WITH FIXES`: no blocker remains; named minor fixes may be completed before publication;
- `HOLD`: one or more blockers or unresolved major findings remain.

## Adversarial consensus round

After the independent reports, share the combined findings with the reviewers and require a challenge round.

Reviewers must:

1. identify overlap and disagreement;
2. challenge unsupported or preference-only findings;
3. separate the merge gate from publication/pilot gates;
4. agree on the minimum fixes that make the evidence, teacher route, access, and language truthful;
5. preserve strengths instead of rebuilding indiscriminately.

Consensus is not majority voting. Any evidence-backed HOLD must be resolved or explicitly disproven. Aesthetic preference cannot override accurate, accessible, classroom-usable work; visual defects or student-facing language leakage can.

## Required review record

Create or update one file in `docs/reviews/` for the pull request. It must include:

- exact scope and artifact identities;
- independent findings and decision from all four lenses;
- consensus findings, safe deferrals, and merge gate;
- fixes applied and verification evidence;
- final four-lens rereview decisions.

The record must contain these machine-readable lines:

```text
Teacher implementation: GO | GO WITH FIXES | HOLD
District curriculum: GO | GO WITH FIXES | HOLD
Student experience: GO | GO WITH FIXES | HOLD
Design and language: GO | GO WITH FIXES | HOLD
Consensus: GO | GO WITH FIXES | HOLD
```

The repository review check fails closed when instructional files change without a changed review record, when a required decision is missing, or when any final decision is `HOLD`.

## Merge versus publication

Merge gates prove the reviewed source is coherent and ready to stage. Publication may still require managed-device rehearsal, district app approval, teacher timing, Student View, or a small student pilot. Record those separately; do not weaken the merge review and do not claim a pilot occurred when it did not.

