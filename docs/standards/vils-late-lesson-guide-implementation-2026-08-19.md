# VILS late-course daily facilitator-guide implementation

This record covers the live Canvas template course, **Irving ISD VILS 2027 Template** (`23402`), for modules 24–33. It implements the lesson-level guide standard demonstrated by Superhero Comics: a teacher page immediately before a particular student lesson, with a learning contract, exact TEKS where the student evidence warrants one, before-class preparation, five-part flow, evidence check, and access supports.

## Scope

- **Created for active SW6:** four AR guides; two missing VR guides (Lesson 2 already had a dedicated guide/materials page); three Pitching guides; a 10-day Capstone guide and Xello run card; and two Closing guides.
- **Created for deployable enrichment:** six Stop Motion guides, including the EdPuzzle reconnection/setup guide required before that optional route can be published safely.
- **Preserved, not duplicated:** existing daily guide/material routes in Snap Circuits, Robot Salad, micro:bit Project, and Smart Electronics Project 3.
- **Not changed:** Enrichment · Parked Alternates. It remains parked and does not count as active guide coverage.

The executable source is `scripts/apply_late_lesson_guides.py`. It requires a fresh local Canvas token, verifies the course and target module/item IDs, creates only unpublished teacher pages, places each page immediately before its matching student item, and verifies exact TEKS wording and module order. It does not export, sync, or modify generated public-site files.

## TEKS policy

The script draws exact wording only from `texas-technology-applications-grade-8-teks-2022.md`. Preparation-only and operational items (the Pitching EdPuzzle, Xello check-in, Post-Survey, and Stop Motion EdPuzzle) explicitly make no lesson-level TEKS claim because their current student evidence does not independently demonstrate an expectation.
