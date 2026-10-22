"""
scripts/sensitivity.py
======================
Sensitivity analysis: what happens to the ranking if we DON'T log-transform?

Variants tested
---------------
  A  log + min-max        (the shipped model)
  B  raw + min-max        (the naive alternative the question asks about)
  C  raw + z-score        (raw, standardised)
  D  raw + percentile     (rank-based; robust to any monotone transform)

Outputs: rank correlation vs A, biggest movers, and the tie/cluster
diagnostic that explains WHY the naive variant fails.
"""

import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "companies.json"
RANKED = ROOT / "data" / "ranked.json"


def minmax(vals):
    lo, hi = min(vals), max(vals)
    span = (hi - lo) or 1
    return {v: (v - lo) / span for v in set(vals)}


def zscore(vals):
    mu = statistics.mean(vals)
    sd = statistics.pstdev(vals) or 1
    return {v: (v - mu) / sd for v in set(vals)}


def pctrank(vals):
    s = sorted(vals)
    n = len(s)
    out = {}
    for v in set(vals):
        below = sum(1 for x in s if x < v)
        equal = sum(1 for x in s if x == v)
        out[v] = (below + (equal - 1) / 2) / (n - 1) if n > 1 else 0
    return out


def score(rows, val_fn, arr_fn):
    """val_fn / arr_fn map a row -> the transformed axis value (or None)."""
    vvals = [val_fn(r) for r in rows if val_fn(r) is not None]
    avals = [arr_fn(r) for r in rows if arr_fn(r) is not None]

    vscale = minmax(vvals) if vvals else {}
    ascale = minmax(avals) if avals else {}

    out = []
    for r in rows:
        v, a = val_fn(r), arr_fn(r)
        zv = vscale.get(v, 0.0) if v is not None else 0.0
        za = ascale.get(a, 0.0) if a is not None else 0.0
        out.append((r["name"], 100 * (0.5 * zv + 0.5 * za)))
    out.sort(key=lambda x: -x[1])
    return out


