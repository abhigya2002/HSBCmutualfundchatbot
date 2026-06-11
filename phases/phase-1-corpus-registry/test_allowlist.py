"""Unit tests for allowlist and registry (run from phase-1-corpus-registry directory)."""

import json
import unittest
from pathlib import Path

from allowlist import (
    AllowlistError,
    canonicalize_url,
    entry_by_scheme_slug,
    get_canonical_urls,
    is_allowlisted,
    load_registry,
    require_allowlisted,
    validate_registry_integrity,
)


class TestCanonicalize(unittest.TestCase):
    def test_strips_query_fragment(self):
        u = "https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth?utm=x#y"
        self.assertEqual(
            canonicalize_url(u),
            "https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth",
        )

    def test_http_to_https(self):
        u = "http://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth"
        self.assertEqual(
            canonicalize_url(u),
            "https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth",
        )

    def test_trailing_slash(self):
        u = "https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth/"
        self.assertEqual(
            canonicalize_url(u),
            "https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth",
        )

    def test_www_host(self):
        u = "https://www.groww.in/mutual-funds/hsbc-midcap-fund-direct-growth"
        self.assertEqual(
            canonicalize_url(u),
            "https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth",
        )

    def test_wrong_host(self):
        with self.assertRaises(AllowlistError):
            canonicalize_url("https://example.com/mutual-funds/hsbc-midcap-fund-direct-growth")

    def test_empty(self):
        with self.assertRaises(AllowlistError):
            canonicalize_url("  ")


class TestAllowlist(unittest.TestCase):
    def test_sixteen_urls(self):
        urls = get_canonical_urls()
        self.assertEqual(len(urls), 16)
        self.assertEqual(len(set(urls)), 16)

    def test_is_allowlisted(self):
        self.assertTrue(is_allowlisted(get_canonical_urls()[0]))
        self.assertFalse(is_allowlisted("https://groww.in/mutual-funds/other-fund"))
        self.assertFalse(is_allowlisted("https://google.com"))

    def test_require_allowlisted(self):
        u = get_canonical_urls()[3]
        self.assertEqual(require_allowlisted(u + "?a=1"), u)

    def test_require_allowlisted_bad(self):
        with self.assertRaises(AllowlistError):
            require_allowlisted("https://groww.in/mutual-funds/unknown")


class TestRegistryIntegrity(unittest.TestCase):
    def test_integrity_passes(self):
        validate_registry_integrity()

    def test_integrity_fails_on_extra_entry(self):
        data = load_registry()
        bad = json.loads(json.dumps(data))
        bad["entries"] = list(bad["entries"]) + [
            {
                "id": 99,
                "scheme": "fake",
                "scheme_display_name": "Fake",
                "url": "https://groww.in/mutual-funds/fake-fund",
                "source_type": "groww_scheme_page",
                "doc_version": "1.0.0",
                "published_date": None,
                "crawl_frequency": "weekly",
                "active": True,
            }
        ]
        with self.assertRaises(AllowlistError):
            validate_registry_integrity(bad)

    def test_entry_by_scheme_slug(self):
        e = entry_by_scheme_slug("hsbc-gilt-fund-direct-growth")
        self.assertIsNotNone(e)
        assert e is not None
        self.assertIn("gilt", e["scheme_display_name"].lower())


if __name__ == "__main__":
    unittest.main()
