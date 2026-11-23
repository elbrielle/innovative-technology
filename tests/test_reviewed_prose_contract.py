"""Prose-layout approval is exact text evidence, not a verification bypass."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from verify_site import plain_text, reviewed_prose_contract, sha256_text


class ReviewedProseContractTests(unittest.TestCase):
    def test_reviewed_text_is_required_and_drift_fails(self):
        body = '<h2>Learning goal</h2><p>Plan a coin.</p><p>Evidence: photo.</p>'
        record = {'contract_format': 'reviewed-prose',
                  'approved_text_sha256': sha256_text(plain_text(body))}
        self.assertTrue(reviewed_prose_contract(body, record))
        self.assertTrue(reviewed_prose_contract(body.replace('<p>', '<p class="new-layout">'), record))
        self.assertFalse(reviewed_prose_contract(body.replace('photo', 'STL'), record))
        self.assertFalse(reviewed_prose_contract(body, None))
        self.assertFalse(reviewed_prose_contract(body, {'contract_format': 'reviewed-prose'}))
        self.assertFalse(reviewed_prose_contract(body, {**record, 'contract_format': 'unreviewed'}))


if __name__ == '__main__':
    unittest.main()
