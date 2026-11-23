import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from export_canvas import referenced_file_ids


class FileReferenceTests(unittest.TestCase):
    def test_external_urls_are_not_canvas_files(self):
        self.assertEqual(referenced_file_ids('''
          <a href="https://kids.usmint.gov/system/files/2026-01/2026-Nickel.pdf">Coin</a>
          <a href="https://example.org/files/123/download">Other file</a>
          <p>Example path /files/456</p>'''), [])

    def test_canvas_routes_and_encoded_routes(self):
        self.assertEqual(referenced_file_ids('''
          <img src="/courses/23402/files/222/preview?verifier=x">
          <a href="https://verizoninnovativelearning.instructure.com/files/333/download">File</a>
          <span data-api-endpoint="/api/v1/courses/23402/files/222"></span>
          <iframe src="/media_attachments_iframe/444"></iframe>
          <a href="%2Fcourses%2F23402%2Ffiles%2F555%2Fdownload">Encoded</a>
          <a href="/files/2026-fake.pdf">Not a file route</a>'''), [222,333,444,555])


if __name__ == '__main__':
    unittest.main()
