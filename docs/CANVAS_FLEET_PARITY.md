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
  homepage, submissions, locally edited canonical content, and teacher-created
  content.
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
> this source approval, audit all three SS courses, and stop at reviewed plans
> before any destination writes.

That sentence authorizes source recording, read-only audit, and planning. It
does not authorize destination writes. After reviewing the plans, use a second
invocation:

> Use $canvas-fleet-parity. Apply these reviewed plans to the named SS courses
> one at a time, preserve all teacher changes and publication choices, verify
> each course before continuing, and stop on the first mismatch.

The second invocation must name or link the immutable plans and identify the
target courses. “The source is good” alone is never enough to apply.

## Approved-source and three-course commands

Keep the Verizon source token separate from the Irving destination token:

    ~/.canvas_vils_source_token    # Verizon course 23402, mode 600
    ~/.canvas_token                # Irving destination API, mode 600

After the user explicitly approves the current Verizon source, record the
exact approval statement and rebuild/verify the snapshot and public mirror:

    python3 scripts/ss_fleet_release.py approve-source \
      --approval-note "<exact user approval statement>"

This runs the Canvas-to-site sync against Verizon, verifies live source parity,
validates the curriculum review gate and private three-course adapter, and
writes an immutable private release manifest. It changes no destination
course. The manifest is sealed with a neighboring `.sha256` file; later audits
fail if either the manifest or approved snapshot changes.

Then run the semantic audit against all three enabled Smart Solutions courses:

    python3 scripts/ss_fleet_release.py audit

The command refuses to run if the approved snapshot changed, the adapter does
not contain exactly three unique enabled destinations, or the adapter points
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
- reviewed_module_rename_preserve: a reviewed destination module ID remains
  mapped while its teacher-selected name is preserved.

Any ambiguous, hold, preserve, no-delete, active-import, detail-error, or
unexpected-identity condition blocks mutation.

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

Ross now has all 510 canonical identities mapped while eight local items and
the teacher-selected Video Game Design module name remain preserved. The
reviewed state is identity-only: it enables durable mapping but does not accept
body-level differences as a semantic baseline.

This proof and state do not authorize a future synchronization. Each approved
source release still requires a new three-course audit, reviewed immutable
plans, current backups, explicit apply approval, and post-apply verification.
