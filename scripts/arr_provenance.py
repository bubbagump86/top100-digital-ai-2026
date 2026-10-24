"""
arr_provenance.py - how much of the ARR axis is actually disclosed?

The argument for weighting revenue above valuation is usually "revenue is the
hard number; valuation is a negotiated round price". That argument only
holds if the ARR figures are better evidence than the valuations. This script
checks: of the rows in the list, how many have a company-disclosed
AI-attributed revenue figure, and how many rest on a third-party estimate,
an analyst note or a stale number?

It also reports the same for the valuation axis, so the two can be compared
honestly.

Run:
    python scripts/arr_provenance.py
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


PRESS_OUTLETS = ("reuters", "bloomberg", "forbes", "techcrunch", "cnbc",
                 "wsj", "wall street journal", "financial times", "ft ",
                 "the information", "the new york times", "nyt", "ycombinator",
                 "sacra", "latka", "crunchbase", "pitchbook", "caplight",
                 "cbinsights", "tracxn", "dealroom", "sifted", "technomion",
                 "the information")

COMPANY_DISCLOSURE = ("earnings", "filing", "sec ", "results", "disclosed",
                       "company-confirmed", "company confirmed", "company-stated",
                       "guidance", "investor", "annual report", "10-q", "10-k",
                       "press release", "announced", "press-reported",
                       "reported", "revenue run-rate", "run-rate", "revenue of",
                       "management", "conference call", "segment revenue",
                       "revenue was", "arr of")


def classify(text):
    """Bucket a source note into a provenance class.

    Order matters: an explicit estimate marker wins over anything else,
    because a figure can be reported by a company AND still be an estimate
    of a segment the company does not break out.
    """
    t = (text or "").lower()
    if not t:
        return "not disclosed"
    if "not disclosed" in t or "no ai revenue" in t or "pre-revenue" in t:
        return "not disclosed"
    if "est." in t or "estimate" in t or "sacra" in t or "latka" in t \
            or "third-party" in t or "third party" in t:
        return "third-party estimate"
    if any(k in t for k in COMPANY_DISCLOSURE):
        return "company-disclosed"
    if any(k in t for k in PRESS_OUTLETS):
        return "press-reported"
    return "other"


def main():
    ranked = json.loads((ROOT / "data" / "ranked.json").read_text(encoding="utf-8"))
    rows = ranked["companies"]

    arr = {}
    val = {}
    for c in rows:
        a = classify(c.get("arr_source"))
        v = classify(c.get("valuation_source"))
        arr[a] = arr.get(a, 0) + 1
        val[v] = val.get(v, 0) + 1

    L = []
    L.append("=" * 74)
    L.append("PROVENANCE OF THE TWO AXES (100 ranked rows)")
    L.append("=" * 74)
    L.append("")
    L.append("AI-ARR axis:")
    for k in sorted(arr, key=lambda x: -arr[x]):
        L.append(f"    {arr[k]:>4}  {k}")
    L.append("")
    L.append("Valuation axis:")
    for k in sorted(val, key=lambda x: -val[x]):
        L.append(f"    {val[k]:>4}  {k}")

    # How many rows have an ARR figure that is not company-disclosed?
    non_disc = [c["name"] for c in rows
                if c.get("arr_usd_m") is not None
                and classify(c.get("arr_source")) != "company-disclosed"]
    stale = [c["name"] for c in rows
             if c.get("arr_usd_m") is not None
             and ("stale" in (c.get("arr_source") or "").lower()
                  or "not updated" in (c.get("arr_source") or "").lower())]
    L.append("")
    L.append("=" * 74)
    L.append("THE ARR AXIS, row by row")
    L.append("=" * 74)
    L.append(f"{'company':<44}{'ARR $M':>9}  {'provenance':<22}source note")
    L.append("-" * 110)
    for c in sorted(rows, key=lambda x: -(x.get("arr_usd_m") or 0)):
        if c.get("arr_usd_m") is None:
            continue
        L.append(f"{c['name'][:43]:<44}{c['arr_usd_m']:>9}  "
                 f"{classify(c.get('arr_source')):<22}"
                 f"{(c.get('arr_source') or '')[:48]}")
    L.append("")
    L.append(f"Rows with an ARR figure that is NOT company-disclosed: {len(non_disc)}")
    for n in non_disc:
        L.append(f"    - {n}")
    L.append("")
    L.append(f"Rows whose ARR figure is company-disclosed but STALE: {len(stale)}")
    for n in stale:
        L.append(f"    - {n}")

    (ROOT / ".tmp_provenance.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
