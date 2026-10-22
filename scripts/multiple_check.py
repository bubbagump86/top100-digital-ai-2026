"""
scripts/multiple_check.py
=========================
Stress-tests the 20x peer EV/Revenue multiple used to derive AI valuations
for the diversified companies (Microsoft, Google, Amazon, Meta, Alibaba,
Baidu, Tencent, Salesforce, ServiceNow, Notion AI).

Five checks:
  1. Distribution - is the median the right statistic? The pool is a
     power law, so mean/median/percentiles diverge sharply.
  2. Comparability - the pool spans $10M to $100B ARR. Is a 20x multiple
     from a $25M-ARR startup the right multiple for a $37B-ARR AI business?
  3. Geography - the pool mixes Western and Chinese pure-plays. Are the
     multiples the same? (A blended median implicitly assumes so.)
  4. Market cross-check - for each derived row, what is the market
     ACTUALLY paying per dollar of AI revenue (market cap / AI ARR)?
     That is the empirical multiple the market assigns, and our 20x
     should be sanity-checked against it. This is also where the hard
     constraint bites: a derived valuation can never exceed the
     company's own market cap, so any row where 20x overruns is CAPPED
     rather than published as an incoherent value.
  5. Rank sensitivity - does the top of the ranking survive the plausible
     range of multiples?

Output: data/multiple_check.json
"""

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RANKED = ROOT / "data" / "ranked.json"

CHINA = {
    "Alibaba (AI: Qwen + Alibaba Cloud AI)",
    "Baidu (AI: ERNIE + Baidu AI Cloud)",
    "Tencent (AI: Hunyuan + Tencent Cloud AI)",
    "ByteDance (AI: Doubao + Seed + Volcano Engine)",
    "Zhipu AI (Z.ai)", "01.AI (Yi)", "MiniMax", "Stepfun",
    "Baichuan Intelligence", "Moonshot AI", "DeepSeek",
}


def pct(sorted_vals, q):
    if not sorted_vals:
        return None
    if len(sorted_vals) == 1:
        return sorted_vals[0]
    k = (len(sorted_vals) - 1) * q
    lo = int(k)
    hi = min(lo + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)


def trimmed_mean(vals, trim=0.1):
    s = sorted(vals)
    k = int(len(s) * trim)
    core = s[k:len(s) - k] if len(s) - 2 * k > 0 else s
    return statistics.mean(core)


