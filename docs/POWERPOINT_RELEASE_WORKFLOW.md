# PowerPoint storage and release workflow

Run this workflow before publishing a new or revised deck to Canvas, Drive,
or Commons. Keep the teacher's PowerPoint download and native Google Slides
copy options.

For teaching content and design, first follow the
[slide authoring standard](SLIDE_AUTHORING_STANDARD.md) and its
[approved exemplars](exemplars/graphic-design/README.md). Storage optimization
must preserve the teaching sequence and interactions, not merely the pixels.

## Preserve the lesson

Work on a copy and archive the original outside Canvas and outside the public
site. Keep slide order, text, notes, editable objects, animations, embedded
fonts, and image crops. The approved Pop Art final work slide is protected;
its slide XML, relationships, and image bytes must remain unchanged. Preserve
the approved History of Emoji and Unicode Consortium masters.

## Images and projection

Use JPEG for suitable opaque photographic images and PNG for transparency,
screenshots, line art, and small text. Do not use WebP in cross-platform
PowerPoint releases: Google's Slides API documents PNG, JPEG, and GIF support,
and the project's earlier WebP import lost an image.

Keep images only as large as their maximum display needs, accounting for crop.
A full-slide 16:9 image needs up to 3840 × 2160 pixels for 4K; an image occupying
half the slide width needs about 1920 display pixels before crop allowance.
Never upscale a small source to claim 4K quality. Avoid a universal 96/150-DPI
setting: on-slide size and crop determine the useful pixels.

The current conservative optimizer **does not downsample**. It retains every
pixel dimension, tries lossless PNG compression, and can encode an
explicitly reviewed photographic PNG as quality-98 JPEG with full chroma.
JPEG conversion requires the exact package part name; there is no blanket
convert-all-images switch. Keep whole-slide images containing text lossless. It accepts JPEG only if size
savings and pixel-error checks pass. Those checks supplement visual review;
they do not prove small text or art remains acceptable. Color metadata the
optimizer cannot safely preserve is held. Existing JPEGs are not recompressed.
It also consolidates byte-identical media. Do not remove fonts automatically;
that can change how text appears on another teacher's computer.

```bash
# Use the bundled Python runtime with Pillow installed.
python3 scripts/optimize_pptx.py source.pptx candidate.pptx \
  --report candidate.optimization.json
# Protect the approved Pop Art work slide when processing that deck:
python3 scripts/optimize_pptx.py source.pptx candidate.pptx \
  --jpeg-part ppt/media/image.png --protect-slide 17 --report candidate.optimization.json
```

## Review before release

- Review any deck over 20 MB, image over 1 MB, and repeated REVIEW/v2/v3 file.
  These are review triggers, not permission to discard detail or delete files.
- Render the original and candidate. Inspect every changed slide, including
  crops and dense text at intended projection size; inspect the protected
  slide and animations separately.
- Verify package relationships/content types and byte-identical slide XML,
  notes, fonts, and protected assets. Check the native Google Slides import
  when its master changes. Preserve source attribution.
- Record original/new size, savings, hashes, visual findings, and approved
  exceptions. Run `python3 scripts/test_optimize_pptx.py` after optimizer changes.

## Retire older source files safely

A filename containing REVIEW or v2 does not establish that it is obsolete.
Scan all Canvas pages, assignments, discussions, announcements, module file
items, syllabus, quiz questions, and structured attachment IDs, plus links in
Office documents and PDFs. Scan unpublished and unmoduled items too. Hold any
file with an unresolved reference or uncertain purpose.

Before deleting an authorized unused source file, download its live bytes to a
private archive, verify its SHA-256 against the backup, and record its name,
Canvas ID, metadata, and reference audit. Canvas file deletion is irreversible;
a backup can restore bytes but does not promise the original Canvas file ID.
Recheck references and metadata immediately before removal. Never delete files
from teacher destination courses as part of source cleanup.

After source maintenance, rebuild and verify the public mirror, update any
changed PowerPoint release in Drive, and update the existing Commons resource.
Archive old releases outside Canvas; leaving them in an Archive folder inside
the source course still makes them part of a full course export. Follow the
separate course-specific approval gate for Irving fleet updates.

Sources: [Google Slides image requirements](https://developers.google.com/workspace/slides/api/reference/rest/v1/presentations/request),
[Microsoft PowerPoint compression](https://support.microsoft.com/en-us/powerpoint/reduce-the-file-size-of-your-powerpoint-presentations),
[Canvas file deletion API](https://developerdocs.instructure.com/services/canvas/resources/files).
