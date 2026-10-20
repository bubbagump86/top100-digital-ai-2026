"""
scoring/score.py
================
Computes the Top 100 Pure-Play Digital AI Companies ranking.

Methodology
-----------
We combine two signals:

  - Valuation (USD billions, most recent reported primary or tender round)
  - ARR      (USD millions, most recent disclosed annualised revenue /
              run-rate)

Both metrics span multiple orders of magnitude ($10M - $50B ARR).
A direct linear sum would let one mega-company (e.g. Salesforce
$280B mcap, $38B ARR) crush smaller frontier labs with no future ARR
visibility yet (SSI, Thinking Machines).  To keep the scale fair we:

  1. Log-transform both metrics: x_log = log10(x).
     - Companies with no disclosed value are dropped from that axis
       rather than coerced to 0.
  2. Min-max rescale each log-axis to [0, 1] across the surviving set.
  3. Composite the two normalised axes with equal weights:
        S = 100 * (0.5 * z_log(val) + 0.5 * z_log(arr))

Output:
  - ranked.json        -> ranked top 100 with metrics + scores
  - ranked.csv         -> flat CSV

Run:
  python scoring/score.py
"""

import csv
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "companies.json"
OUT_JSON = ROOT / "data" / "ranked.json"
OUT_CSV = ROOT / "data" / "ranked.csv"
OUT_PUBLIC_RANKED = ROOT / "site" / "ranked.json"


def is_skipped(company: dict) -> bool:
    """Skip rows that are placeholders / duplicates / missing fields."""
    cat = (company.get("category") or "").lower().strip()
    if cat in {"skip", "duplicate"}:
        return True
    if "duplicate" in cat:
        return True
    val = company.get("valuation_usd_b")
    arr = company.get("arr_usd_m")
    # To qualify for ranking, a company needs at least one disclosed value.
    # Companies with absolutely nothing disclosed (val AND arr both None)
    # are dropped.
    if val is None and arr is None:
        return True
    return False


def log_safe(x):
    return math.log10(x) if x and x > 0 else None


def main() -> None:
    with DATA.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    companies = [c for c in raw["companies"] if not is_skipped(c)]

    # Step 1: build log arrays
    val_logs = [log_safe(c["valuation_usd_b"]) for c in companies
                if c.get("valuation_usd_b") is not None]
    arr_logs = [log_safe(c["arr_usd_m"]) for c in companies
                if c.get("arr_usd_m") is not None]

    val_logs = [v for v in val_logs if v is not None]
    arr_logs = [a for a in arr_logs if a is not None]

    val_min, val_max = min(val_logs), max(val_logs)
    arr_min, arr_max = min(arr_logs), max(arr_logs)

    val_span = val_max - val_min if val_max != val_min else 1
    arr_span = arr_max - arr_min if arr_max != arr_min else 1

    # Step 2: score
    W_VAL = 0.5
    W_ARR = 0.5

    ranked = []
    for c in companies:
        val_b = c.get("valuation_usd_b")
        arr_m = c.get("arr_usd_m")

        z_v = None
        z_a = None

        if val_b is not None:
            v_log = math.log10(val_b)
            z_v = (v_log - val_min) / val_span  # in [0,1]

        if arr_m is not None:
            a_log = math.log10(arr_m)
            z_a = (a_log - arr_min) / arr_span  # in [0,1]

        # If both are missing we already dropped; but if exactly one is
        # missing, rescale the missing axis to 0 (worst observed signal).
        if z_v is None and z_a is None:
            score = 0.0
        elif z_v is None:
            score = 100.0 * (W_VAL * 0.0 + W_ARR * z_a)
            missing_axes = "valuation"
        elif z_a is None:
            score = 100.0 * (W_VAL * z_v + W_ARR * 0.0)
            missing_axes = "arr"
        else:
            score = 100.0 * (W_VAL * z_v + W_ARR * z_a)
            missing_axes = ""

        ranked.append({
            "name": c["name"],
            "category": c["category"],
            "hq": c["hq"],
            "founded": c["founded"],
            "valuation_usd_b": val_b,
            "valuation_date": c.get("valuation_date"),
            "valuation_source": c.get("valuation_source"),
            "arr_usd_m": arr_m,
            "arr_date": c.get("arr_date"),
            "arr_source": c.get("arr_source"),
            "summary": c["summary"],
            "z_val": round(z_v, 4) if z_v is not None else None,
            "z_arr": round(z_a, 4) if z_a is not None else None,
            "missing_axes": missing_axes,
            "score": round(score, 2),
        })

    # Sort descending by score.
    ranked.sort(key=lambda r: r["score"], reverse=True)

    # Slice to top 100 (we already filtered; should be <=100)
    top = ranked[:100]

    # Assign ranks.
    for i, r in enumerate(top, start=1):
        r["rank"] = i

    # Write JSON outputs.
    OUT_JSON.write_text(
        json.dumps({
            "metadata": raw["metadata"],
            "counts": {
                "input": len(raw["companies"]),
                "after_filter": len(companies),
                "ranked": len(top),
            },
            "axes": {
                "valuation_usd_b": {"log_min": val_min, "log_max": val_max},
                "arr_usd_m":        {"log_min": arr_min, "log_max": arr_max},
            },
            "weights": {"valuation": W_VAL, "arr": W_ARR},
            "exclusions": raw.get("exclusions", {}),
            "companies": top,
        }, indent=2),
        encoding="utf-8",
    )

    OUT_PUBLIC_RANKED.parent.mkdir(parents=True, exist_ok=True)
    OUT_PUBLIC_RANKED.write_text(
        json.dumps({
            "metadata": raw["metadata"],
            "counts": {
                "input": len(raw["companies"]),
                "after_filter": len(companies),
                "ranked": len(top),
            },
            "axes": {
                "valuation_usd_b": {"log_min": val_min, "log_max": val_max},
                "arr_usd_m":        {"log_min": arr_min, "log_max": arr_max},
            },
            "weights": {"valuation": W_VAL, "arr": W_ARR},
            "exclusions": raw.get("exclusions", {}),
            "companies": top,
        }, indent=2),
        encoding="utf-8",
    )

    # Write CSV.
    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([
            "rank", "name", "category", "hq", "founded",
            "valuation_usd_b", "valuation_date",
            "arr_usd_m", "arr_date", "score", "z_val", "z_arr",
            "missing_axes", "summary",
        ])
        for r in top:
            w.writerow([
                r["rank"], r["name"], r["category"], r["hq"], r["founded"],
                "" if r["valuation_usd_b"] is None else r["valuation_usd_b"],
                r["valuation_date"] or "",
                "" if r["arr_usd_m"] is None else r["arr_usd_m"],
                r["arr_date"] or "",
                r["score"], r["z_val"], r["z_arr"],
                r["missing_axes"], r["summary"],
            ])

    # Print summary.
    print(f"Input companies:     {len(raw['companies'])}")
    print(f"After filter:        {len(companies)}")
    print(f"Ranked (top 100):    {len(top)}")
    print()
    print(f"Valuation axis (log10): min={val_min:.2f}, max={val_max:.2f}")
    print(f"ARR       axis (log10): min={arr_min:.2f}, max={arr_max:.2f}")
    print()
    print("Top 10:")
    for r in top[:10]:
        v = r["valuation_usd_b"]
        a = r["arr_usd_m"]
        print(f"  #{r['rank']:>3}  {r['name']:<22}  val=${v}B  arr=${a}M  score={r['score']}")


if __name__ == "__main__":
    main()
