# VILS CTE Smart Solutions — Public Curriculum Reference

This repository publishes the public reference for the **VILS CTE Smart Solutions** Canvas course used by Irving ISD.

**Public site:** https://elbrielle.github.io/innovative-technology/

Canvas remains the student delivery and grading environment. The site presents the complete ordered course for curriculum review: teacher guides, student directions, assessments, rubrics, linked resources, and approved Canvas files.

## Planning and backlog

The durable curriculum backlog is [`docs/BACKLOG.md`](docs/BACKLOG.md). It records refinement epics, evidence gates, dependencies, and sprint-ready work without changing Canvas or generated public pages.

## Standards reference

The immutable source record for Grade 8 Technology Applications TEKS is [`docs/standards/texas-technology-applications-grade-8-teks-2022.md`](docs/standards/texas-technology-applications-grade-8-teks-2022.md). It preserves the exact wording of current **19 TAC §126.19(c)**. The matching [VILS learning-contract and alignment pattern](docs/standards/vils-learning-contract-pattern.md) defines how the exact standards, lesson objective, and student evidence appear consistently in Canvas facilitator guides and their public-site equivalents.

## Publication boundary

Public is the default. The only protected exception is **OPTION · About Me Smartphone** (Canvas module item `2633987`) and its creator-approved district-only PDF/video. The public course map shows a protected entry so the sequence remains complete, but the activity body and file bytes are never written to this repository.

The fail-closed rule is stored in [`data/publication-policy.json`](data/publication-policy.json). If the protected activity begins referencing a different file set, export stops and requires a human policy review.

## Stable URLs for IPC and other courses

Each Canvas module item has a stable public URL based on its immutable module-item ID:

```text
https://elbrielle.github.io/innovative-technology/lessons/<module_item_id>.html
```

The machine-readable mapping is [`data/public-links.json`](data/public-links.json). IPC builders should look up the Canvas module-item ID there instead of guessing a title slug. A lesson title may change without breaking the public URL.

The earlier title-based lesson URLs remain as generated redirects, so existing bookmarks continue to reach the corresponding stable item-ID page.

## One-command sync

From the repository root:

```bash
python3 scripts/sync_course.py
```

That command:

1. reads live Canvas course `23402` without changing it;
2. exports a deterministic, public-safe snapshot;
3. downloads or reuses every approved referenced file;
4. generates the course map, module pages, stable lesson pages, parity report, and public-link manifest;
5. verifies the repository against the snapshot; and
6. re-reads live Canvas to prove nothing drifted during the build.

The Canvas token is read from `CANVAS_TOKEN` or `~/.canvas_token`. Never commit the token.

## Release workflow

1. Run `python3 scripts/sync_course.py`.
2. Review `git diff --stat` and `data/site-manifest.json`.
3. Run the responsive visual audit described in [`docs/SYNC_WORKFLOW.md`](docs/SYNC_WORKFLOW.md).
4. Run the independent [four-lens curriculum review gate](docs/CURRICULUM_REVIEW_GATE.md) and record consensus in `docs/reviews/`. Any `HOLD` keeps the PR unmerged.
5. Commit and push `main`. GitHub Pages deploys from the existing repository configuration.
6. Verify the public URL and several stable lesson URLs after deployment.

The CI workflow rebuilds the static pages and runs the repository parity gate. It does not need a Canvas token because live Canvas verification remains an intentional release action.

## Credits

Instructional design by Elisha Lucero. Third-party images, videos, tools, and source materials retain the attribution or usage basis included in the lesson, facilitator guide, or speaker notes.
