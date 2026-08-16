#!/usr/bin/env python3
"""Build the public Innovative Technology curriculum mirror from the snapshot."""

from __future__ import annotations

import hashlib
import html
import json
import re
import shutil
from pathlib import Path
from urllib.parse import unquote, urlparse

from canvas_api import stable_json


ROOT = Path(__file__).resolve().parents[1]
SNAPSHOT_PATH = ROOT / "data" / "course-snapshot.json"
POLICY_PATH = ROOT / "data" / "publication-policy.json"
MANIFEST_PATH = ROOT / "data" / "site-manifest.json"
PUBLIC_LINKS_PATH = ROOT / "data" / "public-links.json"
LEGACY_ALIASES_PATH = ROOT / "data" / "legacy-route-aliases.json"
LESSONS = ROOT / "lessons"
MODULES = ROOT / "modules"
SITE_HOST = "https://elbrielle.github.io/innovative-technology/"
CANVAS_HOST = "verizoninnovativelearning.instructure.com"


def esc(value) -> str:
    return html.escape(str(value or ""), quote=True)


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def canonical_hash(value) -> str:
    return sha256_text(json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")))


def strip_tags(value: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", value or ""))).strip()


def item_role(item: dict) -> str:
    title = (item.get("title") or "").lower()
    metadata = (item.get("resource") or {}).get("metadata") or {}
    if title.startswith("student") or "student guide" in title or "student's guide" in title:
        return "student"
    if (
        "facilitator" in title
        or "teacher guide" in title
        or "teacher reference" in title
        or title.startswith("teacher ")
    ):
        return "teacher"
    if metadata.get("hide_from_students"):
        return "teacher"
    return "student"


def item_flavor(item: dict) -> str:
    title = (item.get("title") or "").lower()
    if item.get("public_state") == "protected":
        return "protected"
    if "parked" in title:
        return "parked"
    if "optional" in title or "option " in title or "flex" in title:
        return "optional"
    return "core"


def item_type_label(item: dict) -> str:
    kind = item.get("type") or "Item"
    return {
        "Page": "Page",
        "Assignment": "Assignment",
        "Discussion": "Discussion",
        "Quiz": "Quiz",
        "ExternalUrl": "External resource",
        "ExternalTool": "External tool",
        "File": "File",
        "SubHeader": "Section",
    }.get(kind, kind)


def build_maps(snapshot: dict, policy: dict) -> dict:
    maps = {
        "item": {},
        "page": {},
        "assignment": {},
        "discussion": {},
        "quiz": {},
        "file": {},
        "route_aliases": {},
        "missing_route_notices": policy.get("missing_route_notices", {}),
        "empty_link_repairs": policy.get("empty_link_repairs", {}),
        "placeholder_link_repairs": {},
    }
    for file_id, row in snapshot["files"].items():
        maps["file"][int(file_id)] = row
    for module in snapshot["modules"]:
        for item in module["items"]:
            maps["item"][int(item["id"])] = item
            if item.get("page_url"):
                maps["page"][item["page_url"]] = item
            if item.get("content_id"):
                if item["type"] == "Assignment":
                    maps["assignment"][int(item["content_id"])] = item
                elif item["type"] == "Discussion":
                    maps["discussion"][int(item["content_id"])] = item
                elif item["type"] == "Quiz":
                    maps["quiz"][int(item["content_id"])] = item
    for slug, rule in policy.get("canvas_route_aliases", {}).items():
        target = maps["item"].get(int(rule["target_module_item_id"]))
        if not target:
            raise RuntimeError(f"Publication-policy route alias {slug} has no target item")
        maps["route_aliases"][slug] = target
    for token, rule in policy.get("placeholder_link_repairs", {}).items():
        target = maps["item"].get(int(rule["target_module_item_id"]))
        if not target:
            raise RuntimeError(f"Publication-policy placeholder repair {token} has no target item")
        maps["placeholder_link_repairs"][token] = target
    return maps


def local_asset_url(file_id: int, maps: dict) -> str | None:
    row = maps["file"].get(file_id)
    if not row:
        return None
    return "../" + row["public_path"]


def file_id_from_url(value: str) -> int | None:
    decoded = html.unescape(unquote(value or ""))
    match = re.search(
        r"(?:/files/|/api/v1/courses/\d+/files/|/media_attachments_iframe/)(\d+)",
        decoded,
        re.I,
    )
    return int(match.group(1)) if match else None


def public_item_url(item: dict) -> str:
    return f"../lessons/{item['id']}.html"


def rewrite_canvas_route(value: str, maps: dict) -> str | None:
    decoded = html.unescape(value or "")
    parsed = urlparse(decoded)
    if parsed.netloc and parsed.netloc.lower() != CANVAS_HOST:
        return None
    path = parsed.path
    match = re.search(r"/courses/\d+/modules/items/(\d+)", path)
    if match and int(match.group(1)) in maps["item"]:
        return public_item_url(maps["item"][int(match.group(1))])
    match = re.search(r"/courses/\d+/pages/([^/?#]+)", path)
    if match and match.group(1) in maps["page"]:
        return public_item_url(maps["page"][match.group(1)])
    if match and match.group(1) in maps["route_aliases"]:
        return public_item_url(maps["route_aliases"][match.group(1)])
    for kind, route in (("assignment", "assignments"), ("discussion", "discussion_topics"), ("quiz", "quizzes")):
        match = re.search(rf"/courses/\d+/{route}/(\d+)", path)
        if match and int(match.group(1)) in maps[kind]:
            return public_item_url(maps[kind][int(match.group(1))])
    if re.search(r"/courses/\d+/modules(?:/|$)", path):
        return "../index.html#course-map"
    return None


def resource_card(file_id: int, maps: dict, label: str | None = None) -> str:
    row = maps["file"].get(file_id)
    if not row:
        return (
            '<span class="mirror-note mirror-note--warning">'
            "This Canvas resource was referenced but is not part of the public release."
            "</span>"
        )
    metadata = row["metadata"]
    name = label or metadata.get("display_name") or metadata.get("filename") or f"Resource {file_id}"
    size = metadata.get("size") or 0
    size_text = f"{size / 1024 / 1024:.1f} MB" if size >= 1024 * 1024 else f"{size / 1024:.0f} KB"
    return (
        f'<a class="mirror-resource" href="{esc(local_asset_url(file_id, maps))}" download>'
        '<span class="mirror-resource__icon" aria-hidden="true">↓</span>'
        f'<span><strong>{esc(name)}</strong><small>{esc(metadata.get("content-type") or "file")} · {size_text}</small></span>'
        "</a>"
    )


def rewrite_body(body: str, maps: dict, unresolved: list[dict], item: dict) -> str:
    if not body:
        return ""

    repairs = list(maps["empty_link_repairs"].get(str(item["id"]), []))
    repair_index = 0

    def repair_empty_link(match: re.Match) -> str:
        nonlocal repair_index
        if repair_index >= len(repairs):
            unresolved.append({"item_id": item["id"], "kind": "empty-link", "target": "#"})
            return match.group(0)
        rule = repairs[repair_index]
        repair_index += 1
        if rule["kind"] == "file":
            target = local_asset_url(int(rule["target_file_id"]), maps)
            if not target:
                raise RuntimeError(f"Empty-link repair for {item['id']} references a missing public file")
        else:
            target = rule["target"]
        return f'href="{esc(target)}"'

    body = re.sub(r'href=["\']#["\']', repair_empty_link, body, flags=re.I)
    body = re.sub(r'\sdata-api-endpoint=["\']#["\']', "", body, flags=re.I)
    if repair_index != len(repairs):
        raise RuntimeError(f"Expected {len(repairs)} empty-link repairs for item {item['id']}, used {repair_index}")

    missing_notices: list[str] = []
    for slug, notice in maps["missing_route_notices"].items():
        if re.search(rf'/pages/{re.escape(slug)}(?:["\'?])', body):
            body = re.sub(
                rf'<a\b([^>]*?)href=["\'][^"\']*/pages/{re.escape(slug)}[^"\']*["\']([^>]*)>([\s\S]*?)</a>',
                rf'<span class="mirror-note mirror-note--warning" id="missing-{slug}">\3 <small>{esc(notice)}</small></span>',
                body,
                flags=re.I,
            )
            missing_notices.append(slug)

    def media_iframe(match: re.Match) -> str:
        tag = match.group(0)
        src_match = re.search(r'\bsrc=["\']([^"\']+)', tag, re.I)
        if not src_match:
            return tag
        source = src_match.group(1)
        file_id = file_id_from_url(source)
        if file_id is None:
            return tag
        row = maps["file"].get(file_id)
        if not row:
            unresolved.append({"item_id": item["id"], "kind": "file", "target": source})
            return resource_card(file_id, maps)
        mime = row["metadata"].get("content-type") or ""
        path = esc(local_asset_url(file_id, maps))
        name = esc(row["metadata"].get("display_name") or "Course media")
        if mime.startswith("video/"):
            return f'<video class="mirror-media" controls preload="metadata"><source src="{path}" type="{esc(mime)}">Download <a href="{path}">{name}</a>.</video>'
        if mime.startswith("audio/"):
            return f'<audio class="mirror-media" controls preload="metadata"><source src="{path}" type="{esc(mime)}">Download <a href="{path}">{name}</a>.</audio>'
        if mime.startswith("image/"):
            return f'<img class="mirror-media" src="{path}" alt="{name}">'
        return resource_card(file_id, maps)

    body = re.sub(r"<iframe\b[^>]*?(?:/>|>[\s\S]*?</iframe>)", media_iframe, body, flags=re.I)

    def attribute(match: re.Match) -> str:
        attr, quote, value = match.group(1), match.group(2), match.group(3)
        if value in maps["placeholder_link_repairs"]:
            return f"{attr}={quote}{public_item_url(maps['placeholder_link_repairs'][value])}{quote}"
        file_id = file_id_from_url(value)
        if file_id is not None:
            local = local_asset_url(file_id, maps)
            if local:
                return f"{attr}={quote}{local}{quote}"
            unresolved.append({"item_id": item["id"], "kind": "file", "target": value})
            return f"{attr}={quote}#{quote}"
        route = rewrite_canvas_route(value, maps)
        if route:
            return f"{attr}={quote}{route}{quote}"
        parsed = urlparse(html.unescape(value))
        if parsed.netloc.lower() == CANVAS_HOST and f"/courses/{maps['course_id']}/" in parsed.path:
            unresolved.append({"item_id": item["id"], "kind": "canvas-route", "target": value})
            return f"{attr}={quote}../index.html#course-map{quote}"
        return match.group(0)

    body = re.sub(r"\b(href|src|data-api-endpoint)=(['\"])(.*?)\2", attribute, body, flags=re.I)
    body = re.sub(r"\sdata-course-type=['\"][^'\"]*['\"]", "", body, flags=re.I)

    def decorative_banner_alt(match: re.Match) -> str:
        tag = match.group(0)
        if re.search(r"\balt\s*=", tag, re.I):
            return tag
        source = re.search(r"\bsrc=['\"]([^'\"]+)", tag, re.I)
        if source and "docs.google.com/drawings/" in source.group(1) and "w=1162" in source.group(1) and "h=100" in source.group(1):
            return re.sub(r"<img\b", '<img alt=""', tag, count=1, flags=re.I)
        return tag

    body = re.sub(r"<img\b[^>]*>", decorative_banner_alt, body, flags=re.I)
    return body


def item_metadata_panel(item: dict) -> str:
    resource = item.get("resource") or {}
    metadata = resource.get("metadata") or {}
    rows: list[tuple[str, str]] = []
    if item.get("type") == "Assignment":
        points = metadata.get("points_possible")
        rows.append(("Points", f"{points:g}" if isinstance(points, (int, float)) else "Not graded"))
        submission = metadata.get("submission_types") or []
        rows.append(("Submission", ", ".join(value.replace("online_", "").replace("_", " ") for value in submission) or "No submission"))
        if metadata.get("omit_from_final_grade"):
            rows.append(("Gradebook", "Formative / omitted"))
    elif item.get("type") == "Quiz":
        rows.append(("Questions", str(metadata.get("question_count") or 0)))
        rows.append(("Points", str(metadata.get("points_possible") or 0)))
    rows.append(("Canvas state", "Published" if item.get("published") else "Unpublished"))
    if not rows:
        return ""
    return '<dl class="lesson-facts">' + "".join(f"<div><dt>{esc(key)}</dt><dd>{esc(value)}</dd></div>" for key, value in rows) + "</dl>"


def site_header(prefix: str = "", current: str = "") -> str:
    def nav_link(key: str, href: str, label: str) -> str:
        active = ' aria-current="page"' if current == key else ""
        return f'<a href="{prefix}{href}"{active}>{label}</a>'

    return f'''<header class="site-header">
  <div class="site-header__inner wrap">
    <a class="site-identity" href="{prefix}index.html" aria-label="Smart Solutions curriculum home">
      <span class="site-identity__district">Irving Independent School District</span>
      <span class="site-identity__course">Smart Solutions</span>
    </a>
    <nav class="site-nav" aria-label="Primary navigation">
      {nav_link("curriculum", "index.html", "Curriculum")}
      {nav_link("about", "about.html", "About")}
    </nav>
  </div>
</header>'''


def site_footer(prefix: str = "") -> str:
    return f'''<footer class="site-footer">
  <div class="site-footer__inner wrap">
    <div>
      <strong>Smart Solutions: Innovative Technology</strong>
      <p>Curriculum developed for Irving ISD by Elisha Lucero.</p>
    </div>
    <nav aria-label="Footer navigation">
      <a href="{prefix}index.html">Curriculum</a>
      <a href="{prefix}about.html">About</a>
      <a href="{prefix}parity.html">Publication status</a>
    </nav>
  </div>
</footer>'''


def shell(
    title: str,
    content: str,
    *,
    description: str = "",
    body_class: str = "",
    prefix: str = "",
    current: str = "",
) -> str:
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta name="color-scheme" content="light">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description or title)}">
  <link rel="stylesheet" href="{prefix}styles.css">
