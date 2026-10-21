"""
scoring/score.py  (v2 — three-basis model, October 2026)
=======================================================
Computes the Top 100 Pure-Play Digital AI Companies ranking.

THE PROBLEM
-----------
Valuation and ARR each span 5+ orders of magnitude ($10M - $100B ARR).
A direct linear sum would let one mega-company crush everything else.
So both axes are log-transformed and min-max rescaled.

THE BIG-TECH PROBLEM (and how we solve it)
-------------------------------------------
Alphabet, Meta, Microsoft, Amazon, Alibaba, Baidu and Tencent have real,
substantial, *disclosed* AI businesses - but they are not AI companies, and
their market caps are overwhelmingly priced on their non-AI businesses
(search, ads, e-commerce, gaming, Office). Dropping them would understate
the most important AI businesses on earth; using their full market caps
would let them dominate a ranking about AI on the strength of ad revenue.

We solve it with a THREE-BASIS model, applied consistently:

  1. pure_play  - the company IS an AI business. Its market/transaction
                  valuation is already an AI valuation. Used as-is.
                  These rows also form the PEER POOL for the multiple.

  2. derived    - the company is diversified but discloses AI-attributed
                  revenue. We value that revenue at the pure-play median
                  EV/Revenue multiple:

                      implied AI valuation = AI ARR x peer median multiple

                  This answers: "what would this AI business be worth if
                  it were a standalone AI company at peer multiples?"

  3. proxy      - no AI-revenue disclosure at all. No AI valuation can be
                  derived. Full market cap is used as a flagged proxy and
                  the ARR axis is scored at 0. Weakest evidence in the list.

The peer multiple is computed from the pure-play pool only (so the
imputation never feeds back into its own input), then applied once.

COMPOSITE
----------
    S = 100 * (0.5 * z_log(valuation) + 0.5 * z_log(ARR))

Output:
  - data/ranked.json, data/ranked.csv, site/ranked.json

Run:
  python scripts/score.py
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
OUT_PUBLIC_RANKED = ROOT / "ranked.json"

W_VAL = 0.5
W_ARR = 0.5


def is_skipped(company: dict) -> bool:
    """Skip placeholders, duplicates, entities rolled up into another row,
    and rows with no usable data at all."""
    cat = (company.get("category") or "").lower().strip()
    name = (company.get("name") or "").lower().strip()
    if cat in {"skip", "duplicate"}:
        return True
    if "duplicate" in cat or "duplicate" in name:
        return True
    if "now part of" in name or "rolls into" in name:
        return True
    if company.get("duplicate_in_ranking_with"):
        return True
    val = company.get("valuation_usd_b")
    arr = company.get("arr_usd_m")
    if val is None and arr is None:
        return True
    return False


def log_safe(x):
    return math.log10(x) if x and x > 0 else None


def ev_revenue(val_usd_b, arr_usd_m):
    """EV/Revenue multiple, both sides in the same unit."""
    if not val_usd_b or not arr_usd_m:
        return None
    return (val_usd_b * 1000.0) / arr_usd_m


def main() -> None:
    with DATA.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    companies = [c for c in raw["companies"] if not is_skipped(c)]

    # ------------------------------------------------------------------
    # PASS 1 - derive the peer EV/Revenue multiple from the pure-play pool
    # ------------------------------------------------------------------
    peer_pool = []
    for c in companies:
        if not c.get("is_pure_play_ai", True):
            continue
        if c.get("valuation_basis", "actual") != "actual":
            continue
        m = ev_revenue(c.get("valuation_usd_b"), c.get("arr_usd_m"))
        if m:
            peer_pool.append((c["name"], m))

    multiples = sorted(m for _, m in peer_pool)
    if not multiples:
        raise SystemExit("No pure-play peers with both valuation and ARR - "
                         "cannot derive the peer multiple.")

    peer_multiple = statistics.median(multiples)
    p25 = multiples[max(0, int(len(multiples) * 0.25) - 1)]
    p75 = multiples[min(len(multiples) - 1, int(len(multiples) * 0.75))]

    # ------------------------------------------------------------------
    # PASS 2 - resolve the valuation axis
    # ------------------------------------------------------------------
    resolved = []
    for c in companies:
        basis = c.get("valuation_basis", "actual")
        val_b = c.get("valuation_usd_b")
        arr_m = c.get("arr_usd_m")

        derived_val = None
        if basis == "derived":
            if arr_m:
                derived_val = round((arr_m * peer_multiple) / 1000.0, 2)
                val_b = derived_val
            else:
                # Nothing to derive from -> cannot score, treat as proxy.
                basis = "proxy"
        elif basis == "proxy":
            # Keep the market cap, but the ARR axis scores 0.
            pass

        resolved.append({
            "name": c["name"],
            "category": c.get("category"),
            "hq": c.get("hq"),
            "founded": c.get("founded"),
            "summary": c.get("summary"),
            "valuation_usd_b": val_b,
            "valuation_date": c.get("valuation_date"),
            "valuation_source": c.get("valuation_source"),
            "arr_usd_m": arr_m,
            "arr_date": c.get("arr_date"),
            "arr_source": c.get("arr_source"),
            "arr_total_usd_m": c.get("arr_total_usd_m"),
            "arr_attribution_note": c.get("arr_attribution_note"),
            "valuation_basis": basis,
            "is_pure_play_ai": c.get("is_pure_play_ai", True),
            "market_cap_usd_b": c.get("market_cap_usd_b"),
            "market_cap_date": c.get("market_cap_date"),
            "corporate_status": c.get("corporate_status"),
            "derived_valuation_usd_b": derived_val,
        })

    # ------------------------------------------------------------------
    # PASS 3 - normalise, score, rank
    # ------------------------------------------------------------------
    val_logs = [log_safe(r["valuation_usd_b"]) for r in resolved
                if r["valuation_usd_b"]]
    arr_logs = [log_safe(r["arr_usd_m"]) for r in resolved if r["arr_usd_m"]]
    val_logs = [v for v in val_logs if v is not None]
    arr_logs = [a for a in arr_logs if a is not None]

    val_min, val_max = min(val_logs), max(val_logs)
    arr_min, arr_max = min(arr_logs), max(arr_logs)
    val_span = (val_max - val_min) or 1
    arr_span = (arr_max - arr_min) or 1

    for r in resolved:
        z_v = z_a = None
        if r["valuation_usd_b"]:
            z_v = (math.log10(r["valuation_usd_b"]) - val_min) / val_span
        if r["arr_usd_m"]:
            z_a = (math.log10(r["arr_usd_m"]) - arr_min) / arr_span

        if z_v is None and z_a is None:
            score, missing = 0.0, "both"
        elif z_v is None:
            score, missing = 100.0 * (W_ARR * z_a), "valuation"
        elif z_a is None:
            score, missing = 100.0 * (W_VAL * z_v), "arr"
        else:
            score, missing = 100.0 * (W_VAL * z_v + W_ARR * z_a), ""

        r["z_val"] = round(z_v, 4) if z_v is not None else None
        r["z_arr"] = round(z_a, 4) if z_a is not None else None
        r["missing_axes"] = missing
        r["score"] = round(score, 2)

    resolved.sort(key=lambda r: r["score"], reverse=True)
    top = resolved[:100]
    for i, r in enumerate(top, start=1):
        r["rank"] = i

    payload = {
        "metadata": raw["metadata"],
        "counts": {
            "input": len(raw["companies"]),
            "after_filter": len(companies),
            "ranked": len(top),
            "pure_play": sum(1 for r in top if r["valuation_basis"] == "actual"),
            "derived": sum(1 for r in top if r["valuation_basis"] == "derived"),
            "proxy": sum(1 for r in top if r["valuation_basis"] == "proxy"),
        },
        "axes": {
            "valuation_usd_b": {"log_min": val_min, "log_max": val_max},
            "arr_usd_m": {"log_min": arr_min, "log_max": arr_max},
        },
        "weights": {"valuation": W_VAL, "arr": W_ARR},
        "peer_multiple": {
            "median_ev_revenue": round(peer_multiple, 2),
            "p25": round(p25, 2),
            "p75": round(p75, 2),
            "min": round(multiples[0], 2),
            "max": round(multiples[-1], 2),
            "pool_size": len(multiples),
            "pool": [{"name": n, "multiple": round(m, 2)} for n, m in peer_pool],
        },
        "exclusions": raw.get("exclusions", {}),
        "companies": top,
    }

    OUT_JSON.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    OUT_PUBLIC_RANKED.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    with OUT_CSV.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([
            "rank", "name", "category", "hq", "founded",
            "valuation_usd_b", "valuation_basis", "valuation_date",
            "arr_usd_m", "arr_date", "score", "z_val", "z_arr",
            "missing_axes", "summary",
        ])
        for r in top:
            w.writerow([
                r["rank"], r["name"], r["category"], r["hq"], r["founded"],
                "" if r["valuation_usd_b"] is None else r["valuation_usd_b"],
                r["valuation_basis"], r["valuation_date"] or "",
                "" if r["arr_usd_m"] is None else r["arr_usd_m"],
                r["arr_date"] or "",
                r["score"], r["z_val"], r["z_arr"],
                r["missing_axes"], r["summary"],
            ])

    # ------------------------------------------------------------------ console report
    print(f"Input companies : {len(raw['companies'])}")
    print(f"After filter    : {len(companies)}")
    print(f"Ranked (top 100): {len(top)}")
    print(f"  basis  actual  : {payload['counts']['pure_play']}")
    print(f"  basis  derived : {payload['counts']['derived']}")
    print(f"  basis  proxy   : {payload['counts']['proxy']}")
    print()
    print(f"Peer EV/Revenue multiple (pure-play pool, n={len(multiples)}):")
    print(f"  median={peer_multiple:.2f}x  p25={p25:.2f}x  p75={p75:.2f}x  "
          f"min={multiples[0]:.2f}x  max={multiples[-1]:.2f}x")
    print()
    print(f"Valuation axis log10: min={val_min:.2f}  max={val_max:.2f}")
    print(f"ARR       axis log10: min={arr_min:.2f}  max={arr_max:.2f}")
    print()
    print("Top 15:")
    for r in top[:15]:
        tag = {"actual": "P", "derived": "D", "proxy": "X"}[r["valuation_basis"]]
        print(f"  {r['rank']:>3}. [{tag}] {r['name'][:36]:<36} "
              f"val=${r['valuation_usd_b']}B  arr=${r['arr_usd_m']}M  score={r['score']}")
    print()
    print("Bottom 5:")
    for r in top[-5:]:
        tag = {"actual": "P", "derived": "D", "proxy": "X"}[r["valuation_basis"]]
        print(f"  {r['rank']:>3}. [{tag}] {r['name'][:36]:<36} "
              f"val=${r['valuation_usd_b']}B  arr=${r['arr_usd_m']}M  score={r['score']}")


if __name__ == "__main__":
    main()
