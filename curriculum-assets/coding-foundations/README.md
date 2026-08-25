# Coding Foundations source assets

These are the reviewed local source artifacts for Canvas course `23402`. A file is not live merely because it changes here; the Canvas publishing layer must deliberately upload and relink the reviewed revision. The Canvas apply script reads from this folder so a clean checkout does not depend on ignored temporary files.

- `Coding_Foundations_Passport_EN.*` and `Coding_Foundations_Passport_ES.*` are the reviewed bilingual student Passports. Each student creates one copy and reuses it across seven unambiguous checkpoints.
- `Smart_Solutions_Coding_Foundations_Retrofit_Teacher_Deck_2027.pptx` is the reviewed 57-slide editable teacher deck, with a section map and teacher-only stop points.
- `Emergency_Supply_Grid_Day1_Highlighted_Bug_Route.txt` highlights the boundary to investigate without revealing the repair.
- `Emergency_Supply_Grid_Day2_Student_Authorship_Scaffold.txt` supplies only MakeCode setup and the sprite helper; students must author typed variables and operations and complete both loop boundaries.
- The Canvas publishing script links the highlighted Day 1 route and the student-authorship Day 2 scaffold. The original bug challenge and full core starter remain in source history for comparison; they are not the reviewed student routes. The exemplar remains teacher-facing.
- `makecode-arcade-new-project-welcome.png` is the neutral Day 1 setup view; it intentionally reveals no challenge code or result.
- `makecode-supply-grid-*.png` are teacher-reference MakeCode captures used only after diagnosis or in Canvas teacher materials.

The Python and JavaScript builders write working outputs under `tmp/coding-foundations-retrofit/`. Rebuilding is a draft-generation step: render and inspect the new outputs before deliberately replacing any reviewed artifact in this folder or an existing Drive/Canvas identity.
