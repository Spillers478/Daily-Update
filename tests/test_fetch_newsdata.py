"""
Regression tests for scripts/fetch_newsdata.py request building.

On 2026-10-25 every newsdata.io request failed and the second source had never
contributed an article, because the script sent two settings the API rejects:
  * excludedomain naming domains newsdata doesn't know (UnsupportedFilter --
    the WHOLE request is refused if any listed domain is unknown), and
  * timeframe on the free plan (AccessDenied).
These tests replay those rejections against a fake API, so they need no
network and no key:

    python -m unittest discover -s tests -v          # from the repo root
"""
import os
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

os.environ["NEWSDATA_KEY"] = "test-key"

import fetch_newsdata as N  # noqa: E402


class FakeResponse:
    status_code = 200

    def __init__(self, payload):
        self._payload = payload

    def json(self):
        return self._payload


def fake_api(url, params=None, timeout=None):
    """Mimics the two rejections seen in production, else succeeds."""
    bad = [d for d in (params.get("excludedomain") or "").split(",") if d in N.NEWSDATA_UNKNOWN_DOMAINS]
    if bad:
        return FakeResponse({"status": "error", "results": {
            "message": "excludedomain doesn't exist in our database", "code": "UnsupportedFilter"}})
    if "timeframe" in params:
        return FakeResponse({"status": "error", "results": {
            "message": "Access denied! To use the timeframe parameter, please upgrade your plan.",
            "code": "AccessDenied"}})
    return FakeResponse({"status": "success", "results": [{"title": "t", "link": "https://x.test/a"}]})


class RequestBuilding(unittest.TestCase):
    def setUp(self):
        N._request_count = 0

    def test_domains_newsdata_rejects_are_not_sent(self):
        sent = (N._EXCLUDE_DOMAINS or "").split(",")
        for d in N.NEWSDATA_UNKNOWN_DOMAINS:
            self.assertNotIn(d, sent)

    def test_plain_topic_succeeds_against_fake_api(self):
        with mock.patch.object(N.requests, "get", side_effect=fake_api):
            raw = N.fetch_latest("Iran AND Israel")
        self.assertEqual(raw["status"], "success")

    def test_timeframe_topic_does_not_trip_free_plan_rejection(self):
        with mock.patch.object(N.requests, "get", side_effect=fake_api) as get:
            raw = N.fetch_latest("earthquake", timeframe=24)
        self.assertEqual(raw["status"], "success")
        self.assertNotIn("timeframe", get.call_args.kwargs["params"])

    def test_timeframe_sent_only_when_explicitly_enabled(self):
        with mock.patch.object(N, "SEND_TIMEFRAME", True), \
                mock.patch.object(N.requests, "get", side_effect=fake_api) as get:
            N.fetch_latest("earthquake", timeframe=24)
        self.assertEqual(get.call_args.kwargs["params"]["timeframe"], 24)

    def test_empty_exclude_list_omits_the_param(self):
        with mock.patch.object(N, "_EXCLUDE_DOMAINS", ""), \
                mock.patch.object(N.requests, "get", side_effect=fake_api) as get:
            N.fetch_latest("x")
        self.assertNotIn("excludedomain", get.call_args.kwargs["params"])

    def test_key_whitespace_is_stripped(self):
        self.assertEqual(N.API_KEY, N.API_KEY.strip())


if __name__ == "__main__":
    unittest.main()
