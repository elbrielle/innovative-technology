# VILS agent contract

## Smart Solutions fleet parity

When the user says the Verizon Smart Solutions source is **good**, **approved**,
**final**, or otherwise ready to distribute, every agent context must:

1. Invoke `$canvas-fleet-parity` and read `docs/CANVAS_FLEET_PARITY.md`.
2. Treat Verizon Canvas course `23402` as the canonical authoring source and
   the three enabled courses in the private VILS adapter as destinations.
3. Record the user's explicit source approval with
   `scripts/ss_fleet_release.py approve-source`; never infer approval from
   silence, a clean diff, or a passing test.
4. Run the semantic three-course audit with
   `scripts/ss_fleet_release.py audit`. Audit and plan are read-only.
5. Review every course separately. Preserve teacher-created content, reviewed
   renames/moves, homepages, dates, publication states, submissions, grades,
   and teacher-modified canonical bodies.
6. Create immutable, hash-pinned, course-specific plans and current private
   backups. Source approval does not authorize destination writes.
7. Obtain a second explicit user approval naming the plans and target courses
   before apply. Apply one course at a time and stop on the first mismatch.
8. Fresh-read every touched object, rerun the semantic fleet audit, and update
   identity-only reviewed state. Never promote semantic drift automatically.

Do not use Commons lineage as ownership proof. Do not delete or replace a
teacher object to force parity. Keep adapters, teacher labels, IDs, tokens,
backups, plans, releases, and reports under
`~/.config/canvas-fleet-parity/vils/`, never in this repository.
