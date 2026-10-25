"""
Fails the CI run loudly when an "enhancement layer" silently produced nothing.

Every Claude stage and the newsdata.io fetch are continue-on-error and catch
their own exceptions, by design: one bad layer must never stop the brief from
publishing. The cost is that a dead layer looks identical to a healthy one --
a revoked or mis-pasted API key produced a green run (and a brief with no
BLUF, no relevance vetting) for weeks, and newsdata.io has never merged a
single article since it was added. This step runs after the build, before the
commit, and turns those silent failures into a red run (GitHub emails you).
The commit step has `if: always()`, so the page still publishes either way.

Checks, for today's data/<date>/ directory:
  1. synthesis.json has a BLUF            (synthesize.py / Anthropic key worked)
  2. redteam/_errors.json has no failures (redteam.py / Anthropic key worked)
  3. newsdata/ has raw payloads           (fetch_newsdata.py / NEWSDATA_KEY worked)

ANTHROPIC_KEY_SET / NEWSDATA_KEY_SET ("true"/"false") are passed in by the
workflow so the message can say whether the secret is empty or missing. They
carry only presence, never the key itself.
"""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load(path):
    try:
        with open(path) as f:
            return json.load(f)
    except (OSError, ValueError):
        return None


def main():
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    data_dir = ROOT / "data" / today
    anthropic_set = os.environ.get("ANTHROPIC_KEY_SET", "").lower()
    newsdata_set = os.environ.get("NEWSDATA_KEY_SET", "").lower()
    problems = []

    # --- Claude layers ---------------------------------------------------
    anthropic_hint = ""
    if anthropic_set == "false":
        anthropic_hint = " The ANTHROPIC_API_KEY secret is empty or not set."

    synthesis = _load(data_dir / "synthesis.json") or {}
    if not synthesis.get("bluf"):
        problems.append(("Synthesis produced no BLUF",
                         "data/%s/synthesis.json has no bluf, so the page shows headlines only.%s "
                         "Check the 'Generate BLUF' step log for 'Synthesis failed'." % (today, anthropic_hint)))

    errors = _load(data_dir / "redteam" / "_errors.json") or {}
    failures = errors.get("failures") or []
    if failures:
        first = ""
        for f in failures:
            for a in f.get("attempts") or []:
                if a.get("error"):
                    first = a["error"]
                    break
            if first:
                break
        extra = ""
        if "APIConnectionError" in first:
            extra = (" 'Connection error' with a key that is set usually means stray whitespace/quotes "
                     "in the secret: re-save ANTHROPIC_API_KEY with nothing but the key.")
        problems.append(("Red team failed",
                         "%d topic(s) fell back to unvetted articles. First error: %s.%s%s"
                         % (len(failures), (first or "unknown").rstrip("."), extra, anthropic_hint)))

    # --- newsdata.io -----------------------------------------------------
    raw_dir = data_dir / "newsdata"
    n_raw = len(list(raw_dir.glob("*.json"))) if raw_dir.exists() else 0
    if n_raw == 0:
        if newsdata_set == "false":
            why = "The NEWSDATA_KEY secret is empty or not set (or is named differently in repo settings)."
        else:
            why = ("No request succeeded. Check the 'Fetch newsdata.io' step log for "
                   "'NEWSDATA_KEY is not set', 'newsdata.io returned error', or 'ABORTING'.")
        problems.append(("newsdata.io returned nothing", why))

    if not problems:
        print("Pipeline check OK: BLUF present, red team clean, newsdata.io data present (%d topic files)." % n_raw)
        return 0

    for title, msg in problems:
        print("::error title=%s::%s" % (title, msg))
    print("\n%d pipeline problem(s). The brief was still built and will be published." % len(problems))
    return 1


if __name__ == "__main__":
    sys.exit(main())