</head>
<body class="{esc(body_class)}">
<a class="skip-link" href="#main-content">Skip to main content</a>
{site_header(prefix, current)}
{content}
{site_footer(prefix)}
<script src="{prefix}app.js" defer></script>
</body>
</html>
'''


def legacy_redirect_document(title: str, target_item_id: int) -> str:
    target = f"{target_item_id}.html"
    return f'''<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="refresh" content="0; url={target}">
  <link rel="canonical" href="{target}">
  <title>{esc(title)} · Moved</title>
</head>
<body>
  <main><p>This lesson has a stable new address. <a href="{target}">Continue to {esc(title)}</a>.</p></main>
</body>
</html>
'''


def lesson_document(item: dict, module: dict, body: str) -> str:
    role = item_role(item)
    flavor = item_flavor(item)
    protected = item.get("public_state") == "protected"
    resource = item.get("resource") or {}
    audience = "Teacher material" if role == "teacher" else "Student material"
    context = [audience, item_type_label(item)]
    if flavor in {"optional", "parked"}:
        context.append("Optional")
    context.append("Published in Canvas" if item.get("published") else "Unpublished in Canvas")
    content = f'''
<header class="page-intro lesson-header">
  <div class="lesson-header__inner">
    <nav class="breadcrumb" aria-label="Breadcrumb"><a href="../index.html">Curriculum</a><span aria-hidden="true">/</span><a href="../modules/{module['id']}.html">{esc(module['name'])}</a></nav>
    <p class="page-kicker">{' · '.join(esc(value) for value in context)}</p>
    <h1 class="page-title">{esc(item['title'])}</h1>
    {item_metadata_panel(item)}
  </div>
