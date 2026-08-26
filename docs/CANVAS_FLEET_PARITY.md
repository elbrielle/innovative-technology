# Canvas fleet parity

VILS curriculum distribution uses the reusable personal Codex skill
$canvas-fleet-parity. The skill audits destination courses without turning
this public curriculum repository into a teacher-roster database or a second
copy of live Canvas.

## Ownership boundary

- Verizon Canvas course 23402 remains the canonical VILS authoring source.
- data/course-snapshot.json is the verified source inventory used by the
  VILS fleet adapter.
- The generated public mirror remains downstream of canonical Canvas and is
  never edited to push content into teacher courses.
- Each teacher course retains its own IDs, dates, publication choices,
  homepage, submissions, materially edited canonical content, and
  teacher-created content.
- Publication is not parity data. Published/unpublished differences are
  ignored, never classified as edits or drift, and never synchronized.
- Canonical module names, canonical item placement/order, and module structure
  are parity-managed. Teacher-created extras remain; materially edited
  canonical bodies/settings are protected.
- The fleet controller does not make Commons provenance authoritative.

## Private fleet data

The live adapter, destination course IDs, teacher labels, reviewed baselines,
backups, and reports stay outside this public repository:

    ~/.config/canvas-fleet-parity/vils/
      vils-smart-solutions.json
      states/vils-smart-solutions-reviewed-identity.json
      backups/
      releases/
      reports/

Use config/fleet-parity/vils-smart-solutions.example.json only as a sanitized
shape reference. Never add a real token or teacher fleet roster to Git.

## Invocation contract

The short user invocation is:

> Use $canvas-fleet-parity. The Verizon Smart Solutions source is good. Record
> this source approval, audit every enabled SS course, and stop at reviewed plans
> before any destination writes.

That sentence authorizes source recording, read-only audit, and planning. It
does not authorize destination writes. After reviewing the plans, use a second
invocation:

> Use $canvas-fleet-parity. Apply these reviewed plans to the named SS courses
> one at a time, ignore and preserve every publication choice, restore
> canonical names/order/structure, protect teacher-created or materially edited
> content, verify each course before continuing, and stop on the first mismatch.

The second invocation must name or link the immutable plans and identify the
target courses. “The source is good” alone is never enough to apply.

## Approved-source and enabled-fleet commands

Keep the Verizon source token separate from the Irving destination token:

    ~/.canvas_vils_source_token    # Verizon course 23402, mode 600
    ~/.canvas_token                # Irving destination API, mode 600

After the user explicitly approves the current Verizon source, record the
exact approval statement and rebuild/verify the snapshot and public mirror:

    python3 scripts/ss_fleet_release.py approve-source \
      --approval-note "<exact user approval statement>"

This runs the Canvas-to-site sync against Verizon, verifies live source parity,
validates the curriculum review gate and private fleet adapter, and
writes an immutable private release manifest. It changes no destination
course. The manifest is sealed with a neighboring `.sha256` file; later audits
fail if either the manifest or approved snapshot changes.

Then run the semantic audit against every enabled Smart Solutions course:

    python3 scripts/ss_fleet_release.py audit

For a teacher-specific onboarding or repair, keep the same approved source but
scope the read-only audit to that enabled destination:

    python3 scripts/ss_fleet_release.py audit --course <course_id>

The command refuses to run if the approved snapshot changed, the adapter does
contain no enabled destinations or duplicate course IDs, or the adapter points
to a different source. It uses the reviewed identity state when present and
writes a timestamped private report.

## Lower-level audit commands

Validate the private adapter:

    python3 ~/.codex/skills/canvas-fleet-parity/scripts/fleet_audit.py \
      --adapter ~/.config/canvas-fleet-parity/vils/vils-smart-solutions.json \
      --validate-only

Run the fast structure audit:

    python3 ~/.codex/skills/canvas-fleet-parity/scripts/fleet_audit.py \
      --adapter ~/.config/canvas-fleet-parity/vils/vils-smart-solutions.json \
      --content-depth structure \
      --output ~/.config/canvas-fleet-parity/vils/reports/structure-audit

Run the body-level semantic audit:

    python3 ~/.codex/skills/canvas-fleet-parity/scripts/fleet_audit.py \
      --adapter ~/.config/canvas-fleet-parity/vils/vils-smart-solutions.json \
      --content-depth semantic \
      --output ~/.config/canvas-fleet-parity/vils/reports/semantic-audit

