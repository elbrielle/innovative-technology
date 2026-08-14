# Canvas and public-site parity workflow

## Source of truth

The live Irving 2027 Canvas course (`23402`) is the instructional source. This repository is a generated public review surface, not a second authoring system.

Do not hand-edit files in `lessons/`, `modules/`, `index.html`, `parity.html`, `data/course-snapshot.json`, or `data/public-links.json`. Change Canvas first, then sync.

Legacy title-based lesson links are declared in `data/legacy-route-aliases.json` and regenerated as redirects. Keep an alias when an older public URL may already be bookmarked; point it to the stable Canvas module-item ID.

## What parity covers

The snapshot pins:

- course, module, module-item, title, order, route, and publication state;
- page, assignment, discussion, and quiz bodies;
- assignment grading and submission metadata;
- rubric criteria and settings returned with assignments;
- Classic Quiz question and answer contracts as hashes, without publishing answer text;
- referenced Canvas file metadata and exact downloaded bytes; and
- the explicit public/protected publication policy.

The generated-site verifier checks all expected pages/assets, hashes every public file, validates relative links and fragments, rejects authenticated course links, and confirms that the protected phone files were not exported.

`verify_live.py` is read-only. It refetches the live projections and fails when Canvas has changed since the snapshot.

## Intentional link repairs

Some inherited Canvas bodies contain stale or empty links. Public-safe repairs live in `data/publication-policy.json`, with a reason for each one. The generator currently repairs:

- the former Career Fair teacher-guide slug to the current guide;
- the missing Spanish Career Fair planning-sheet link to the current district organizer;
- two empty CoSpaces fallback/example links; and
- five literal Stop Motion `YOUR_CANVAS_LINK_*` placeholders to their real module items.

The missing Spanish Vision Board page is not fabricated. The public mirror shows a visible source-course notice in place of its dead link.

When Canvas is later corrected, remove the matching repair rule and run the full sync. The verifier will catch stale or unnecessary mappings.

## The protected About Me Phone activity

The public page may list the activity title and explain where authorized teachers can find it. It must not include:

- the Canvas body;
- the phone PDF bytes;
- the demonstration video bytes; or
- a public download link to either file.

Any change to the protected activity's exact referenced file-ID set stops export.

## Responsive review checklist

Serve the repository locally, then run the Playwright gate from an environment where Playwright is available:

```bash
python3 -m http.server 8765 --bind 127.0.0.1
node scripts/visual_audit.mjs
```

The audit visits every generated page at 390 pixels, exercises Canvas-style tabs, checks local images and links, and writes representative desktop/phone screenshots under the ignored `tmp/site-visual-audit/` folder.

Before deployment, inspect at least:

- course index and search/filter controls;
- a full module page;
- a handcrafted visual lesson;
- a dense inherited VILS lesson;
- a teacher facilitator guide;
- a page with local video or downloadable files;
- a quiz/assignment contract page; and
- the protected phone notice.

Test desktop, tablet, and 390-pixel phone widths. Stop release for clipped text, horizontal page overflow, broken tabs, empty links, hidden instructional content, unreadable color contrast, or a file that still requires Canvas authentication.

## Downstream IPC use

IPC link builders should consume `data/public-links.json`. Resolve by `module_item_id`; do not scrape lesson titles or copy Canvas URLs. The protected item remains in the manifest with `public_state: protected`, allowing downstream tooling to reject or label it explicitly.