</header>
<main class="lesson-main" id="main-content">
  <aside class="reference-note"><strong>Canvas</strong><span>Use Canvas for submissions and grades.</span></aside>
'''
    if protected:
        content += f'''<section class="protected-panel">
  <p class="protected-panel__eyebrow">District-only activity</p>
  <h2>This activity is not available on the public site.</h2>
  <p>{esc(resource.get('public_notice'))}</p>
  <p class="muted">{esc(resource.get('protection_reason'))}</p>
</section>'''
    elif body:
        content += f'<article class="canvas-content">{body}</article>'
    elif item.get("external_url"):
        content += f'''<section class="empty-state">
  <h2>Open the course resource</h2>
  <p><a class="button" href="{esc(item["external_url"])}">Open {esc(item["title"])} <span aria-hidden="true">↗</span></a></p>
</section>'''
    else:
        content += f'''<section class="empty-state">
  <h2>No separate Canvas page</h2>
  <p>This {esc(item_type_label(item).lower())} is listed in the module only.</p>
  <p><a href="../modules/{module['id']}.html">Return to {esc(module['name'])}</a></p>
</section>'''
    content += '''</main>
'''
    return shell(
        item["title"],
        content,
        description=strip_tags(body)[:155],
        body_class="lesson-page",
        prefix="../",
    )


def item_row(item: dict, prefix: str = "../") -> str:
    role = item_role(item)
    flavor = item_flavor(item)
    classes = f"item-row item-row--{role} item-row--{flavor}"
    href = f"{prefix}lessons/{item['id']}.html"
    state = "Published in Canvas" if item.get("published") else "Unpublished in Canvas"
    audience = "Teacher" if role == "teacher" else "Student"
    return f'''<a class="{classes}" href="{href}" data-search="{esc(item['title'].lower())}" data-role="{role}" data-state="{flavor}">
  <span class="item-row__position" aria-hidden="true">{int(item.get('position') or 0):02d}</span>
  <span class="item-row__body"><strong>{esc(item['title'])}</strong><span class="item-row__meta">{esc(audience)} · {esc(item_type_label(item))} · {esc(state)}</span></span>
  <span class="item-row__arrow" aria-hidden="true">→</span>
