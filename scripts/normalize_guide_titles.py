#!/usr/bin/env python3
"""Normalize Canvas source titles without changing page/module-item identity."""

from __future__ import annotations

import argparse
import re

from canvas_api import Canvas, env_course_id


GUIDE_RE = re.compile(r"facilitator|teacher guide|teacher run card", re.I)
UNIT_EXCLUDED = {30, 31, 32, 33, 34}


def unit_name(module_name: str) -> str:
    name = re.sub(r"^(?:SW\d+|OPTIONAL/FLEX|Enrichment)\s*·\s*", "", module_name)
    return re.sub(r"\s*\([^)]*\)$", "", name).strip()


def facilitator_name(title: str) -> str:
    title = re.sub(r"^Teacher Run Card:\s*", "Facilitator Guide: ", title, flags=re.I)
    title = re.sub(r"^Teacher Guide\s*[·:]\s*", "Facilitator Guide: ", title, flags=re.I)
    title = re.sub(r"^Facilitator['’]s Guide(?: and Materials)?:\s*", "Facilitator Guide: ", title, flags=re.I)
    title = re.sub(r"^Facilitator['’]s Guide(?: and Materials)?\s*", "Facilitator Guide: ", title, flags=re.I)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    canvas = Canvas()
    course_id = env_course_id()
    changes = []
    for module in canvas.paged(f"/courses/{course_id}/modules?per_page=100"):
        items = canvas.paged(f"/courses/{course_id}/modules/{module['id']}/items?per_page=100")
        guide_items = [item for item in items if GUIDE_RE.search(item['title'])]
        for index, item in enumerate(guide_items):
            if index == 0 and module['position'] not in UNIT_EXCLUDED:
                new_title = f"Unit at a Glance: {unit_name(module['name'])}"
            else:
                new_title = facilitator_name(item['title'])
            if new_title != item['title']:
                changes.append((module, item, new_title))
    for module, item, title in changes:
        print(f"{'APPLY' if args.apply else 'DRY-RUN'} [{module['position']:02d}] {item['title']} -> {title}")
        if args.apply:
            page = canvas.get(f"/courses/{course_id}/pages/{item['page_url']}")
            canvas.request("PUT", f"/courses/{course_id}/pages/{item['page_url']}", {"wiki_page[title]": title})
            canvas.request(
                "PUT",
                f"/courses/{course_id}/modules/{module['id']}/items/{item['id']}",
                {"module_item[title]": title},
            )
    print(f"changes: {len(changes)}")


if __name__ == "__main__":
    main()
