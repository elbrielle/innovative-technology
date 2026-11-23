# Approved-source ledger reconciliation

## Reviewed scope

Release preparation requested by the owner: “Fleet parity and commons please.”
This patch reconciles ten historical ledger records with the current approved
Canvas source. It changes no Canvas lesson, student artifact, teacher guide,
slide, rubric, publication choice, or classroom requirement.

The affected record IDs are 2636701, 2636702, 2636703, 2657941, 2657942,
2657943, 2657944, 2636712, 2636713, and 2636714. They cover approved CAD/STL
evidence and the map, standalone 360 and branching sequence.

The August ledger incorrectly expected PNG/annotation artifacts, an actual ring
revision, or the retired Welcome Mission. The revised ledger records current
STL submissions and existing reflections, preserves the ring's hypothetical
troubleshooting distinction, and removes the retired map dependency from 360.

Four approved guides use prose layouts. They remain eligible only while the
hash of their complete normalized visible text matches this reviewed record.
Topic, objective/evidence excerpts and cited TEKS must still appear. Other
guides retain the existing markup checks. Guide identity follows known ledger
IDs as well as title detection, so renamed guides cannot silently disappear.

## Independent findings

- Teacher implementation: GO. All ten records match current teaching and
  existing submissions; no extra worksheet or revision artifact was added.
- District curriculum: GO. Scope and evidence distinctions remain intact;
  this reconciliation does not establish full TEKS or iCEV mastery.
- Student experience: GO. Current requirements are preserved, including
  creative branching and the existing reflections.
- Design and language: GO. No approved page is forced back into August
  headings or layout. Text hashes are wording checks, not visual proof.

The curriculum and student reviewers identified a missing reference to this
review document. This file resolves that packaging finding.

## Adversarial consensus

All four reviewers agree on the bounded fix: reconcile records to the approved
source and retain strict drift detection. No reviewer recommended restoring
superseded instructions or adding student evidence. The remaining distinction
is intentional: metadata/code validation does not prove student mastery,
browser access, Commons completion or teacher-course distribution.

Teacher implementation: GO
District curriculum: GO
Student experience: GO
Design and language: GO
Consensus: GO

## Merge gate

The focused regression test verifies that exact approved prose passes, harmless
layout markup does not change the text hash, and evidence changes, missing
approval, missing hashes, or unknown formats fail that approval check.
`verify_site.py` passes against 36 modules, 517 items, 157 guides and 334 public
files after this reconciliation. The release controller must still perform
fresh source/live verification before sealing its release manifest.

No fleet apply is authorized by this review. Immutable course-specific plans
still require separate owner approval. Homepage and publication changes remain
outside parity.

## Fixes and final rereview

The independent findings were resolved without Canvas mutations. Original
ledger issue notes remain available as `prior_audit_issues` on revised records
and in Git history. All four approved prose hashes were checked against current
snapshot text; required semantic phrases remain independently checked.

Teaching checks for this bounded metadata patch:

1. Existing source teaching moves and order are unchanged.
2. No concept/example or application timing changes.
3. No comparison/reveal changes.
4. Teacher demo checklists remain unchanged.
5. Persistent work slides and submission routes remain unchanged.
6. No images, screenshots or projection assets changed.
7. No new discussion stops or student wording added.
8. Ledger evidence now matches approved assignments and guides.
9. Source attribution and accessibility alternatives remain unchanged.
10. No presentation was rebuilt or republished by this patch; prior artifact
    verification is separate from this release-metadata verification.