</a>'''


def module_document(module: dict) -> str:
    rows = []
    for item in module["items"]:
        if item["type"] == "SubHeader":
            rows.append(f'<h2 class="module-subheader">{esc(item["title"])}</h2>')
        else:
            rows.append(item_row(item))
    content = f'''
<header class="page-intro module-hero"><div class="wrap">
  <nav class="breadcrumb" aria-label="Breadcrumb"><a href="../index.html">Curriculum</a><span aria-hidden="true">/</span><span>Module {module['position']}</span></nav>
  <p class="page-kicker">Module {module['position']} · {'Published in Canvas' if module.get('published') else 'Unpublished in Canvas'}</p>
  <h1 class="page-title">{esc(module['name'])}</h1>
  <p>{len(module['items'])} items in Canvas order.</p>
</div></header>
<main class="wrap module-page__main" id="main-content">
  <div class="module-list" aria-label="Ordered module items">{''.join(rows)}</div>
</main>'''
    return shell(module["name"], content, body_class="module-page", prefix="../")


def course_sections(modules: list[dict]) -> list[tuple[str, str, list[dict]]]:
    last_sw6 = max(
        (int(module["position"]) for module in modules if (module.get("name") or "").upper().startswith("SW6")),
        default=0,
    )
    grouped: list[tuple[str, str, list[dict]]] = []
    ordinal = {"1": "1st", "2": "2nd", "3": "3rd", "4": "4th", "5": "5th", "6": "6th"}
    current_key = "six-weeks-1"
    current_label = "1st six weeks"
    for module in modules:
        name = module.get("name") or ""
        match = re.match(r"SW([1-6])\b", name, re.I)
        if match:
            number = match.group(1)
            current_key = f"six-weeks-{number}"
            current_label = f"{ordinal[number]} six weeks"
        elif int(module["position"]) > last_sw6:
            current_key = "additional-enrichment"
            current_label = "Additional enrichment"
        if not grouped or grouped[-1][0] != current_key:
            grouped.append((current_key, current_label, []))
        grouped[-1][2].append(module)
    return grouped


def module_entry(module: dict) -> str:
    visible_items = [item for item in module["items"] if item["type"] != "SubHeader"]
    search_text = " ".join([module["name"], *(item["title"] for item in visible_items)]).lower()
    teacher_count = sum(item_role(item) == "teacher" for item in visible_items)
    student_count = len(visible_items) - teacher_count
    return f'''<li class="module-entry" id="module-{module['id']}" data-module data-search="{esc(search_text)}">
  <a href="modules/{module['id']}.html">
    <span class="module-entry__number" aria-hidden="true">{int(module['position']):02d}</span>
    <span class="module-entry__body"><strong>{esc(module['name'])}</strong><span>{len(visible_items)} items · {teacher_count} teacher · {student_count} student</span></span>
    <span class="module-entry__arrow" aria-hidden="true">→</span>
  </a>
