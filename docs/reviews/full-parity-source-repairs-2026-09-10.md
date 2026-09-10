# Full parity source repairs

## Reviewed scope

This release repairs two canonical teacher pages and one stale download after a complete source/fleet inventory and a 232-file Google reference audit. It does not redesign every lesson or claim that teacher variations are errors.

The August 28 owner-approved 69-slide native Piskel master contains six revised slides (32, 33, 34, 37, 41, 49), but the Canvas PowerPoint still carried the August 25 version. The new download is an export of that existing approved master; the separate 58-slide compressed teaching route remains separate. The final master target remains ten seconds at 12 FPS. Initial tool previews at 5–8 FPS, five-second workload examples, and the one-to-two-second Practice Wall exercise serve different purposes.

The unavailable Ready Set facilitator-guide copy link now points to a native Google Doc containing the current canonical teacher guide. Its self-reference says “this document”; all other teaching requirements, resource links, optional routes, materials constraints, and language supports remain. Nine native resource chips accompany retained copy links. The master grants unlisted district-reader access and preserves the owner. All three native PDF pages were inspected.

The snapshot exporter also retains quiz scoring policy and discussion-rating fields consumed by the fleet audit. Omitted source fields previously appeared as null differences. This metadata correction changes no live course settings.

## Independent findings

Four separate reviewers inspected the same artifact set independently before exchanging findings.

- **Teacher implementation:** The repaired guide preserves the complete class flow, optional routes, materials/grouping explanation, evidence, and language scaffolds. Initial HOLD for missing replacement/access proof cleared after inspecting the native document, all three PDF pages, and district-reader metadata.
- **District curriculum:** The new download restores approved instruction without changing the final assessment. Five-second frame examples are not a new final length requirement. Historical source matches support narrowly planned updates; teacher grading/alternate routes and submitted assessments remain separate protections.
- **Student experience:** The restored source preserves the different preview, practice, and final-product routes. Representative Passport, robotics, and AI case-file directions remain concrete. No added student product, translation burden, or supply/budget assignment is required.
- **Design and language:** The exact exported PowerPoint has 69 slides and 69 notes; only the six intended slides change text, all notes retain their text, and seven GIF byte hashes survive. Some XML is reserialized, so XML byte identity is not claimed. All internal relationships resolve. Native PDF and actual PowerPoint rendered through bundled LibreOffice were inspected; task-local font configuration restored the already-installed intended fonts. No package or system font changes were required.

## Adversarial consensus

The reviewers distinguished existing source issues from changes introduced by synchronization. Existing Piskel overlap/crowding and older source-guide wording are recorded for separate authoring review; they do not justify redesigning an already approved master during this release. The source teacher note explicitly explains slide 34's five-second examples and keeps the final assignment/rubric requirements. It also distinguishes native Google video players from the PowerPoint's clickable tutorial links. Neither Microsoft PowerPoint playback nor managed-device access is claimed.

The Ready Set replacement resolves an unavailable resource without changing student assessment. Broad provider originals are references, not supposedly identical copies of adapted Canvas lessons. Teacher variations, historical assignment submissions, grades, dates, and publication choices are protected in separate course-specific plans.

## Merge gate

Teacher implementation: GO
District curriculum: GO
Student experience: GO
Design and language: GO
Consensus: GO

GO covers the bounded canonical source repair, snapshot metadata correction, and generated public mirror. Destination writes require their separate reviewed plans and approval; this record does not authorize overwriting a teacher variation or submitted assessment.

## Fixes and final rereview

- The final Piskel teacher note resolves the arithmetic-context and video-delivery disclosures.
- Native guide readback confirms all content, semantic headings/lists, nine rich links, and district-reader sharing. All three rendered pages are readable and unclipped.
- PowerPoint SHA-256: `5a1cee958faff83fda50eb62dd71d344fe2ed89e7153852a9d68d34cf097a78d`; size 11,872,869 bytes. Actual LibreOffice-rendered PDF SHA-256: `38186eef50b92d359dd56fcecf09c0357f9d0d43f3190e8f241bae98ba33762d`.
- The original PowerPoint remains archived privately and retained in Canvas; no teacher file deletion is included.
- Canvas refreshed only the download verifier while serializing the page. The write was inspected, not replayed. Newly uploaded file visibility was configured to the original hidden-but-unlocked state; existing object publication was preserved.
- Both projection regression tests and the existing suite pass: 21 tests total. Complete source export/build/live checks and public deployment are release verification steps, recorded separately.

### Teaching checks

The approved sequence and conceptual buildup remain; brand examples and comparisons are preserved; the six revised slides restore real interface/tool instruction; the demo-to-practice-to-final sequence remains; final work criteria remain visible; actual native and exported renders were reviewed; no new planner prose enters student directions; artifact/submission requirements are unchanged; original attribution, GIFs, notes, and tutorial references remain; native video players and exported clickable links are described accurately. The new guide is a faithful copy repair, not a new standalone teaching-deck design.
