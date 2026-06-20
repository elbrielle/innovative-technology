#!/usr/bin/env node
/*
 * im-showcase generator
 * Reads the Canvas export's course-data.js, picks the featured Units, and emits
 * a self-contained static showcase:
 *   index.html            gallery (Units -> lesson cards), cards baked in (visible w/o JS)
 *   lessons/<slug>.html   each featured lesson's real HTML, asset paths localized,
 *                         internal Canvas cross-links rewired to sibling lessons
 *   assets/media/*        only the media those lessons reference
 * styles.css + app.js are hand-authored static files (not generated here).
 *
 * Re-run any time:  node build.cjs
 */
const fs = require("fs");
const path = require("path");

// ---- source export (this session's unzip location) -------------------------
const EXPORT = "/tmp/canvas-export/2026---IM-Bowie-Middle-School-TX-CTE-Lucero-2026-Jun-20_06-22-51-409";
const PROJ = __dirname;

// ---- featured Units, in display order --------------------------------------
// blurbs are plain factual summaries — Elisha's to rewrite in her own voice.
// Two sources merged: source:"bundle" comes from the IM Bowie viewer export
// (course-data.js, by module id); source:"cc" comes from the 2027 VILS template
// Common Cartridge (cc-arvr.json, by module name) — that's where AR + VR live.
const FEATURED = [
  { source: "bundle", id: 56239, blurb: "A complete, fully self-authored pixel micro-animation series in Piskel: an interconnected hub, superhero promise, plot diagram, storyboard, export, and a practice wall." },
  { source: "bundle", id: 57632, blurb: "Graphic design through 1960s pop art, Canva, pictographs, and a full Define / Ideate / Prototype / Share emoji design-thinking project." },
  { source: "bundle", id: 57892, blurb: "3D modeling and printing in TinkerCAD: design your own currency, a favorite toy, and a scaled, buildable dream room." },
  { source: "bundle", id: 58389, blurb: "Hands-on intro to AI image classification with Teachable Machine — train a model, then code with it." },
  { source: "cc", name: "Augmented Reality with MergeCube" },
  { source: "cc", name: "Virtual Reality in Delightex" },
];

// scaffolding detectors -> human tag labels (evidence-based, from lesson HTML)
const SCAF = [
  { key: "Objectives",      re: /objective|learning target|i can\b|by the end|goal[:s]/i },
  { key: "Sentence stems",  re: /sentence stem|sentence frame|sentence starter/i },
  { key: "ESL supports",    re: /\besl\b|language support|word bank|vocabulary|emergent bilingual|sheltered|cognate|glossary/i },
  { key: "Deliverable",     re: /deliverable|turn in|submit|success criteria|checklist|rubric|exit ticket/i },
  { key: "Differentiation", re: /scaffold|level up|extension|challenge|optional/i },
];

// ---- load COURSE_DATA -------------------------------------------------------
const window = {};
eval(fs.readFileSync(path.join(EXPORT, "viewer/course-data.js"), "utf8"));
const COURSE = window.COURSE_DATA;
const modulesById = new Map(COURSE.modules.map((m) => [m.id, m]));

// CC source (AR + VR), extracted from the .imscc by extract-cc.py
const CC_PATH = path.join(PROJ, "cc-arvr.json");
const ccByName = new Map(
  (fs.existsSync(CC_PATH) ? JSON.parse(fs.readFileSync(CC_PATH, "utf8")) : []).map((u) => [u.name, u])
);

// resolve a FEATURED spec to a uniform { uid, name, blurb, items } from either source
function resolveUnit(spec) {
  if (spec.source === "cc") {
    const u = ccByName.get(spec.name);
    if (!u) return null;
    return { uid: slugify(u.name), name: u.name, blurb: spec.blurb || u.blurb, items: u.lessons };
  }
  const mod = modulesById.get(spec.id);
  if (!mod) return null;
  return { uid: String(mod.id), name: mod.name, blurb: spec.blurb, items: mod.items || [] };
}

// ---- output dirs ------------------------------------------------------------
const LESS = path.join(PROJ, "lessons");
const MEDIA = path.join(PROJ, "assets", "media");
fs.rmSync(LESS, { recursive: true, force: true });
fs.rmSync(MEDIA, { recursive: true, force: true });
fs.mkdirSync(LESS, { recursive: true });
fs.mkdirSync(MEDIA, { recursive: true });

// ---- helpers ----------------------------------------------------------------
const slugify = (s) => (s || "").toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/(^-|-$)/g, "").slice(0, 60);
const esc = (s) => (s || "").replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
const stripTags = (s) => (s || "").replace(/<[^>]+>/g, "");
const copied = new Set();
const exportIdToSlug = new Map(); // populated in pass A, used by rewriteAssets in pass B