</li>'''


def index_document(snapshot: dict) -> str:
    modules = snapshot["modules"]
    item_count = sum(len(module["items"]) for module in modules)
    public_items = sum(1 for module in modules for item in module["items"] if item.get("public_state") == "public")
    protected_items = item_count - public_items
    sections = []
    section_nav = []
    for key, label, section_modules in course_sections(modules):
        section_items = sum(len(module["items"]) for module in section_modules)
        section_nav.append(f'<a href="#{key}">{esc(label)}</a>')
        sections.append(f'''
<section class="course-section" id="{esc(key)}" data-course-section>
  <header class="course-section__heading">
    <div><p class="section-number">{len(section_modules)} modules</p><h2>{esc(label)}</h2></div>
    <p>{section_items} ordered items</p>
  </header>
  <ol class="module-directory">{''.join(module_entry(module) for module in section_modules)}</ol>
</section>''')
    generated = snapshot["generated_at"].replace("T", " ").replace("+00:00", " UTC")
    content = f'''
<header class="page-intro site-hero"><div class="wrap">
  <p class="page-kicker">Irving ISD · VILS 2027</p>
  <h1 class="page-title">Smart Solutions: Innovative Technology</h1>
  <p class="lede">Public course sequence for Irving ISD's Smart Solutions curriculum.</p>
