# Canvas fleet parity

VILS curriculum distribution uses the reusable personal Codex skill
$canvas-fleet-parity. The skill audits destination courses without turning
this public curriculum repository into a teacher-roster database or a second
copy of live Canvas.

## Ownership boundary

- Canvas course 23402 remains the canonical VILS authoring source.
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
      reviewed-state.json
      backups/
      reports/

Use config/fleet-parity/vils-smart-solutions.example.json only as a sanitized
shape reference. Never add a real token or teacher fleet roster to Git.

## Audit commands

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

This proof establishes audit/classification behavior only. It does not approve
a reviewed baseline or authorize synchronization.
