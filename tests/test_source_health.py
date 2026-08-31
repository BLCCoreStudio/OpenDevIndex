from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from check_source_health import classify_http_code, static_public_https_url  # noqa: E402
from url_safety import is_safe_https_url  # noqa: E402


class SourceHealthTests(unittest.TestCase):
    def test_static_url_safety(self) -> None:
        self.assertTrue(is_safe_https_url("https://example.com/docs"))
        self.assertTrue(static_public_https_url("https://example.com/docs")[0])

        unsafe = (
            "http://example.com/",
            "https://localhost/",
            "https://127.0.0.1/",
            "https://10.0.0.1/",
            "https://169.254.169.254/",
            "https://[::1]/",
            "https://user:pass@example.com/",
            "https://example.com:8443/",
        )
        for value in unsafe:
            with self.subTest(value=value):
                self.assertFalse(is_safe_https_url(value))
                self.assertFalse(static_public_https_url(value)[0])

    def test_http_classification(self) -> None:
        self.assertEqual(classify_http_code(200), "healthy")
        self.assertEqual(classify_http_code(301), "healthy")
        self.assertEqual(classify_http_code(403), "restricted")
        self.assertEqual(classify_http_code(429), "restricted")
        self.assertEqual(classify_http_code(404), "broken")
        self.assertEqual(classify_http_code(410), "broken")
        self.assertEqual(classify_http_code(503), "transient")


if __name__ == "__main__":
    unittest.main()
