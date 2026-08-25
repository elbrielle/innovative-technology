import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import apply_xello_week1_parity as xello  # noqa: E402


class XelloWeek1ParityTests(unittest.TestCase):
    def test_student_route_is_bilingual_visual_and_privacy_safe(self):
        body = xello.student_body()
        self.assertIn(xello.STUDENT_MARKER, body)
        self.assertIn(xello.STUDENT_DECK_ID, body)
        self.assertIn("<strong>1–6</strong> for Matchmaker", body)
        self.assertIn("<strong>7–11</strong> for Personality Style", body)
        self.assertIn("<strong>12–15</strong> for Learning Style", body)
        self.assertNotIn("Teacher-only route cards", body)
        self.assertIn("Shift + Ctrl + Show windows", body)
        self.assertIn("Mayús + Ctrl + Mostrar ventanas", body)
        self.assertNotIn("<strong>Ctrl + Show windows</strong>", body)
        self.assertIn("Files → Downloads", body)
        self.assertIn("Archivos → Descargas", body)
        self.assertIn("esta ruta de texto contiene los mismos pasos", body)
        self.assertIn("You are done when", body)
        self.assertIn("Terminas cuando", body)
        self.assertIn("surprised me or confirmed what I already knew", body)
        self.assertIn("me sorprendió o confirmó lo que ya sabía", body)
        self.assertIn("How the 5 points work", body)
        self.assertIn("Cómo funcionan los 5 puntos", body)
        self.assertIn("first screenshot you are missing", body)
        self.assertIn("primera captura que te falte", body)
        self.assertIn('id="es-xello-w1" lang="es"', body)
        self.assertNotIn("§126.19", body)

    def test_teacher_guide_runs_end_to_end_without_false_teks_claim(self):
        body = xello.teacher_body()
        self.assertIn(xello.GUIDE_MARKER, body)
        self.assertIn(xello.DECK_ID, body)
        self.assertIn("One assessment per day", body)
        self.assertIn("Compressed 50–55 minute route", body)
        self.assertIn("Day 1 (35–45 min Xello)", body)
        self.assertIn("Activity: Ready, Set, Design", body)
        self.assertIn("Teach the route end to end", body)
        self.assertIn("Checks, expected responses, and misconceptions", body)
        self.assertIn("UDL, differentiation, and DOK scaffolds", body)
        self.assertIn("Troubleshooting and recovery", body)
        self.assertIn("Absence and independent route", body)
        self.assertIn("does not independently demonstrate a Grade 8 Technology Applications TEKS expectation", body)
        self.assertIn("DOK 1", body)
        self.assertIn("DOK 2", body)
        self.assertIn("confirmed prior self-knowledge", body)
        self.assertIn("Do not claim DOK 3", body)
        self.assertIn("available captions or a teacher summary", body)
        self.assertIn("private Canvas grading comment", body)
        self.assertIn("ClassLink or Xello will not open", body)
        self.assertIn("1 point:</strong> completed Matchmaker", body)

    def test_assignment_contract_fails_closed(self):
        valid = {"points_possible": 5.0, "grading_type": "points", "submission_types": ["online_upload"]}
        xello.validate_assignment_contract(valid)
        for invalid in (
            {**valid, "points_possible": 10.0},
            {**valid, "grading_type": "pass_fail"},
            {**valid, "submission_types": ["online_text_entry"]},
        ):
            with self.assertRaises(RuntimeError):
                xello.validate_assignment_contract(invalid)

    def test_existing_teacher_guide_cannot_remain_exposed(self):
        valid_page = {"published": False, "hide_from_students": True, "editing_roles": "teachers"}
        valid_item = {"published": False}
        xello.validate_guide_visibility(valid_page, valid_item)
        for page, item in (
            ({**valid_page, "published": True}, valid_item),
            ({**valid_page, "hide_from_students": False}, valid_item),
            ({**valid_page, "editing_roles": "teachers,students"}, valid_item),
            (valid_page, {"published": True}),
        ):
            with self.assertRaises(RuntimeError):
                xello.validate_guide_visibility(page, item)

    def test_stable_canvas_identities_are_bounded(self):
        self.assertEqual(xello.COURSE_ID, 23402)
        self.assertEqual(xello.MODULE_ID, 72564)
        self.assertEqual(xello.ASSIGNMENT_ID, 1183431)
        self.assertEqual(xello.ASSIGNMENT_ITEM_ID, 2633997)
        self.assertNotEqual(xello.DECK_ID, xello.STUDENT_DECK_ID)


if __name__ == "__main__":
    unittest.main()
