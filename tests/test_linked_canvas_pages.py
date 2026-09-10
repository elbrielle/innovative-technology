"""A public page graph stays complete without becoming a module sequence."""
import copy
import io
import json
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import export_canvas as export
import build_site as build
import verify_site
import verify_live

HOST = "https://verizoninnovativelearning.instructure.com"
COURSE = 23402


def page(page_id, slug, body):
    return {"page_id": page_id, "url": slug, "title": slug, "published": True, "body": body}


class FakeCanvas:
    base = HOST + "/api/v1"

    def __init__(self):
        self.calls = []
        self.pages = {
            "root": page(100, "root", '<a href="/courses/23402/pages/nested%20%7C">Next</a>'
                         '<a href="/courses/23402/pages/200">Protected by ID</a>'
                         '<a href="/courses/23402/pages/private">Protected by slug</a>'
                         '<a href="https://outside.example/courses/23402/pages/external">External</a>'
                         '<a href="https://verizoninnovativelearning.instructure.com/courses/9/pages/other">Other course</a>'
                         '<a href="/courses/23402/pages/known-missing">Expected missing route</a>'),
            "private": page(200, "private", '<p>PRIVATE MATERIAL</p><a href="/courses/23402/pages/secret-child">Private child</a>'
                            '<img src="/courses/23402/files/999/preview">'),
            "nested%20%7C": page(300, "nested |", '<a href="/courses/23402/pages/deep#target">Deeper</a>'
                                '<a href="/courses/23402/pages/root">Back</a>'
                                '<a href="/courses/23402/files/222/download#page=2">Document</a>'),
            "deep": page(400, "deep", '<h2 id="target">Nested content</h2><a href="/courses/23402/pages/300">Cycle</a>'),
        }
        self.file = {"id": 222, "size": 1, "filename": "document.pdf", "content-type": "application/pdf"}
        self.module = {"id": 1, "name": "Exploration", "position": 1, "published": True}
        self.items = [{"id": 10, "position": 1, "type": "Page", "title": "root", "page_url": "root", "published": True},
                      {"id": 11, "position": 2, "type": "Page", "title": "private", "page_url": "private", "published": True}]

    def get(self, path):
        self.calls.append(path)
        if path == "/files/222":
            return copy.deepcopy(self.file)
        prefix = f"/courses/{COURSE}/pages/"
        if not path.startswith(prefix) or path[len(prefix):] not in self.pages:
            raise AssertionError(f"Unexpected fetch outside the allowed graph: {path}")
        return copy.deepcopy(self.pages[path[len(prefix):]])

    def paged(self, path):
        if path == f"/courses/{COURSE}/modules?per_page=100":
            return [copy.deepcopy(self.module)]
        if path == f"/courses/{COURSE}/modules/1/items?per_page=100":
            return copy.deepcopy(self.items)
        raise AssertionError(path)


def fixture():
    canvas = FakeCanvas()
    policy = {"course_id": COURSE, "protected_items": [{"module_item_id": 11}],
              "missing_route_notices": {"known-missing": "This source page is unavailable."}}
    resources = {item["id"]: {"kind": "page", "metadata": export.page_projection(canvas.pages[item["page_url"]]),
                              "body": canvas.pages[item["page_url"]]["body"]}
                 for item in canvas.items}
    linked = export.collect_linked_pages(canvas, canvas.items, resources, policy, COURSE)
    items = []
    for raw in canvas.items:
        item = export.item_projection(raw)
        resource = copy.deepcopy(resources[item["id"]])
        body = resource["body"]
        item["public_state"] = "protected" if item["id"] == 11 else "public"
        if item["id"] == 11:
            resource.update(body="", private_body_sha256=export.sha256_text(body), private_body_length=len(body),
                            public_notice="District only", protection_reason="Restricted license")
        else:
            resource.update(body_sha256=export.sha256_text(body), referenced_file_ids=export.referenced_file_ids(body))
        item["resource"] = resource
        items.append(item)
    snapshot = {"schema_version": 1, "generated_at": "2026-09-10T00:00:00+00:00",
                "source": {"course_id": COURSE, "canvas_host": HOST}, "course": {"name": "Test course"},
                "publication_policy": policy, "modules": [{**export.module_projection(canvas.module), "items": items}],
                "linked_pages": linked, "protected_file_ids": [999],
                "files": {"222": {"metadata": export.file_metadata(canvas.file, None),
                                  "public_path": "assets/canvas/222-document.pdf", "sha256": export.sha256_bytes(b"x")}}}
    snapshot["semantic_sha256"] = export.canonical_hash({k: v for k, v in snapshot.items() if k != "generated_at"})
    return canvas, snapshot