</div></header>
<main class="wrap" id="main-content">
  <span id="course-map" class="anchor-target" aria-hidden="true"></span>
  <nav class="section-nav" aria-label="Six-weeks sections">{''.join(section_nav)}</nav>
  <section class="course-tools" aria-label="Search the curriculum">
    <label for="course-search">Find a module or lesson</label>
    <input id="course-search" type="search" placeholder="Try circuits, robotics, Canva, or teacher guide" autocomplete="off">
    <p id="search-status" class="search-status" aria-live="polite">Showing all {len(modules)} modules.</p>
  </section>
{''.join(sections)}
  <aside class="publication-note"><strong>District-only material</strong><span>One optional activity requires district Canvas access.</span></aside>
</main>
'''
    return shell(
        "Smart Solutions curriculum · Irving ISD",
        content,
        description="Irving ISD Smart Solutions curriculum reference with modules, teacher guides, student lessons, assessments, and approved course resources.",
        current="curriculum",
    )


def about_document(snapshot: dict) -> str:
    generated = snapshot["generated_at"].replace("T", " ").replace("+00:00", " UTC")
    content = f'''
<header class="page-intro"><div class="wrap">
  <p class="page-kicker">Smart Solutions curriculum</p>
  <h1 class="page-title">About this curriculum</h1>
  <p class="lede">Public course sequence and approved files for Smart Solutions.</p>
