import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
import verify_curriculum_review_gate as gate


class CurriculumReviewGateTests(unittest.TestCase):
    def test_staged_instruction_and_review_are_both_in_changed_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            def git(*args):
                subprocess.run(['git', *args], cwd=root, check=True, capture_output=True)
            git('init', '-q')
            git('-c', 'user.name=Test', '-c', 'user.email=test@example.invalid',
                'commit', '--allow-empty', '-qm', 'Initial')
            for name in ['lessons/123.html', 'docs/reviews/staged-review.md']:
                file = root / name
                file.parent.mkdir(parents=True, exist_ok=True)
                file.write_text('staged content')
            git('add', '.')
            with patch.object(gate, 'ROOT', root):
                self.assertEqual(gate.changed_paths('HEAD'),
                                 ['docs/reviews/staged-review.md', 'lessons/123.html'])
            self.assertTrue(gate.instructional('pages/123.html'))


if __name__ == '__main__':
    unittest.main()
