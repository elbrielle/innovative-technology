"""Snapshot metadata must retain the settings consumed by fleet comparison."""
import sys
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from export_canvas import discussion_projection, quiz_projection

class ParityMetadataProjection(unittest.TestCase):
    def test_discussion_rating_choices_survive_export(self):
        settings = {'allow_rating': True, 'only_graders_can_rate': False, 'sort_by_rating': False}
        result = discussion_projection(settings)
        self.assertEqual({key: result[key] for key in settings}, settings)

    def test_quiz_scoring_policy_survives_export(self):
        self.assertEqual(quiz_projection({'scoring_policy': 'keep_highest'})['scoring_policy'], 'keep_highest')
        self.assertEqual(quiz_projection({'scoring_policy': 'keep_latest'})['scoring_policy'], 'keep_latest')
