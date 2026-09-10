# PowerPoint storage maintenance — September 9, 2026

Teacher implementation: GO
District curriculum: GO
Student experience: GO
Design and language: GO
Consensus: GO

## Reviewed scope

Source-only asset maintenance: 18 PowerPoint packages, 498 slides, 68,645,444 bytes saved. The user also authorized archiving/removing unused older source files: 22 verified backups and removals, 305,694,216 bytes. No instructional rewriting, assessment changes, teacher-course deletion, or publication-state changes are included.

The final set retains all image dimensions, fonts, slide XML, notes, timing, and crops. Every decoded image is identical except one Pop Art soup artwork, explicitly permitted as JPEG 98 with full chroma. Pop Art slides 1 and 5 use that artwork; its final work slide remains byte-identical. History of Emoji, Unicode Consortium, and the current Lesson 2 live-teaching release remain untouched.

Final release packages and SHA-256 identities:

| Deck | SHA-256 |
| --- | --- |
| 01-Pop-Art-Teaching-Deck.pptx | `177a12c089eab2d1ae2bca3a9d89254884cb0456c62defcc504a164f4550b101` |
| Career Fair Step 3 — Example Student Websites (Lucero).pptx | `a1c8256bd0a95139e442999c644c32947b1b0b0d4f223ea12d5d2b9f58f05e2f` |
| Career Fair Step 4 — Example Promotional Materials (Lucero).pptx | `55f3786430f17a44e1106de941dc1237907965393a0ed76e890775b8232425df` |
| Graphic Design L1 — Pop Art of the 60's (Lucero).pptx | `39b0031c03057b19041e4467704cc5387da387722ca6b6c785db8280e9609e99` |
| Graphic Design L2 — Canva, 2026 live-teach revision (Lucero).pptx | `78a279143edac2e68a462d8f0e951ec11924b5525e712548ab0d0afdc7ac067f` |
| Graphic Design L2 — Graphic Design with Canva (Lucero).pptx | `94d91e82ff5874a99b3a2b9d17bc12c7f062f1ba8e1a059c8af1ce95004abe3d` |
| Graphic Design L4 — Pictographs (Verizon VILS U1C2L3).pptx | `48477d44e91138359806e2b7a20604784c0fd95448a87a4dc7576e3c1c364447` |
| Picture_This_Day_1_Teacher_Deck.pptx | `c36195731e3bed94d4c3048fc40f4874c9209ad0dd1dd372ed46af865c7cb4c5` |
| Smart_Solutions_3D_Modeling_Foundations_Teacher_Deck_2027.pptx | `6c49df84f5568ef25ff7f1e5993adde3161ae7e37efac0c8301d48cb3e902d38` |
| Smart_Solutions_AI_Ethics_Council_Teacher_Deck_2027.pptx | `0f43124fd032dc05e46765e574fc0e431235b17659af2d7bda21a00004b1aaec` |
| Smart_Solutions_AIR_Unit_0_Teacher_Deck_2027.pptx | `83b620c9cf24593e8687b3f871182330ab2581378f18bb08e312055de131b835` |
| Smart_Solutions_Circuit_Systems_Teacher_Deck_2027.pptx | `aa8102e7480092eb3fa0be6b33ba8f9854c4f464751707058f1c0a1b4276043d` |
| Smart_Solutions_Emoji_Design_Challenge_Teacher_Deck_2027.pptx | `5d0477df24d56b0129fc0d024b5f7b748f61530309559ece86d309349aed690b` |
| Smart_Solutions_Intro_to_CS_Code_and_Web_Teacher_Deck_2027.pptx | `cd2716c434abea2c335f456804fc05e77ff6d2958f47552b771430c46a05fe72` |
| Smart_Solutions_RVR_Robotics_Teacher_Deck_2027.pptx | `b389739961c066a38f65434c3fd4c53fb45e2ba6f34b67a0b94e6ce15779dcca` |
| Smart_Solutions_Video_Game_Design_Skillmap_and_Remix_Teacher_Deck_2027.pptx | `70acebae23d34df26de3d1a121c3d5811788b3b4825e8625cd224f9c2747ed50` |
| ThingLink_360_and_Visitor_Decisions_Teacher_Deck_2027.pptx | `1faf36095b02d2516897553a07c4cce0567312d450bb42fc5c342e0ae5c6f526` |
| ThingLink_Welcome_Mission_Teacher_Deck_2027.pptx | `17a21b658ac3241b2b2d902a2078051e1b037ec9562fc984fdefd36c9d2b27c7` |