function resolveExportFile(rawSrc) {
  const clean = decodeURIComponent(rawSrc.replace(/^\.?\//, "").split("?")[0].split("#")[0]);
  const cands = [path.join(EXPORT, clean), path.join(EXPORT, "viewer", clean)];
  return cands.find((c) => { try { return fs.statSync(c).isFile(); } catch { return false; } }) || null;
}
function localizeForLesson(rawSrc) {
  const abs = resolveExportFile(rawSrc);
  if (!abs) return null;
  const base = path.basename(abs);
  if (!copied.has(base)) { fs.copyFileSync(abs, path.join(MEDIA, base)); copied.add(base); }
  return "../assets/media/" + encodeURIComponent(base);
}
function localizeForCard(rawSrc) {
  const rel = localizeForLesson(rawSrc);
  return rel ? rel.replace("../", "") : null;
}

// --- internal Canvas link resolution ----------------------------------------
// Canvas lessons link to each other (hub nav bars, "next module" buttons). Rewire
// those to the sibling lesson doc so the interconnection works in the showcase.
//   by id   — assignments/pages/discussion_topics/g<hash> carry the content
//             exportId, which maps straight to a slug (Piskel hub).
//   by text — modules/items/g<hash> carry a *membership* id the export doesn't
//             expose, so match the link's visible text to a sibling lesson title
//             (Emoji hub: "Open Define Module" / "Abrir Modulo Definir" -> Step 1).
const STOP = new Set("open module modulo abrir go to view the a an your this here lesson step paso click".split(" "));
const SYN = { define: "define", definir: "define", ideate: "ideate", idear: "ideate",
  prototype: "prototype", prototipo: "prototype", share: "share", showcase: "share",
  present: "share", presentar: "share", presentation: "share", compartir: "share" };
function toks(s) {
  return [...new Set(
    s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "")
     .replace(/[^a-z0-9 ]/g, " ").split(/\s+/)
     .filter((w) => w && !STOP.has(w)).map((w) => SYN[w] || w)
  )];
}
function resolveByText(innerHtml, lessons) {
  const t = new Set(toks(innerHtml.replace(/<[^>]+>/g, " ")));
  if (!t.size) return null;
  let best = null, score = 0;
  for (const L of lessons) {
    const s = toks(L.title).filter((w) => t.has(w)).length;
    if (s > score) { score = s; best = L; }
  }
  return score > 0 ? best.slug : null;
}
const INTERNAL = /(^|\/)(assignments|pages|discussion_topics|modules\/items|quizzes)\//i;
function resolveLinks(html, lessons) {
  return html.replace(/<a\b([^>]*?)href="([^"]+)"([^>]*)>([\s\S]*?)<\/a>/gi, (full, pre, href, post, inner) => {
    if (/^(https?:|mailto:|#|about:)/i.test(href)) return full;
    if (resolveExportFile(href)) return full;                 // real local asset (pdf/img) -> localizeAssets
    const g = href.match(/\/(g[0-9a-f]{20,})/i);
    let slug = g && exportIdToSlug.has(g[1]) ? exportIdToSlug.get(g[1]) : null;
    if (!slug && INTERNAL.test(href)) slug = resolveByText(inner, lessons);
    if (slug) {
      // strip target="_blank" so the link navigates inside the lightbox iframe
      // (keeping the hub / nav-bar experience) instead of popping a new tab.
      const attrs = (pre + " " + post).replace(/\s*target\s*=\s*"[^"]*"/gi, " ").replace(/\s+/g, " ").trim();
      return `<a ${attrs} href="${slug}.html">${inner}</a>`;
    }
    if (g || INTERNAL.test(href)) return `<a${pre}href="#"${post} data-canvas-link="${esc(href).slice(0, 80)}">${inner}</a>`;
    return full;
  });
}

// localize local file refs (images, PDFs) to bundled copies; leave external URLs,
// already-resolved sibling links (*.html), and the anchors handled by resolveLinks.
function localizeAssets(html) {
  return html.replace(/(src|href)\s*=\s*"([^"]+)"/gi, (m, attr, val) => {
    if (/^(https?:|data:|mailto:|#|about:)/i.test(val) || /\.html$/i.test(val)) return m;
    const rel = localizeForLesson(val);
    return rel ? `${attr}="${rel}"` : m;
  });
}

