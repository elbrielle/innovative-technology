# VILS agent contract

## Smart Solutions fleet parity

When the user says the Verizon Smart Solutions source is **good**, **approved**,
**final**, or otherwise ready to distribute, every agent context must:

1. Invoke `$canvas-fleet-parity` and read `docs/CANVAS_FLEET_PARITY.md`.
2. Treat Verizon Canvas course `23402` as the canonical authoring source and
   every enabled Smart Solutions course in the private VILS adapter as a destination.
3. Record the user's explicit source approval with
   `scripts/ss_fleet_release.py approve-source`; never infer approval from
   silence, a clean diff, or a passing test.
4. Run the semantic enabled-fleet audit with
   `scripts/ss_fleet_release.py audit`. Audit and plan are read-only.
5. Review every course separately. Publication is teacher-only operational
   discretion: ignore published/unpublished differences and never include a
   publication field in an existing-object update. Maintain canonical module
   names, canonical item placement/order, and module structure. Preserve
   teacher-created extras, homepages, dates, submissions, grades, and
   materially teacher-modified canonical content bodies/settings.
6. Create immutable, hash-pinned, course-specific plans and current private
   backups. Source approval does not authorize destination writes.
7. Obtain a second explicit user approval naming the plans and target courses
   before apply. Apply one course at a time and stop on the first mismatch.
8. Fresh-read every touched object, rerun the semantic fleet audit, and update
   identity-only reviewed state. Never promote semantic drift automatically.

For a course with duplicate historical import lineages, use
`scripts/plan_ss_legacy_rebootstrap.py` to create the sealed, course-specific
mapping and backup. Do not import, remove module shells, or update the homepage
until the user approves that exact plan hash. An approved module-shell cleanup
must retain all underlying pages, assignments, quizzes, files, and submissions.
If a cartridge returns any migration issue, stop the original plan, seal an
amended post-import plan with `scripts/plan_ss_partial_import_recovery.py`, and
obtain approval of that new hash before recovery. Verify with the dedicated
read-only verifier; never rerun an apply merely because its final local
bookkeeping step failed.

Do not use Commons lineage as ownership proof. Do not delete or replace a
teacher object to force parity. A new object may begin unpublished because no
teacher state exists yet; subsequent parity runs never flip it. Keep adapters, teacher labels, IDs, tokens,
backups, plans, releases, and reports under
`~/.config/canvas-fleet-parity/vils/`, never in this repository.

Do not use `reconcile_ross_course.py` or `reconcile_duncan_course.py` for fleet
parity. They are historical one-time rebuild tools and may contain publication
operations that this fleet contract forbids.
