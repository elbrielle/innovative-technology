import importlib.util
import json
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "plan_ss_legacy_rebootstrap.py"
)
sys.path.insert(0, str(SCRIPT.parent))
SPEC = importlib.util.spec_from_file_location("plan_ss_legacy_rebootstrap", SCRIPT)
planner = importlib.util.module_from_spec(SPEC)
assert SPEC.loader
sys.modules["plan_ss_legacy_rebootstrap"] = planner
SPEC.loader.exec_module(planner)

RECOVERY_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "plan_ss_partial_import_recovery.py"
)
RECOVERY_SPEC = importlib.util.spec_from_file_location(
    "plan_ss_partial_import_recovery", RECOVERY_SCRIPT
)
recovery = importlib.util.module_from_spec(RECOVERY_SPEC)
assert RECOVERY_SPEC.loader
sys.modules["plan_ss_partial_import_recovery"] = recovery
RECOVERY_SPEC.loader.exec_module(recovery)

APPLY_SCRIPT = (
    Path(__file__).resolve().parents[1]
    / "scripts"
    / "apply_ss_partial_import_recovery.py"
)
APPLY_SPEC = importlib.util.spec_from_file_location(
    "apply_ss_partial_import_recovery", APPLY_SCRIPT
)
recovery_apply = importlib.util.module_from_spec(APPLY_SPEC)
assert APPLY_SPEC.loader
sys.modules["apply_ss_partial_import_recovery"] = recovery_apply
APPLY_SPEC.loader.exec_module(recovery_apply)


class LegacyRebootstrapPlannerTests(unittest.TestCase):
    def test_keep_module_mapping_parser(self):
        self.assertEqual(planner.parse_keep_module("3=547875"), (3, 547875))

    def test_module_guard_ignores_publication(self):
        module = {
            "id": 10,
            "name": "Example",
            "position": 2,
            "published": False,
            "unlock_at": None,
            "require_sequential_progress": False,
            "prerequisite_module_ids": [],
        }
        item = {
            "id": 20,
            "position": 1,
            "type": "Page",
            "title": "Lesson",
            "page_url": "lesson",
            "content_id": None,
            "external_url": None,
            "indent": 0,
            "completion_requirement": None,
            "published": False,
        }
        self.assertEqual(
            planner.module_guard(module, [item]),
            planner.module_guard(
                {**module, "published": True}, [{**item, "published": True}]
            ),
        )

    def test_verify_seal_fails_after_tampering(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "plan.json"
            planner.write_sealed(path, {"status": "reviewed"})
            planner.verify_seal(path)
            path.write_text(json.dumps({"status": "changed"}), encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError, "seal does not match"):
                planner.verify_seal(path)

    def test_assignment_guard_ignores_publication_and_dynamic_counts(self):
        assignment = {
            "id": 1,
            "name": "Example",
            "description": "Body",
            "points_possible": 5.0,
            "grading_type": "points",
            "submission_types": ["online_upload"],
            "allowed_attempts": -1,
            "omit_from_final_grade": False,
            "peer_reviews": False,
            "anonymous_peer_reviews": False,
            "automatic_peer_reviews": False,
            "assignment_group_id": 2,
            "due_at": None,
            "unlock_at": None,
            "lock_at": None,
            "has_submitted_submissions": False,
            "external_tool_tag_attributes": None,
            "published": False,
            "needs_grading_count": 0,
        }
        changed = {
            **assignment,
            "published": True,
            "needs_grading_count": 99,
        }
        self.assertEqual(
            recovery_apply.assignment_guard(assignment),
            recovery_apply.assignment_guard(changed),
        )

    def test_rewrite_file_links_keeps_course_scoped_shape(self):
        body = (
            '<a href="https://verizoninnovativelearning.instructure.com/'
            'courses/23402/files/10/download?verifier=old" '
            'data-api-endpoint="https://verizoninnovativelearning.instructure.com/'
            'api/v1/courses/23402/files/10">Open</a>'
        )
        rewritten = recovery.rewrite_file_links(
            body,
            [10],
            {
                10: {
                    "id": 20,
                    "url": "https://learn.irvingisd.net/files/20/download?verifier=new",
                }
            },
            course_id=30,
        )
        self.assertIn("/courses/30/files/20/download?verifier=new", rewritten)
        self.assertIn("/api/v1/courses/30/files/20", rewritten)
        self.assertNotIn("courses/23402/files/10", rewritten)


if __name__ == "__main__":
    unittest.main()