</div></header>
<main class="wrap about-main" id="main-content">
  <section><h2>Course content</h2><p>Visual design, fabrication, coding, circuits, artificial intelligence, robotics, extended reality, communication projects, and a capstone. Modules include teacher guides, student directions, assignments, assessments, rubrics, and approved course files.</p></section>
  <section><h2>Authorship and sources</h2><p>Elisha Lucero developed the course for Irving ISD. Lessons also use district materials, program resources, platform documentation, and credited third-party media. Attributions remain with the lesson or file where each source is used.</p></section>
  <section><h2>Navigation</h2><p>Modules and items follow Canvas order.</p></section>
  <section><h2>Canvas access</h2><p>Canvas is the course record for submissions and grades. District-only and restricted materials are excluded from the public site.</p></section>
  <section class="about-status"><h2>Current snapshot</h2><p>{esc(generated)} · <a href="parity.html">Publication status</a></p></section>
</main>'''
    return shell(
        "About the Smart Solutions curriculum · Irving ISD",
        content,
        description="Course scope, authorship, sources, navigation, and access information for the Irving ISD Smart Solutions curriculum.",
        current="about",
    )


def parity_document(snapshot: dict, manifest: dict) -> str:
    generated = snapshot["generated_at"].replace("T", " ").replace("+00:00", " UTC")
    content = f'''
<header class="page-intro"><div class="wrap"><p class="page-kicker">Site status</p><h1 class="page-title">Publication status</h1></div></header>
<main class="wrap parity-main" id="main-content">
  <section class="parity-status"><span class="parity-status__mark" aria-hidden="true">✓</span><div><h2>Matches the saved Canvas snapshot</h2><p>{esc(generated)}</p></div></section>
  <section class="status-details"><h2>Checked</h2><ul><li>{manifest['counts']['modules']} modules and {manifest['counts']['items']} course items</li><li>Lesson content, settings, rubrics, and public files</li><li>Links and public lesson addresses</li><li>District-only exclusions</li></ul></section>
  <p class="status-return"><a href="index.html">Return to the curriculum</a></p>
