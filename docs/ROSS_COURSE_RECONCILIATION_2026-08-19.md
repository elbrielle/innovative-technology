# Ross course reconciliation — August 19, 2026

## Final live state

- Irving course: `97926`
- Current template modules: 34
- Current canonical module items: 503
- Protected Ross-local module items: 8
- Archived template modules remaining: 0
- Archived template pages remaining: 0
- Exact duplicate page titles remaining: 0
- Front page preserved: `Welcome!` (`page_id 1116666`, URL `welcome-2`)
- Current `Student Home — Smart Solutions` remains available but is not the front page
- Facilitator guides: 112 tagged manual bridge pages, all unpublished

## Protected local content

The following existing assignment objects were linked into the current Week 0
module without copying or changing their IDs:

- `3098868` — 👀 Texas Mobile Device State Law!
- `3109581` — Turn In Your Portfolio (student submissions preserved)
- `3098899` — Help Activity
- `3098931` — Teamwork Exit Ticket

Two imported pages with substantive Ross-authored revisions were retained,
renamed for clarity, and linked into the current modules:

- `1116656` — `ROSS COPY · Welcome Week: Syllabus + Lab Contract`
- `1116640` — `ROSS COPY · Lesson 1: Become a Superhero (Create your Comic Book Cover)`

Their bodies were verified unchanged against the pre-mutation backup. Ross's
edited `Welcome!` front page and `Schedule` page were left untouched.

## Removed archived content

- 34 archived template module containers
- 88 archived/orphan page objects
- all archived assignments except the four protected local assignments
- all archived quizzes
- all archived discussions

The original import remains in Canvas migration history. Full local backup and
identity records are stored under ignored `artifacts/` files:

- `artifacts/ross-local-content-backup-2026-08-19.json`
- `artifacts/ross-old-template-backup-2026-08-19.json`
- `artifacts/ross-reconciliation-map-2026-08-19.json`
- `artifacts/ross-current-release-map-2026-08-19.json`

## Commons status and future updates

The August 19 Commons UI accepted an import request for Ross, but no new Canvas
migration record appeared. A direct server-side reuse attempt (`118099230`)
failed at 0.5% because the stored cartridge URL produced a redirect loop; it
changed no course content.

The 112 new guides were therefore installed as a tagged manual bridge. Each
contains `data-vils-manual-bridge="2026-08-19"` and its source module-item ID.
If a future Commons update supplies canonical guide copies, prove a one-to-one
counterpart in the same module, remove only the marked bridge copies, and keep
the Commons-linked copies. This is the same reconciliation that completed
Duncan's course after Commons eventually supplied canonical guides.

After any future update, verify:

1. 34 current modules and 503 canonical items, plus exactly 8 Ross-local items.
2. Ross's `Welcome!` page remains the front page.
3. All four protected assignment IDs remain present.
4. Both `ROSS COPY` page bodies remain unchanged.
5. Facilitator guides remain unpublished.
6. No exact duplicate page titles remain.

