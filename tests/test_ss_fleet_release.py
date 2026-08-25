import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "ss_fleet_release.py"
SPEC = importlib.util.spec_from_file_location("ss_fleet_release", SCRIPT)
ss_fleet_release = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules["ss_fleet_release"] = ss_fleet_release
SPEC.loader.exec_module(ss_fleet_release)

SYNC_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "sync_reviewed_fleet_additions.py"
)
sys.path.insert(0, str(SYNC_SCRIPT.parent))
SYNC_SPEC = importlib.util.spec_from_file_location(
    "sync_reviewed_fleet_additions", SYNC_SCRIPT
)
sync_reviewed_fleet_additions = importlib.util.module_from_spec(SYNC_SPEC)
assert SYNC_SPEC.loader
sys.modules["sync_reviewed_fleet_additions"] = sync_reviewed_fleet_additions
SYNC_SPEC.loader.exec_module(sync_reviewed_fleet_additions)


class SmartSolutionsFleetReleaseTests(unittest.TestCase):
    def adapter(self, count: int) -> dict:
        return {
            "source": {
                "kind": "canvas_snapshot",
                "path": str(ss_fleet_release.SNAPSHOT.resolve()),
            },
            "courses": [
                {"course_id": 100 + index, "label": f"Course {index}", "enabled": True}
                for index in range(count)
            ],
        }

    def test_requires_exactly_three_enabled_destinations(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "adapter.json"
            path.write_text(json.dumps(self.adapter(2)), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "exactly three"):
                ss_fleet_release.validate_three_course_adapter(path)
            path.write_text(json.dumps(self.adapter(3)), encoding="utf-8")
            loaded = ss_fleet_release.validate_three_course_adapter(path)
            self.assertEqual(len(ss_fleet_release.enabled_courses(loaded)), 3)

    def test_duplicate_destination_ids_fail_closed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "adapter.json"
            adapter = self.adapter(3)
            adapter["courses"][2]["course_id"] = adapter["courses"][1]["course_id"]
            path.write_text(json.dumps(adapter), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "duplicate course ID"):
                ss_fleet_release.validate_three_course_adapter(path)

    def test_source_approval_and_destination_apply_are_separate(self):
        args = ss_fleet_release.parser().parse_args(
            ["approve-source", "--approval-note", "Verizon source is good"]
        )
        self.assertEqual(args.func, ss_fleet_release.approve_source)
        self.assertNotIn("apply", ss_fleet_release.parser().format_help().lower())

    def test_approved_release_manifest_is_hash_sealed(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "release-approved.json"
            release = {
                "status": "source_approved_by_user",
                "snapshot": ss_fleet_release.snapshot_evidence(),
            }
            ss_fleet_release.write_private(path, release)
            ss_fleet_release.seal_private(path)
            self.assertEqual(
                ss_fleet_release.validate_release(path)["status"],
                "source_approved_by_user",
            )
            path.write_text("{}", encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "seal does not match"):
                ss_fleet_release.validate_release(path)

    def test_apply_guards_ignore_publication_state(self):
        item = {
            "id": 1,
            "type": "Page",
            "title": "Example",
            "position": 2,
            "content_id": None,
            "page_url": "example",
            "published": False,
        }
        published = {**item, "published": True}
        self.assertEqual(
            sync_reviewed_fleet_additions.module_item_guard(item),
            sync_reviewed_fleet_additions.module_item_guard(published),
        )
        page = {
            "page_id": 2,
            "url": "home",
            "title": "Home",
            "body": "Same",
            "front_page": True,
            "editing_roles": "teachers",
            "hide_from_students": False,
            "published": False,
        }
        self.assertEqual(
            sync_reviewed_fleet_additions.front_page_content_guard(page),
            sync_reviewed_fleet_additions.front_page_content_guard(
                {**page, "published": True}
            ),
        )


if __name__ == "__main__":
    unittest.main()
