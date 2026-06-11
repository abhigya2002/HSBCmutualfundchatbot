"""Tests for Phase 2.4 normalization (chrome strip, Markdown emit, corpus dedupe)."""

from __future__ import annotations

import unittest
from pathlib import Path

from phase_2_3.extract import extract_main_fragment
from phase_2_4.normalize import (
    NORMALIZER_VERSION,
    build_corpus_boilerplate_lines,
    normalize_extracted_html,
    strip_chrome,
)
from bs4 import BeautifulSoup


class TestNormalize(unittest.TestCase):
    def test_version(self):
        self.assertTrue(NORMALIZER_VERSION.startswith("2.4"))

    def test_fixture_pipeline_heading_and_rupee(self):
        raw_path = Path(__file__).resolve().parent / "fixtures" / "minimal_mf.html"
        raw = raw_path.read_bytes()
        ex = extract_main_fragment(raw)
        out = normalize_extracted_html(ex.main_html.encode("utf-8"))
        self.assertIn("# Test Fund", out.markdown)
        self.assertIn("₹", out.markdown)
        self.assertIn("%", out.markdown)

    def test_table_markdown(self):
        html = b"""<html><body><div id="root"><table><tr><th>A</th><th>B</th></tr>
        <tr><td>1</td><td>2%</td></tr></table></div></body></html>"""
        out = normalize_extracted_html(html)
        self.assertIn("| A | B |", out.markdown)
        self.assertIn("| 1 | 2% |", out.markdown)

    def test_chrome_class_stripped(self):
        html = b"""<html><body><div id="root">
        <div class="header2025_headerContainer__x"><span>Nav Junk</span></div>
        <h2>Real Title</h2><p>Real body with 12345678901234567890 digits skip dedupe.</p>
        </div></body></html>"""
        soup = BeautifulSoup(html, "html.parser")
        strip_chrome(soup)
        text = soup.get_text(" ", strip=True)
        self.assertNotIn("Nav Junk", text)
        self.assertIn("Real Title", text)

    def test_corpus_boilerplate_detection(self):
        shared = "Same Menu Line"
        long_a = "a" * 900
        long_b = "b" * 900
        html_a = f"<html><body><div id='root'><p>{shared}</p><p>{long_a}</p></div></body></html>".encode()
        html_b = f"<html><body><div id='root'><p>{shared}</p><p>{long_b}</p></div></body></html>".encode()
        ma = normalize_extracted_html(html_a).markdown
        mb = normalize_extracted_html(html_b).markdown
        bl = build_corpus_boilerplate_lines([ma, mb], min_doc_coverage=2)
        self.assertIn(shared, bl)
        out = normalize_extracted_html(html_a, corpus_line_blocklist=bl)
        self.assertNotIn(shared, out.markdown)


if __name__ == "__main__":
    unittest.main()
