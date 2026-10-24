"""
patch_watchlist.py - add explicit 'match' fields to the coverage watchlist.

One-off helper used when the external list's name differs from the row name
in data/companies.json (e.g. "Zhipu AI" vs "Zhipu AI (Z.ai)"). Keeps the
coverage audit's matching explicit and auditable instead of relying on
fuzzy string matching.

Run:
    python scripts/patch_watchlist.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCH = ROOT / "data" / "coverage_watchlist.json"

MATCHES = {
    "SpaceX (xAI + Cursor)": "SpaceXAI (xAI + Cursor + X)",
    "Zhipu AI": "Zhipu AI (Z.ai)",
    "Safe Superintelligence": "Safe Superintelligence (SSI)",
    "Cognition AI": "Cognition (Devin)",
    "ServiceNow": "ServiceNow (Now Assist AI)",
    "Snowflake": "Snowflake (Cortex AI / Snowflake Intelligence)",
    "Prometheus": "Prometheus (prometheus.ai)",
    "Advanced Machine Intelligence (AMI)": "Advanced Machine Intelligence (AMI)",
    "Preferred Networks": "Preferred Networks (PFN)",
    "Microsoft Research Asia (MSRA)": "Microsoft Research Asia (MSRA)",
    "Google DeepMind": "Google DeepMind",
}


def main():
    data = json.loads(WATCH.read_text(encoding="utf-8"))
    n = 0
    for e in data["entries"]:
        m = MATCHES.get(e["name"])
        if m:
            e["match"] = m
            n += 1
    data["note"] = (
        data["note"]
        + " An entry may carry an explicit 'match' field naming the row in "
          "data/companies.json when the external list's name differs from ours."
    )
    WATCH.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                     encoding="utf-8")
    print(f"patched {n} entries in {WATCH.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