## Independent findings

Four independent agents reviewed teacher implementation, district curriculum, student experience, and design/language. The first design review held the broader experiment because general JPEG conversion could alter rasterized text and screenshots. That experiment was discarded. The final implementation requires an exact media-part allowlist and keeps screenshots, line art, and whole-slide instructional images lossless.

- Teacher implementation: final GO. Existing live-teaching flow, speaker notes, examples, editable content, completion criteria, and download choices are preserved.
- District curriculum: final GO. Independent source/output hashes and non-media package comparisons found no standards, assessment, sequencing, or language changes introduced by maintenance. This does not recertify every preexisting curriculum claim.
- Student experience: final GO. All 18 hash pairs and 1,510 instructional/notes/font parts checked; 426 optimized image entries decoded. Only the named soup artwork differs. Its two slide appearances remain legible and useful for novice, multilingual, and confident learners.
- Design and language: final GO. Independently checked 546 media mappings, preserved dimensions and protected parts, inspected both changed artwork appearances at 3840 × 2160 with unscaled detail crops, and inspected all 17 pages exported by the actual Google Slides import.

## Adversarial consensus

The challenge round agreed that pixel metrics alone do not justify changing instructional text images. Lossless preservation for those images plus focused 4K/native inspection resolves the original HOLD. No evidence-backed HOLD remains. Native PowerPoint animation rehearsal and a physical projector were not tested; unchanged timing XML and decoded media are the preservation evidence, not a claim of hardware testing.

## Fixes and final rereview

All 36 final before/after render jobs passed, 498 slides per version. Automated comparison found 496 pixel-identical rendered slides; only Pop Art slides 1 and 5 differ (about 59.7/59.6 dB). This is a full computational comparison, not a claim that a human inspected 498 slides. Both differing slides received direct 4K review; all 17 native Google Pop Art pages were visually inspected.

The optimizer validates relationship targets and namespace-aware content types, rejects duplicate ZIP records and signed/macro packages, and pins protected parts. Regressions cover namespace-prefixed content types during JPEG conversion, directory records, duplicate media overrides, and protected bytes. The JPEG regression uses a deterministic test texture, so it cannot silently skip when a Canvas asset ID changes.

Original files, reference scans, hashes, immutable release manifests, and upload receipts are held privately outside Canvas and the public repository. Every removed file had no references in the audit and a live-byte hash matching its archived backup. Metadata was rechecked before deletion; the reference inventory was the saved audit rather than a synchronous rescan before each individual delete. The fresh post-maintenance scan is a separate completion check and does not retroactively change that evidence limit.

Canvas replacement downloads were fetched and hash-verified; original hidden/locked flags were preserved. Canvas rewrote download URLs to replacement IDs, and the matching Google-copy association metadata was refreshed without changing Google master URLs. Source maintenance grants no destination-fleet mutation authority.

## Workflow change

[PowerPoint release workflow](../POWERPOINT_RELEASE_WORKFLOW.md) now requires size review, projection-aware image sizing, protected-slide preservation, verified off-course archives, before/after QA, and source/Drive/website/Commons consistency. Existing PowerPoint and native Google copy options remain.

Fresh post-maintenance audit: 220 pages, 248 assignments, 3 discussions, 21 quizzes/100 questions, 34 modules, syllabus, 72 Office/HTML files, and 40 PDFs scanned. No live references remain to any of the 22 removed or 18 replaced file IDs; all 46 remaining PowerPoints are referenced. Course-file inventory decreased from 332 to 310 files and by 374,339,660 bytes.

Public mirror verification passed for 34 modules, 510 items, 207 public files, and 517 HTML pages. The responsive runtime gate passed all 482 non-redirect pages at 390 px, 50 desktop/phone screenshots, and 25 enlarged-text/reduced-motion samples. Representative index, about/status, module, protected notice, visual lesson, dense lesson, assignment, and download/video routes were inspected. Twelve established raw Drive release files were replaced in place; native Google masters and copy URLs were retained.

## Merge gate

GO for this source-maintenance release. All four final lens decisions are GO; protected content, final package hashes, rendered comparisons, live-source links, source/site parity, and responsive runtime checks passed. Commons processing and GitHub Pages deployment are tracked separately from these review conclusions. No Irving destination writes are included.