Both modes are read-only. state-candidate.json is not a reviewed baseline.
Do not pass it back with --state until the mapping and every bootstrap hold
have been adjudicated.

## Legacy duplicate-import repair

When a teacher course contains more than one historical Smart Solutions import,
do not treat either lineage as an automatically safe baseline and do not reuse
the old Duncan or Ross cleanup scripts. Create a course-specific, sealed,
read-only rebootstrap plan with `scripts/plan_ss_legacy_rebootstrap.py`.

The planner requires an explicit mapping from every canonical source position
to the destination module container that will survive. This makes the choice
between duplicate module IDs reviewable instead of title-inferred. It also:

- verifies the approved release and cartridge hashes;
- excludes publication from destination guards;
- requires the declared submission holds to equal Canvas's live
  `has_submitted_submissions` set;
- records protected quiz, assignment, and module-item IDs together;
- creates a private recoverable placement/front-page backup; and
- emits a sealed plan and exact approval phrase under the private parity root.

Deleting a duplicate *module shell* is distinct from deleting its underlying
course content: Canvas removes the placements from Modules but retains the
pages, assignments, quizzes, files, and submissions in the course. Even so,
module-shell removal is a destructive structural operation and must be named in
the immutable plan and separately approved. Never delete the underlying course
objects to make the audit count look cleaner.

The approved plan must preserve submitted assessments unchanged, omit every
publication parameter, skip course settings and visibility settings during any
staging import, update an explicitly approved homepage in place, and stop on a
migration issue or any preflight hash mismatch.

If Canvas completes the cartridge but reports migration issues, stop the
original plan before structural cleanup. Use
`scripts/plan_ss_partial_import_recovery.py` to seal the exact post-import
state, failed unsubmitted assignment payloads, verified file mappings, Week 0
move set, homepage payload, and obsolete shell IDs. Apply only a separately
approved amended hash with `scripts/apply_ss_partial_import_recovery.py`, then
run `scripts/verify_ss_partial_import_recovery.py` and the normal semantic fleet
audit. A verifier failure is not permission to rerun an apply; inspect live
state and use the read-only verifier.

## Classification contract

- candidate_current: semantic hashes match; still needs initial-baseline review.
- bootstrap_review: first-run difference; preserve until adjudicated.
- safe_update: source changed while destination still matches a reviewed baseline.
- teacher_modified_preserve: destination changed while source did not.
- conflict_hold: source and destination both changed.
- proposed_add_review: canonical item is missing and may be added after review.
- destination_extra_preserve: teacher/local item is retained.
- source_removed_no_delete: removal is reported and never automatic.
- reviewed_identity_unbaselined: the source/destination identity is reviewed,
  but body-level drift has not been accepted as a semantic baseline.
- module_name_update_review: a reviewed mapped module has a noncanonical name
  and may be renamed without touching publication.
- canonical_placement_update_review: a mapped canonical item is in the wrong
  module or relative position and may be structurally repaired while retaining
  teacher-created extras.

Any ambiguous, hold, preserve, no-delete, active-import, detail-error, or
unexpected-identity condition blocks mutation.

The historical `reconcile_ross_course.py` and `reconcile_duncan_course.py`
scripts are not fleet apply tools and must not be reused for parity. They were
one-time rebuild utilities and include operations outside this publication-
neutral contract.

## First VILS proof

The first read-only fleet audit ran against the three currently accessible
Smart Solutions destination courses.

- The structure pass uniquely mapped all 510 canonical items in two courses.
- It preserved one local item in one course and two local modules in another.
- The third course retained ten local items, held a renamed canonical module,
  and proposed three missing canonical items for review.
- The semantic pass detected both exact content matches and operational drift,
  including an external-tool assignment whose visible body and grading
  settings survived import while its LTI configuration did not.
- No destination course, Drive file, source snapshot, or public page changed.

Ross now has all 510 canonical identities mapped while eight local items remain
preserved. His older Video Game Design module name and the moved Portfolio item
remain mapped by ID and will appear as structural plan candidates, not content
conflicts. The reviewed state is identity-only: it enables durable mapping but
does not accept body-level differences as a semantic baseline.

This proof and state do not authorize a future synchronization. Each approved
source release still requires a new enabled-fleet audit, reviewed immutable
plans, current backups, explicit apply approval, and post-apply verification.