// interactive 3D/AR/VR tools (CoSpaces/MergeCube, Delightex, ThingLink) block
// iframe embedding, so they render as a blank box. Swap those iframes for a clean
// "open the scene" launch button instead. YouTube and the rest embed fine, untouched.
function linkifyInteractive(html) {
  return html.replace(/<iframe\b[^>]*?src="([^"]+)"[^>]*?>(?:[\s\S]*?<\/iframe>)?/gi, (m, src) => {
    let host = "";
    try { host = new URL(src).hostname; } catch { return m; }
    if (!/(cospaces\.io|delightex\.com|thinglink\.com)$/i.test(host)) return m;
    const label = /cospaces/i.test(host) ? "CoSpaces / MergeCube" : /delightex/i.test(host) ? "Delightex" : "ThingLink";
    return `<a href="${esc(src)}" target="_blank" rel="noopener" style="display:inline-block;padding:12px 18px;margin:10px 0;background:#3949ab;color:#fff;border-radius:10px;font-weight:600;text-decoration:none">&#9654;&#65039; Open the interactive ${label} scene &rarr;</a>`;
  });
}

// pedagogical order: hubs first, then by sequence prefix (lesson < part < activity <
// step < day), then number ascending; un-numbered items keep their export order.
const PREFIX_ORDER = { lesson: 0, part: 1, activity: 2, step: 3, day: 4 };
function seqKey(title) {
  const t = (title || "").toLowerCase();
  const intro = /\bhub\b/.test(t) ? 0 : 1;
  const m = t.match(/\b(lesson|day|step|activity|part)\s*#?\s*(\d+)/);
  const group = m ? (PREFIX_ORDER[m[1]] ?? 5) : 5;
  const num = m ? parseInt(m[2], 10) : 999;
  return { intro, group, num };
}
function cmp(a, b) {
  const A = seqKey(a.title), B = seqKey(b.title);
  return A.intro - B.intro || A.group - B.group || A.num - B.num;
}

function lessonDoc(title, body) {
  return `<!doctype html>
<html lang="en"><head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>${esc(title)}</title>
<style>
  html,body{margin:0;background:#fff}
  body{padding:18px;font-family:-apple-system,'Segoe UI','Helvetica Neue',Arial,sans-serif;color:#1a1a1a;line-height:1.5;-webkit-text-size-adjust:100%}
  img,video,iframe{max-width:100%;height:auto}
  iframe{border:0;aspect-ratio:16/9;width:100%}
  a{color:#3949ab}
  *{box-sizing:border-box}
</style>
</head><body>
${body}
<script>window.addEventListener("load",function(){try{parent.postMessage({t:"lesson",title:document.title},"*")}catch(e){}});</script>
</body></html>`;
}

const contentful = (it) => it.content && stripTags(it.content).trim().length > 120;

// ---- PASS A: assign slugs + build exportId -> slug map ----------------------
const units = [];
for (const spec of FEATURED) {
  const ru = resolveUnit(spec);
  if (!ru) { console.warn("!! missing unit", spec); continue; }
  const items = ru.items.filter(contentful).sort(cmp);
  const lessons = items.map((it) => {
    const slug = slugify(`${ru.name}-${it.title}`);
    if (it.exportId) exportIdToSlug.set(it.exportId, slug);
    return { it, slug };
  });
  units.push({ id: ru.uid, name: ru.name, blurb: ru.blurb, lessons });
}

// ---- PASS B: write lesson docs + manifest -----------------------------------
let xlinkResolved = 0;
for (const u of units) {
  const unitLessons = u.lessons.map((l) => ({ title: l.it.title, slug: l.slug }));
  u.cards = u.lessons.map(({ it, slug }) => {
    const bodyRaw = it.content;
    const body = linkifyInteractive(localizeAssets(resolveLinks(bodyRaw, unitLessons)));
    xlinkResolved += (body.match(/href="[a-z0-9-]+\.html"/gi) || []).length;
    fs.writeFileSync(path.join(LESS, slug + ".html"), lessonDoc(it.title, body));

    const tags = SCAF.filter((s) => s.re.test(bodyRaw)).map((s) => s.key);
    if (/youtube\.com|youtu\.be|<video/i.test(bodyRaw)) tags.push("Video");
    if ((bodyRaw.match(/<img/gi) || []).length >= 4) tags.push("Visual / step-by-step");

    let thumb = null;
    const im = bodyRaw.match(/<img[^>]+src="([^"]+)"/i);
    if (im && !/^https?:/i.test(im[1])) thumb = localizeForCard(im[1]);

    return { slug, title: it.title, type: it.type, tags, thumb, commons: "#" };
  });
}

// ---- render index.html ------------------------------------------------------
const TYPE_LABEL = { Assignment: "Activity", WikiPage: "Page", DiscussionTopic: "Discussion" };
// Header "Browse everything on Canvas Commons" target. For now this is a single
// shared Commons resource link (Elisha couldn't get a profile-level URL yet).
const COMMONS_PROFILE = "https://lor.instructure.com/resources/01d360231dfe4f24889064bc43b58619?shared";

