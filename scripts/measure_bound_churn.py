"""
measure_bound_churn.py - reproduce the "why the bounds are fixed" measurement.

The methodology page argues for FIXED axis bounds with a measured claim:
"a company joining with $5M of ARR shifts the median score by 2.53 points,
and still reorders 13 companies by three or more places. A $1M entrant
reorders 39."

A measured claim that cannot be re-run is just a number someone typed once.
This script re-derives it with the real scoring engine, so the published
figure can never drift from the data.

Method:
  * run scripts/score.py twice on the SAME data, once with
    --axis sample (bounds taken from the sample's own extremes) and once
    with --axis anchored (the shipped policy), each with and without a
    hypothetical entrant
  * the entrant is stated explicitly: $1.0B valuation, and either $5M or
    $1M of ARR
  * report: median-score shift, rows whose score moves by more than
    0.5 points, and rows moving 3+ rank places

The contrast IS the argument: sample bounds re-base the whole list on every
data update; anchored bounds move nothing.

Run:
    python scripts/measure_bound_churn.py
"""

import json
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "scripts" / "score.py"
DATA = ROOT / "data" / "companies.json"

ENTRANT_VAL_B = 1.0    # $1.0B valuation
ENTRANT_ARR_M = 5.0    # $5M ARR (first scenario)
ENTRANT_ARR_LOW = 1.0  # $1M ARR (second scenario)

VARIANTS = ROOT / "data" / "variants"


def run_variant(name, companies_path, axis):
    cmd = [sys.executable, str(SCORE), "--axis", axis,
           "--variant", name, "--companies", str(companies_path)]
    subprocess.run(cmd, check=True, capture_output=True, cwd=str(ROOT))
    return json.loads((VARIANTS / name / "ranked.json").read_text(encoding="utf-8"))


def compare(a, b):
    ra = {c["name"]: c for c in a["companies"]}
    rb = {c["name"]: c for c in b["companies"]}
    common = set(ra) & set(rb)

    med_a = statistics.median([ra[n]["score"] for n in common])
    med_b = statistics.median([rb[n]["score"] for n in common])

    score_moved = sum(1 for n in common
                       if abs(ra[n]["score"] - rb[n]["score"]) > 0.5)
    max_shift = max((abs(ra[n]["score"] - rb[n]["score"]) for n in common),
                     default=0.0)
    rank_moved = sum(1 for n in common
                     if abs(ra[n]["rank"] - rb[n]["rank"]) >= 3)
    return {
        "median_score_before": round(med_a, 2),
        "median_score_after": round(med_b, 2),
        "median_shift": round(med_b - med_a, 2),
        "rows_score_moved_over_0_5": score_moved,
        "max_score_change": round(max_shift, 2),
        "rows_moved_3plus_places": rank_moved,
        "n_compared": len(common),
    }


def with_entrant(arr_m):
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    raw["companies"].append({
        "rank_seed": 999,
        "name": "__hypothetical_entrant__",
        "category": "Hypothetical",
        "hq": "n/a",
        "founded": 2026,
        "valuation_usd_b": ENTRANT_VAL_B,
        "valuation_date": "hypothetical",
        "valuation_source": "hypothetical entrant",
        "arr_usd_m": arr_m,
        "arr_date": "hypothetical",
        "arr_source": "hypothetical entrant",
        "summary": "Hypothetical entrant used to measure bound churn.",
        "is_digital_only": True,
        "is_pure_play_ai": True,
        "valuation_basis": "actual",
    })
    p = ROOT / "data" / ".churn_entrant.json"
    p.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
    return p


def main():
    VARIANTS.mkdir(parents=True, exist_ok=True)
    results = []

    for arr_m, label in ((ENTRANT_ARR_M, "$5M ARR entrant"),
                         (ENTRANT_ARR_LOW, "$1M ARR entrant")):
        temp = with_entrant(arr_m)
        sample_base = run_variant("churn_sample_base", DATA, "sample")
        sample_new = run_variant("churn_sample_new", temp, "sample")
        anchored_base = run_variant("churn_anchored_base", DATA, "anchored")
        anchored_new = run_variant("churn_anchored_new", temp, "anchored")

        results.append({
            "label": label,
            "entrant_valuation_usd_b": ENTRANT_VAL_B,
            "entrant_arr_usd_m": arr_m,
            "sample_derived_bounds": compare(sample_base, sample_new),
            "anchored_bounds_shipped": compare(anchored_base, anchored_new),
        })
        temp.unlink()

    print("=" * 74)
    print("BOUND CHURN - what happens when one company joins the list")
    print("=" * 74)
    for r in results:
        print(f"\n{r['label']}  (${r['entrant_valuation_usd_b']}B valuation)")
        for key, title in (("sample_derived_bounds", "sample-derived bounds (rejected)"),
                           ("anchored_bounds_shipped", "anchored bounds (shipped)")):
            c = r[key]
            print(f"  {title}")
            print(f"    median score       : {c['median_score_before']} -> "
                  f"{c['median_score_after']}  ({c['median_shift']:+})")
            print(f"    rows score moved   : {c['rows_score_moved_over_0_5']} "
                  f"(by >0.5 pts)")
            print(f"    largest score move : {c['max_score_change']} pts")
            print(f"    rows moving 3+     : {c['rows_moved_3plus_places']}")
    print("\n" + "=" * 74)

    out = ROOT / "data" / "bound_churn.json"
    out.write_text(json.dumps({
        "method": "scripts/score.py --axis sample vs --axis anchored",
        "entrants": results,
    }, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
