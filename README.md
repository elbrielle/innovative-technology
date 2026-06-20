# CTE Innovative Technology — Curriculum Showcase

A selection of units from my CTE Innovative Technology course (Bowie MS, Irving ISD).
Each module is designed and built in Canvas using custom HTML and inline CSS, with
embedded video, visual scaffolds, sentence stems, ESL supports, and clear deliverables.
The modules are built to be self-paced and to encourage student differentiation.

**Live:** https://elbrielle.github.io/innovative-technology/

## What this is

A static showcase: a gallery of Units, each holding its lessons. Click a lesson to open
the real module HTML in a lightbox, video and interactive scenes included. Internal
cross-links (hub nav bars, the Emoji design-thinking flow) work inside the showcase.

## How it's built

Lesson content is generated from Canvas course exports, not hand-maintained:

- `build.cjs` reads the Canvas viewer-bundle export (`course-data.js`) and emits the
  gallery (`index.html`), per-lesson docs (`lessons/`), and bundled media (`assets/media/`).
- `extract-cc.py` pulls the AR + VR units from a Common Cartridge (`.imscc`) into
  `cc-arvr.json`, which `build.cjs` merges in.

Regenerate (with the source exports unzipped in place):

```bash
python3 extract-cc.py   # refresh AR/VR from the .imscc
node build.cjs          # rebuild the whole site
```

## Credits

Curriculum may reference freely available resources from Verizon Innovative Learning HQ,
MIT RAICA, and others as noted. Instructional design by Elisha Lucero.
