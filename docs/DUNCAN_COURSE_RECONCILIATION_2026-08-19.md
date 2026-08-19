# Duncan course reconciliation — August 19, 2026

## Final live state

- Irving course: `97806`
- Current template lineage: 34 modules, 503 module items
- Teacher-owned course-shell modules preserved: 2
- Archived August 5 template modules remaining: 0
- Archived August 5 pages remaining: 0
- Exact duplicate page titles remaining: 0
- Current front page: `Student Home — Smart Solutions`
- Current facilitator guides: 112 canonical Commons-linked guide pages, unpublished
- Submitted legacy record preserved: quiz `279777` / assignment `3066662` (`Student: Pre-Survey`)

The August 19 Commons migration `118099205` eventually completed and supplied
canonical copies of the new facilitator guides. The 112 temporary API-created
bridge pages were then removed by their explicit `data-vils-manual-bridge`
marker. The final guide layer is therefore Commons-linked rather than manual.

## What was removed

- 34 module containers from the August 5 archived template
- 88 August 5 page objects, including the obsolete `Course Home — Smart Solutions`
- 205 old assignment objects with no submitted work
- 17 old quiz objects with no submitted work
- 3 old discussions with no replies

The old import cartridge remains in Canvas import history. A full local page
and module backup was also written before deletion.

## Local recovery and identity records

These files are intentionally ignored by Git because the backup contains full
course bodies and may include authenticated curriculum content:

- `artifacts/duncan-old-template-module-backup-2026-08-19.json`
- `artifacts/duncan-current-release-map-2026-08-19.json`

The current-release map now records the canonical source-to-Irving module-item
identities and the removed manual bridge identities.

## Future Commons updates

Use the same Commons resource: `Irving ISD VILS 2027 Template`.

The August 10/current imported objects retained their Irving IDs through the
August 17 and August 19 updates. A future update from this same Commons resource
should update those objects in place. Do not import an archived or copied
Commons resource with a different resource identity; that is what created the
August 5 duplicate lineage.

After an update, verify:

1. 34 current template modules plus the 2 teacher-owned modules.
2. Module item title/type/order parity with `data/course-snapshot.json`.
3. No exact duplicate page titles.
4. Teacher facilitator guides remain unpublished.
5. `Student Home — Smart Solutions` remains the front page.
6. Assignment `3066662` remains intact while it holds student submissions.