class LinkedCanvasPagesTests(unittest.TestCase):
    def test_nested_chain_cycle_and_protected_external_boundaries(self):
        canvas, snapshot = fixture()
        linked = snapshot["linked_pages"]
        self.assertEqual([p["page_id"] for p in linked], [300, 400])
        self.assertEqual(canvas.calls, [f"/courses/{COURSE}/pages/nested%20%7C", f"/courses/{COURSE}/pages/deep"])
        self.assertEqual(linked[0]["resource"]["referenced_file_ids"], [222])
        self.assertTrue(all("id" not in p for p in linked))  # real page IDs, no invented placements
        self.assertNotIn("PRIVATE MATERIAL", json.dumps(linked))
        maps = build.build_maps(snapshot, snapshot["publication_policy"])
        self.assertEqual(build.rewrite_canvas_route(f"{HOST}/courses/{COURSE}/pages/nested%20%7C#target", maps),
                         "../pages/300.html#target")
        self.assertEqual(build.rewrite_canvas_route(f"/courses/{COURSE}/pages/200", maps), "../lessons/11.html")
        self.assertEqual(build.rewrite_canvas_route(f"{HOST}/api/v1/courses/{COURSE}/pages/nested%2520%257C", maps),
                         "../pages/300.html")
        self.assertIsNone(build.rewrite_canvas_route(f"{HOST}/courses/9/pages/nested%20%7C", maps))
        body = '<a href="https://outside.example/files/222">External file</a><a href="/courses/9/files/222">Other course file</a>'
        self.assertEqual(build.rewrite_body(body, maps, [], linked[0]), body)
        self.assertIsNone(export.canvas_page_slug(f"https://outside.example/courses/{COURSE}/pages/deep", COURSE, HOST))
        self.assertIsNone(export.canvas_page_slug(f"/courses/{COURSE}/pages/..%2fprivate", COURSE, HOST))

    def test_site_and_live_verifiers_cover_nested_content(self):
        canvas, snapshot = fixture()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "data").mkdir()
            (root / "assets/canvas").mkdir(parents=True)
            (root / "assets/canvas/222-document.pdf").write_bytes(b"x")
            snapshot_path = root / "data/course-snapshot.json"
            policy_path = root / "data/publication-policy.json"
            aliases_path = root / "data/legacy-route-aliases.json"
            snapshot_path.write_text(json.dumps(snapshot))
            policy_path.write_text(json.dumps(snapshot["publication_policy"]))
            aliases_path.write_text("{}")
            with patch.multiple(build, ROOT=root, SNAPSHOT_PATH=snapshot_path, POLICY_PATH=policy_path,
                                LEGACY_ALIASES_PATH=aliases_path, MANIFEST_PATH=root / "data/site-manifest.json",
                                PUBLIC_LINKS_PATH=root / "data/public-links.json", LESSONS=root / "lessons",
                                MODULES=root / "modules", PAGES=root / "pages"), redirect_stdout(io.StringIO()):
                build.main()
            manifest = json.loads((root / "data/site-manifest.json").read_text())
            links = json.loads((root / "data/public-links.json").read_text())
            self.assertEqual(manifest["counts"]["items"], 2)
            self.assertEqual(manifest["counts"]["linked_pages"], 2)
            self.assertEqual({row["module_item_id"] for row in links["items"]}, {10, 11})
            self.assertEqual({p.name for p in (root / "pages").glob("*.html")}, {"300.html", "400.html"})
            self.assertIn('../pages/400.html#target', (root / "pages/300.html").read_text())
            self.assertIn('../assets/canvas/222-document.pdf#page=2', (root / "pages/300.html").read_text())
            self.assertNotIn("PRIVATE MATERIAL", (root / "lessons/11.html").read_text())
            self.assertEqual(manifest["unresolved"], [])
            failures = []
            verify_site.check_linked_pages(snapshot, manifest, links, failures)
            self.assertEqual(failures, [])
            changed = copy.deepcopy(snapshot)
            changed["linked_pages"][1]["resource"]["body"] += "Unrecorded change"
            verify_site.check_linked_pages(changed, manifest, links, failures)
            self.assertTrue(any("body hash differs" in failure for failure in failures))
            with patch.multiple(verify_live, ROOT=root, SNAPSHOT_PATH=snapshot_path), patch.object(verify_live, "Canvas", return_value=canvas), redirect_stdout(io.StringIO()):
                verify_live.main()
                canvas.pages["deep"]["body"] += "Live nested change"
                with self.assertRaises(SystemExit):
                    verify_live.main()


if __name__ == "__main__":
    unittest.main()