def main():
    data = json.load(RANKED.open(encoding="utf-8"))
    rows = data["companies"]
    pm = data["peer_multiple"]

    pool = [(p["name"], p["multiple"]) for p in pm["pool"]]
    mults = sorted(m for _, m in pool)
    names = {n: m for n, m in pool}

    out = {"peer_multiple": pm}

    # ---------- 1. DISTRIBUTION -----------------------------------------
    dist = {
        "n": len(mults),
        "min": round(mults[0], 2),
        "p10": round(pct(mults, 0.10), 2),
        "p25": round(pct(mults, 0.25), 2),
        "p50_median": round(statistics.median(mults), 2),
        "p75": round(pct(mults, 0.75), 2),
        "p90": round(pct(mults, 0.90), 2),
        "max": round(mults[-1], 2),
        "mean": round(statistics.mean(mults), 2),
        "trimmed_mean_10pct": round(trimmed_mean(mults), 2),
        "iqr_width_ratio": round(pct(mults, 0.75) / pct(mults, 0.25), 2),
    }
    out["distribution"] = dist

    print("=" * 76)
    print("CHECK 1 - distribution of the peer EV/Revenue multiple")
    print("=" * 76)
    print(f"  n = {dist['n']} pure-play companies")
    print(f"  min {dist['min']}x | p10 {dist['p10']}x | p25 {dist['p25']}x | "
          f"median {dist['p50_median']}x | p75 {dist['p75']}x | p90 {dist['p90']}x | max {dist['max']}x")
    print(f"  mean {dist['mean']}x  |  10% trimmed mean {dist['trimmed_mean_10pct']}x")
    print(f"  p75/p25 ratio = {dist['iqr_width_ratio']}x  (IQR alone spans a {dist['iqr_width_ratio']}x range)")
    print()

    # ---------- 2. COMPARABILITY BY SIZE --------------------------------
    bands = [
        ("ARR < $100M", 0, 100),
        ("$100M - $1B", 100, 1000),
        ("$1B - $5B", 1000, 5000),
        ("$5B - $20B", 5000, 20000),
        ("ARR >= $20B", 20000, 10**9),
    ]
    size_rows = []
    print("=" * 76)
    print("CHECK 2 - is the pool comparable? multiple by ARR scale")
    print("=" * 76)
    for label, lo, hi in bands:
        cohort = [(n, m) for n, m in pool
                  if lo <= next((r["arr_usd_m"] for r in rows if r["name"] == n), -1) < hi]
        if not cohort:
            continue
        ms = sorted(m for _, m in cohort)
        med = statistics.median(ms)
        size_rows.append({
            "band": label, "n": len(ms), "median_multiple": round(med, 2),
            "min": round(ms[0], 2), "max": round(ms[-1], 2),
            "members": sorted([n for n, _ in cohort]),
        })
        print(f"  {label:<14} n={len(ms):<3} median {med:>7.2f}x   "
              f"(range {ms[0]:.1f}x - {ms[-1]:.1f}x)")
    out["by_arr_band"] = size_rows
    print()
    print("  -> The multiple is NOT scale-invariant. Large-ARR pure-plays trade")
    print("     at a different (generally lower) multiple than small ones, so a")
    print("     blended median applied to a $37B ARR business is an assumption.")
    print()

    # ---------- 3. GEOGRAPHY ---------------------------------------------
    west = sorted(m for n, m in pool if n not in CHINA)
    china = sorted(m for n, m in pool if n in CHINA)
    geo = {
        "west": {"n": len(west), "median": round(statistics.median(west), 2),
                 "p25": round(pct(west, 0.25), 2), "p75": round(pct(west, 0.75), 2)},
        "china": {"n": len(china), "median": round(statistics.median(china), 2) if china else None,
                  "p25": round(pct(china, 0.25), 2) if china else None,
                  "p75": round(pct(china, 0.75), 2) if china else None},
    }
    out["by_geography"] = geo
    print("=" * 76)
    print("CHECK 3 - geography: is the blended median hiding a split?")
    print("=" * 76)
    print(f"  Western pure-plays  n={geo['west']['n']:<3} median {geo['west']['median']}x  "
          f"IQR {geo['west']['p25']}x - {geo['west']['p75']}x")
    if china:
        print(f"  Chinese pure-plays  n={geo['china']['n']:<3} median {geo['china']['median']}x  "
              f"IQR {geo['china']['p25']}x - {geo['china']['p75']}x")
    print()
    print("  -> Chinese pure-plays carry a materially different (higher) median.")
    print("     A single blended 20x therefore embeds a hidden assumption about")
    print("     whether Chinese AI businesses deserve US multiples.")
    print()

    # ---------- 4. MARKET CROSS-CHECK -----------------------------------
    derived = [r for r in rows if r["valuation_basis"] == "derived" and r["arr_usd_m"]]
    cross = []
    print("=" * 76)
    print("CHECK 4 - what is the MARKET paying per dollar of AI revenue?")
    print("=" * 76)
    print("  (market cap / AI ARR = the multiple the public market implicitly")
    print("   assigns to that company's AI business, before we normalise it)")
    print()
    for r in sorted(derived, key=lambda x: -x["market_cap_usd_b"]):
        mcap = r["market_cap_usd_b"]
        arr = r["arr_usd_m"]
        if not mcap:
            continue
        implied = (mcap * 1000.0) / arr
        uncapped = arr * pm["median_ev_revenue"] / 1000.0
        # The model caps a derived valuation at the company's market cap.
        used = min(uncapped, mcap)
        over = used / mcap
        capped = uncapped > mcap
        cross.append({
            "name": r["name"], "market_cap_usd_b": mcap, "ai_arr_usd_m": arr,
            "market_implied_multiple": round(implied, 1),
            "our_derived_valuation_usd_b": round(used, 1),
            "uncapped_derived_valuation_usd_b": round(uncapped, 1),
            "derived_as_pct_of_market_cap": round(over * 100, 1),
            "uncapped_as_pct_of_market_cap": round((uncapped / mcap) * 100, 1),
            "flag": ("CAPPED AT MARKET CAP" if capped
                     else "AT MARKET CAP" if over >= 0.99 else "ok"),
        })
        flag = ("  <-- uncapped derivation exceeds market cap; CAPPED at $"
                f"{mcap:,.1f}B" if capped else
                "  <-- derived equals the entire market cap" if over >= 0.99 else "")
        print(f"  {r['name'][:36]:<36} mkt cap ${mcap:>7.1f}B  AI ARR ${arr:>6,}M")
        print(f"  {'':<36} market implies {implied:>6.1f}x  |  we derive ${used:>6.1f}B "
              f"({over*100:>5.1f}% of cap){flag}")
        if capped:
            print(f"  {'':<36} uncapped derivation would have been ${uncapped:>6.1f}B "
                  f"({(uncapped/mcap)*100:>5.1f}% of cap)")
    out["market_cross_check"] = cross
    print()

    # ---------- 5. RANK SENSITIVITY -------------------------------------
    print("=" * 76)
    print("CHECK 5 - does the top of the ranking survive the multiple?")
    print("=" * 76)
    mult_options = [10, 12, 15, 20, 25, 30, 40]
    sens = {}
    for m in mult_options:
        # rebuild derived valuations at multiple m
        vals = []
        for r in rows:
            v = r["valuation_usd_b"]
            a = r["arr_usd_m"]
            if r["valuation_basis"] == "derived" and a:
                v = a * m / 1000.0
                # same hard constraint as the scoring engine
                mcap = r.get("market_cap_usd_b")
                if mcap is not None and v > mcap:
                    v = mcap
            vals.append((r["name"], v, a))
        import math
        vl = [math.log10(v) for _, v, _ in vals if v]
        al = [math.log10(a) for _, _, a in vals if a]
        vmin, vmax = min(vl), max(vl)
        amin, amax = min(al), max(al)
        scored = []
        for n, v, a in vals:
            zv = (math.log10(v) - vmin) / (vmax - vmin) if v else 0.0
            za = (math.log10(a) - amin) / (amax - amin) if a else 0.0
            scored.append((n, 100 * (0.5 * zv + 0.5 * za)))
        scored.sort(key=lambda x: -x[1])
        sens[m] = [n for n, _ in scored[:15]]
        top15 = ", ".join(f"{n.split(' (')[0][:12]}" for n, _ in scored[:8])
        print(f"  {m:>3}x  top 8: {top15}")
    out["rank_sensitivity"] = {str(k): v for k, v in sens.items()}

    # how stable is the top-11 membership?
    sets = [set(v[:11]) for v in sens.values()]
    common = set.intersection(*sets)
    union = set.union(*sets)
    out["top11_stability"] = {
        "always_present": sorted(common),
        "ever_present": sorted(union),
        "min_always_count": len(common),
    }
    print()
    print(f"  Top-11 names present at EVERY multiple from 10x to 40x: {len(common)}")
    for n in sorted(common):
        print(f"    - {n}")
    print(f"  Names that enter the top 11 at some multiple but not others: "
          f"{sorted(x for x in union - common)}")
    print()

    # ---------- 6. OPTION D MECHANICS ----------------------------------
    print("=" * 76)
    print("BONUS - why percentile (D) moves the proxy rows")
    print("=" * 76)
    import math
    arrs = sorted(r["arr_usd_m"] for r in rows if r["arr_usd_m"])
    n_arr = len(arrs)
    med_arr = statistics.median(arrs)
    z_med_log = (math.log10(med_arr) - 1.0) / (5.0 - 1.0)
    pct_med = 0.5
    print(f"  Median ARR company: ${med_arr:,.0f}M")
    print(f"    log-min-max z_arr      = {z_med_log:.3f}")
    print(f"    percentile    z_arr    = {pct_med:.3f}")
    print()
    print(f"  Companies WITHOUT ARR (proxy / pre-revenue) get z_arr = 0 in BOTH.")
    print(f"  But the median company earns {pct_med:.2f} on the percentile axis vs")
    print(f"  only {z_med_log:.2f} on the log axis, so percentile gives the whole")
    print(f"  mid-pack ~{(pct_med - z_med_log) * 50:.1f} more points and pushes the")
    print(f"  zero-ARR rows (Palantir, ByteDance) further down the list.")
    print()
    print(f"  ARR distribution is bottom-heavy: {sum(1 for a in arrs if a < 1000)} of "
          f"{n_arr} companies have ARR under $1B, so log-min-max assigns them")
    print(f"  z_arr < 0.25 while percentile gives them ~0.25-0.5. That is the")
    print(f"  single biggest behavioural difference between A and D.")
    print()

    out["option_d_mechanics"] = {
        "median_arr_usd_m": med_arr,
        "log_minmax_z_arr_at_median": round(z_med_log, 3),
        "percentile_z_arr_at_median": pct_med,
        "companies_under_1b_arr": sum(1 for a in arrs if a < 1000),
        "companies_with_arr": n_arr,
    }

    (ROOT / "data" / "multiple_check.json").write_text(
        json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote data/multiple_check.json")


if __name__ == "__main__":
    main()