def main():
    ranked = json.load(RANKED.open(encoding="utf-8"))
    rows = ranked["companies"]

    # --- variant A: the shipped model (log + min-max) -------------------
    def A_val(r):
        return math.log10(r["valuation_usd_b"]) if r["valuation_usd_b"] else None

    def A_arr(r):
        return math.log10(r["arr_usd_m"]) if r["arr_usd_m"] else None

    A = score(rows, A_val, A_arr)

    # --- variant B: raw + min-max ---------------------------------------
    B = score(rows, lambda r: r["valuation_usd_b"], lambda r: r["arr_usd_m"])

    # --- variant C: raw + z-score ---------------------------------------
    def C_score():
        vvals = [r["valuation_usd_b"] for r in rows if r["valuation_usd_b"]]
        avals = [r["arr_usd_m"] for r in rows if r["arr_usd_m"]]
        vs, as_ = zscore(vvals), zscore(avals)
        out = []
        for r in rows:
            v = r["valuation_usd_b"]
            a = r["arr_usd_m"]
            zv = vs.get(v, -3.0) if v is not None else -3.0
            za = as_.get(a, -3.0) if a is not None else -3.0
            out.append((r["name"], 100 * (0.5 * zv + 0.5 * za)))
        out.sort(key=lambda x: -x[1])
        return out

    C = C_score()

    # --- variant D: raw + percentile rank -------------------------------
    def D_score():
        vvals = [r["valuation_usd_b"] for r in rows if r["valuation_usd_b"]]
        avals = [r["arr_usd_m"] for r in rows if r["arr_usd_m"]]
        vs, as_ = pctrank(vvals), pctrank(avals)
        out = []
        for r in rows:
            v = r["valuation_usd_b"]
            a = r["arr_usd_m"]
            zv = vs.get(v, 0.0) if v is not None else 0.0
            za = as_.get(a, 0.0) if a is not None else 0.0
            out.append((r["name"], 100 * (0.5 * zv + 0.5 * za)))
        out.sort(key=lambda x: -x[1])
        return out

    D = D_score()

    def ranks(lst):
        return {n: i + 1 for i, (n, _) in enumerate(lst)}

    def spearman(x, y):
        rx, ry = ranks(x), ranks(y)
        n = len(rx)
        d2 = sum((rx[k] - ry[k]) ** 2 for k in rx)
        return 1 - 6 * d2 / (n * (n * n - 1))

    def kendall_tau(x, y):
        rx, ry = ranks(x), ranks(y)
        conc = disc = 0
        keys = list(rx)
        for i in range(len(keys)):
            for j in range(i + 1, len(keys)):
                a, b = keys[i], keys[j]
                s = (rx[a] - rx[b]) * (ry[a] - ry[b])
                if s > 0:
                    conc += 1
                elif s < 0:
                    disc += 1
        return (conc - disc) / ((conc + disc) or 1)

    print("=" * 78)
    print("SENSITIVITY: log-transform vs raw values")
    print("=" * 78)
    print()
    for label, variant in (("B  raw + min-max", B), ("C  raw + z-score", C),
                            ("D  raw + percentile", D)):
        sp = spearman(A, variant)
        kt = kendall_tau(A, variant)
        print(f"  {label:<22} vs shipped A:  Spearman rho = {sp:+.3f}   "
              f"Kendall tau = {kt:+.3f}")
    print()

    rA, rB, rC, rD = ranks(A), ranks(B), ranks(C), ranks(D)
    print("--- TOP 15 under each variant ---")
    print(f"{'A: log+minmax':<28} {'B: raw+minmax':<28} {'C: raw+zscore':<28}")
    for i in range(15):
        a = A[i][0]
        b = B[i][0]
        c = C[i][0]
        print(f"  {i+1:>2}. {a[:25]:<25}  {i+1:>2}. {b[:25]:<25}  {i+1:>2}. {c[:25]:<25}")
    print()

    print("--- biggest movers: shipped (A) vs raw min-max (B) ---")
    movers = sorted(rA, key=lambda n: abs(rA[n] - rB[n]), reverse=True)[:12]
    for n in movers:
        d = rB[n] - rA[n]
        arrow = "UP  " if d < 0 else "DOWN"
        print(f"  {arrow} {n[:40]:<40}  A #{rA[n]:<3} -> B #{rB[n]:<3}  ({d:+d})")
    print()

    # --- the failure diagnostic: how many rows collapse to ~zero ----------
    b_scores = dict(B)
    collapsed = [n for n, s in b_scores.items() if s < 5.0]
    print("--- WHY raw fails: the tail collapses ---")
    print(f"  Rows scoring < 5.0/100 under raw min-max:  {len(collapsed)} of {len(B)}")
    print(f"  Rows scoring < 5.0/100 under shipped A:    "
          f"{len([1 for n, s in dict(A).items() if s < 5.0])} of {len(A)}")
    print()
    print("  How much of each axis one company occupies (raw min-max):")
    for n, v, a in (("Anthropic", 965.0, 100000),
                    ("OpenAI", 852.0, 50000),
                    ("Microsoft (AI business)", 740.0, 37000),
                    ("Reworkd AI", 0.1, 10)):
        vmin, vmax = 0.1, 965.0
        amin, amax = 10, 100000
        print(f"    {n:<24} valuation z={(v - vmin) / (vmax - vmin):.4f}   "
              f"ARR z={(a - amin) / (amax - amin):.4f}")
    print()
    print("  With raw min-max, the #2 company (OpenAI) scores 0.5 on the ARR axis")
    print("  while every company below ~$1B ARR scores < 0.01. A company with")
    print("  $900M ARR and a company with $12M ARR are ~15x apart in reality but")
    print("  0.009 vs 0.0002 after linear min-max - indistinguishable.")
    print()

    # --- D: percentile is the robust alternative -------------------------
    print("--- D (raw + percentile rank) top 12: robust to scale choice ---")
    for i in range(12):
        n, s = D[i]
        print(f"  {i+1:>2}. {n[:34]:<34} score={s:6.2f}   (A rank #{rA[n]})")
    print()
    d_movers = sorted(rA, key=lambda n: abs(rA[n] - rD[n]), reverse=True)[:8]
    print("  biggest movers A vs D:")
    for n in d_movers:
        print(f"    {n[:40]:<40}  A #{rA[n]:<3} -> D #{rD[n]:<3}  ({rD[n] - rA[n]:+d})")
    print()

    # --- write a machine-readable summary for the site --------------------
    summary = {
        "shipped": "A: log + min-max",
        "variants": {},
    }
    for label, variant in (("raw_minmax", B), ("raw_zscore", C), ("raw_percentile", D)):
        summary["variants"][label] = {
            "spearman_vs_shipped": round(spearman(A, variant), 3),
            "kendall_tau_vs_shipped": round(kendall_tau(A, variant), 3),
            "rows_below_5_points": len([1 for _, s in variant if s < 5.0]),
            "top10": [n for n, _ in variant[:10]],
        }
    summary["variants"]["log_minmax_shipped"] = {
        "spearman_vs_shipped": 1.0,
        "kendall_tau_vs_shipped": 1.0,
        "rows_below_5_points": len([1 for _, s in A if s < 5.0]),
        "top10": [n for n, _ in A[:10]],
    }
    out = ROOT / "data" / "sensitivity.json"
    out.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