</main>'''
    return shell("Publication status · Smart Solutions", content)


def main() -> None:
    snapshot = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    policy = json.loads(POLICY_PATH.read_text(encoding="utf-8"))
    maps = build_maps(snapshot, policy)
    legacy_aliases = json.loads(LEGACY_ALIASES_PATH.read_text(encoding="utf-8"))
    maps["course_id"] = snapshot["source"]["course_id"]
    unresolved: list[dict] = []

    shutil.rmtree(LESSONS, ignore_errors=True)
    shutil.rmtree(MODULES, ignore_errors=True)
    LESSONS.mkdir(parents=True, exist_ok=True)
    MODULES.mkdir(parents=True, exist_ok=True)

    pages: dict[str, dict] = {}
    for module in snapshot["modules"]:
        module_html = module_document(module)
        module_path = f"modules/{module['id']}.html"
        (ROOT / module_path).write_text(module_html, encoding="utf-8")
        pages[module_path] = {"sha256": sha256_text(module_html), "kind": "module", "canvas_id": module["id"]}
        for item in module["items"]:
            if item["type"] == "SubHeader":
                continue
            resource = item.get("resource") or {}
            transformed = rewrite_body(resource.get("body") or "", maps, unresolved, item)
            lesson_html = lesson_document(item, module, transformed)
            lesson_path = f"lessons/{item['id']}.html"
            (ROOT / lesson_path).write_text(lesson_html, encoding="utf-8")
            pages[lesson_path] = {
                "sha256": sha256_text(lesson_html),
                "kind": "item",
                "canvas_id": item["id"],
                "canvas_body_sha256": resource.get("body_sha256") or resource.get("private_body_sha256"),
                "public_state": item.get("public_state"),
            }

    item_by_id = maps["item"]
    for filename, target_item_id in legacy_aliases.items():
        if not re.fullmatch(r"[a-z0-9-]+\.html", filename):
            raise RuntimeError(f"Unsafe legacy lesson alias filename: {filename}")
        target = item_by_id.get(int(target_item_id))
        if not target or target.get("type") == "SubHeader":
            raise RuntimeError(f"Legacy lesson alias {filename} has no public lesson target {target_item_id}")
        redirect_html = legacy_redirect_document(target["title"], int(target_item_id))
        redirect_path = f"lessons/{filename}"
        (ROOT / redirect_path).write_text(redirect_html, encoding="utf-8")
        pages[redirect_path] = {
            "sha256": sha256_text(redirect_html),
            "kind": "legacy_redirect",
            "canvas_id": int(target_item_id),
        }

    index_html = index_document(snapshot)
    (ROOT / "index.html").write_text(index_html, encoding="utf-8")
    pages["index.html"] = {"sha256": sha256_text(index_html), "kind": "index"}

    about_html = about_document(snapshot)
    (ROOT / "about.html").write_text(about_html, encoding="utf-8")
    pages["about.html"] = {"sha256": sha256_text(about_html), "kind": "about"}

    site_semantic = {
        "snapshot_sha256": snapshot["semantic_sha256"],
        "pages": pages,
        "files": {file_id: {"sha256": row["sha256"], "path": row["public_path"]} for file_id, row in snapshot["files"].items()},
        "unresolved": unresolved,
    }
    manifest = {
        "schema_version": 1,
        "snapshot_sha256": snapshot["semantic_sha256"],
        "counts": {
            "modules": len(snapshot["modules"]),
            "items": sum(len(module["items"]) for module in snapshot["modules"]),
            "item_pages": sum(1 for row in pages.values() if row["kind"] == "item"),
            "public_files": len(snapshot["files"]),
            "protected_items": sum(1 for module in snapshot["modules"] for item in module["items"] if item.get("public_state") == "protected"),
        },
        "pages": pages,
        "unresolved": unresolved,
        "site_sha256": canonical_hash(site_semantic),
    }
    parity_html = parity_document(snapshot, manifest)
    (ROOT / "parity.html").write_text(parity_html, encoding="utf-8")
    manifest["pages"]["parity.html"] = {"sha256": sha256_text(parity_html), "kind": "parity"}
    MANIFEST_PATH.write_text(stable_json(manifest), encoding="utf-8")
    public_links = {
        "schema_version": 1,
        "site_base": SITE_HOST,
        "canvas_snapshot_sha256": snapshot["semantic_sha256"],
        "items": [
            {
                "module_id": module["id"],
                "module_position": module["position"],
                "module_name": module["name"],
                "module_item_id": item["id"],
                "item_position": item["position"],
                "title": item["title"],
                "type": item["type"],
                "published_in_canvas": item.get("published"),
                "public_state": item.get("public_state"),
                "url": f"{SITE_HOST}lessons/{item['id']}.html" if item["type"] != "SubHeader" else f"{SITE_HOST}modules/{module['id']}.html",
            }
            for module in snapshot["modules"]
            for item in module["items"]
        ],
    }
    PUBLIC_LINKS_PATH.write_text(stable_json(public_links), encoding="utf-8")
    print(stable_json({"manifest": str(MANIFEST_PATH), **manifest["counts"], "unresolved": len(unresolved), "site_sha256": manifest["site_sha256"]}))


if __name__ == "__main__":
    main()
