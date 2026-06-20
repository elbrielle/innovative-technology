#!/usr/bin/env python3
"""
Extract the AR + VR Units from the Irving ISD VILS 2027 Template Common Cartridge
(.imscc) and emit cc-arvr.json for build.cjs to merge into the showcase.

These lessons reference everything via external embeds (YouTube, CoSpaces, Delightex),
so there are no local Common Cartridge file tokens to rewrite — we just lift the body.

Re-run after re-unzipping a fresh .imscc:  python3 extract-cc.py
"""
import xml.etree.ElementTree as ET
import json, re, os, sys

CC = "/tmp/cc-export"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "cc-arvr.json")

# Units to pull, in display order, with factual placeholder blurbs (Elisha's to reword).
WANT = [
    ("Augmented Reality with MergeCube",
     "Augmented reality design with MergeCube and CoSpaces: AR worlds, AR shopping apps, and interactive AR games."),
    ("Virtual Reality in Delightex",
     "Virtual reality builds in Delightex: the basics, 360 images and scenes, and an interactive VR novel."),
]

def ln(tag):  # localname, namespace-agnostic
    return tag.split("}")[-1]

def text_of(el, name):
    for c in el:
        if ln(c.tag) == name:
            return (c.text or "").strip()
    return ""

# 1) imsmanifest: resource identifier -> href (attr or nested <file href>)
man = ET.parse(os.path.join(CC, "imsmanifest.xml")).getroot()
href = {}
for r in man.iter():
    if ln(r.tag) != "resource":
        continue
    ident = r.get("identifier")
    h = r.get("href")
    if not h:
        for c in r:
            if ln(c.tag) == "file" and c.get("href"):
                h = c.get("href")
                break
    if ident:
        href[ident] = h

# 2) module_meta: ordered items per wanted module
mm = ET.parse(os.path.join(CC, "course_settings", "module_meta.xml")).getroot()
modules = {}
for mod in mm:
    if ln(mod.tag) != "module":
        continue
    title = text_of(mod, "title")
    items = []
    for c in mod:
        if ln(c.tag) == "items":
            for it in c:
                d = {ln(f.tag): (f.text or "").strip() for f in it}
                items.append(d)
    modules[title] = items

def body_html(path):
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        html = f.read()
    m = re.search(r"<body[^>]*>(.*)</body>", html, re.S | re.I)
    return (m.group(1) if m else html).strip()

def strip_len(html):
    return len(re.sub(r"<[^>]+>", "", html).strip())

units = []
for name, blurb in WANT:
    items = modules.get(name, [])
    lessons = []
    for d in items:
        if d.get("content_type") not in ("Assignment", "WikiPage"):
            continue
        ref = d.get("identifierref")
        rel = href.get(ref)
        if not rel:
            continue
        path = os.path.join(CC, rel)
        if not os.path.isfile(path):
            continue
        content = body_html(path)
        if strip_len(content) < 120:          # skip LTI stubs / empty guides
            continue
        lessons.append({
            "title": d.get("title", "").strip(),
            "type": d.get("content_type"),
            "content": content,
            "exportId": ref,
        })
    units.append({"name": name, "blurb": blurb, "lessons": lessons})
    print(f"  {name}: {len(lessons)} lessons")

with open(OUT, "w", encoding="utf-8") as f:
    json.dump(units, f, ensure_ascii=False)
print(f"wrote {OUT}")