function cardHTML(l) {
  const thumb = l.thumb
    ? `<span class="card__thumb" style="background-image:url('${l.thumb}')"></span>`
    : `<span class="card__thumb card__thumb--blank" aria-hidden="true">IM</span>`;
  const tags = l.tags.map((t) => `<li class="tag">${esc(t)}</li>`).join("");
  return `<article class="card">
  <button class="card__open" type="button" data-slug="${l.slug}" data-title="${esc(l.title)}" data-commons="${esc(l.commons)}">
    ${thumb}
    <span class="card__body">
      <span class="card__type">${TYPE_LABEL[l.type] || l.type}</span>
      <span class="card__title">${esc(l.title)}</span>
      <ul class="tags">${tags}</ul>
    </span>
  </button>
</article>`;
}

function unitHTML(u) {
  return `<section class="unit" id="unit-${u.id}">
  <div class="unit__head">
    <h2 class="unit__title">${esc(u.name)}</h2>
    <span class="unit__count">${u.cards.length} lesson${u.cards.length === 1 ? "" : "s"}</span>
  </div>
  <p class="unit__blurb">${esc(u.blurb)}</p>
  <div class="grid">
    ${u.cards.map(cardHTML).join("\n    ")}
  </div>
</section>`;
}

const totalLessons = units.reduce((n, u) => n + u.cards.length, 0);
const nav = units.map((u) => `<a href="#unit-${u.id}">${esc(u.name)}</a>`).join("");

const indexHTML = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>CTE Innovative Technology — Curriculum Showcase · Elisha Lucero</title>
<meta name="description" content="Selected units from a CTE Innovative Technology course: animation, graphic design, 3D modeling and printing, AI, AR, and VR. Designed and coded by Elisha Lucero.">
<link rel="stylesheet" href="styles.css">
</head>
<body>
<header class="site-header">
  <div class="wrap">
    <p class="eyebrow">Curriculum &middot; CTE Innovative Technology</p>
    <h1>Designed &amp; coded learning modules</h1>
    <p class="lede">A selection of units from my CTE Innovative Technology course. Each module is designed and built in Canvas using custom HTML and inline CSS, with embedded video, visual scaffolds, sentence stems, ESL supports, and clear deliverables. The goal of these modules is to be self-paced and to encourage student differentiation. Click any lesson to open the real thing. Curriculum may reference freely available resources from Verizon Innovative Learning HQ, MIT RAICA, and others as noted.</p>
    <div class="actions">
      <a class="btn btn--primary" href="${COMMONS_PROFILE}">Browse everything on Canvas Commons &rarr;</a>
    </div>
    <nav class="unitnav">${nav}</nav>
  </div>
</header>

<main class="wrap">
  ${units.map(unitHTML).join("\n  ")}
</main>

<footer class="site-footer">
  <div class="wrap">
    <p>${units.length} Units &middot; ${totalLessons} lessons shown &middot; full course on Canvas Commons.</p>
    <p class="muted">Embedded media and tools are open-licensed and credited to their sources. The instructional design and code shown here are the author's own.</p>
  </div>
</footer>

<!-- lightbox -->
<div class="lightbox" id="lightbox" hidden>
  <div class="lightbox__backdrop" data-close></div>
  <div class="lightbox__panel" role="dialog" aria-modal="true" aria-labelledby="lb-title">
    <div class="lightbox__bar">
      <h2 class="lightbox__title" id="lb-title">Lesson</h2>
      <div class="lightbox__bar-actions">
        <a class="btn btn--ghost" id="lb-commons" href="#" target="_blank" rel="noopener">View on Canvas Commons &rarr;</a>
        <button class="lightbox__close" type="button" data-close aria-label="Close">&times;</button>
      </div>
    </div>
    <div class="lightbox__stage">
      <iframe id="lb-frame" title="Lesson preview" loading="lazy"></iframe>
    </div>
  </div>
</div>

<script src="app.js"></script>
</body>
</html>`;

fs.writeFileSync(path.join(PROJ, "index.html"), indexHTML);

// ---- report -----------------------------------------------------------------
console.log("Built im-showcase:");
units.forEach((u) => console.log(`  • ${u.name}: ${u.cards.length} lessons`));
console.log(`  total lessons: ${totalLessons}`);
console.log(`  media files copied: ${copied.size}`);
console.log(`  cross-links rewired to sibling lessons: ${xlinkResolved}`);
console.log(`  output: ${PROJ}/index.html`);
