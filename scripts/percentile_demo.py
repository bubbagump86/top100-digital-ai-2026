"""
percentile_demo.py - what the raw + percentile variant (D) actually does.

Variant D replaces the rescaling step. Instead of

    z = (x - min) / (max - min)          [min-max, on whatever scale]

each value is replaced by its EMPIRICAL PERCENTILE RANK among all rows:

    z = (number of rows below x + (ties - 1)/2) / (n - 1)

Only the ORDER of the values matters. Log or raw, dollars or billions, the
percentile is identical - which is the variant's appeal: it makes the
"which transform?" argument disappear, because it never uses the transform.

This script prints the shipped model's z-values beside variant D's for the
rows where the difference is most instructive.

Run:
    python scripts/percentile_demo.py
"""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from sensitivity import pctrank  # noqa: E402


def main():
    ranked = json.loads((ROOT / "data" / "ranked.json").read_text(encoding="utf-8"))
    rows = ranked["companies"]

    vv = [c["valuation_usd_b"] for c in rows if c["valuation_usd_b"]]
    av = [c["arr_usd_m"] for c in rows if c["arr_usd_m"]]
    vs, as_ = pctrank(vv), pctrank(av)

    def d_score(c):
        zv = vs.get(c["valuation_usd_b"]) if c["valuation_usd_b"] is not None else None
        za = as_.get(c["arr_usd_m"]) if c["arr_usd_m"] is not None else None
        if zv is None and za is None:
            return 0.0
        if zv is None:
            return 50.0 * za
        if za is None:
            return 50.0 * zv
        return 50.0 * (zv + za)

    scored = sorted(((c["name"], d_score(c)) for c in rows), key=lambda x: -x[1])
    drank = {n: i + 1 for i, (n, _) in enumerate(scored)}
    dsc = dict(scored)

    L = []
    W = 108
    L.append("=" * W)
    L.append("VARIANT D - raw + percentile rank - beside the shipped log + min-max")
    L.append("=" * W)
    L.append("")
    L.append("  shipped z_val = (log10(val) - log_min) / 4      anchored bounds")
    L.append("  shipped z_arr = (log10(arr) - log_min) / 4")
    L.append("  variant D z   = percentile rank among the rows that have a value")
    L.append("")
    L.append(f"{'company':<38}{'shipped z_val':>14}{'D z_val':>10}"
             f"{'shipped z_arr':>15}{'D z_arr':>10}{'shipped rk':>12}{'D rk':>7}")
    L.append("-" * W)

    show = [
        "Anthropic", "OpenAI", "Microsoft (AI business)",
        "Google / Alphabet (AI: Gemini + Cloud AI)",
        "Palantir Technologies",
        "ByteDance (AI: Doubao + Seed + Volcano Engine)",
        "Midjourney", "Suno",
        "Zhipu AI (Z.ai)", "SandboxAQ", "Sakana AI",
        "Safe Superintelligence (SSI)", "Otter.ai",
    ]
    by = {c["name"]: c for c in rows}
    for n in show:
        c = by.get(n)
        if not c:
            continue
        zv_s = "n/a" if c["z_val"] is None else f"{c['z_val']:.4f}"
        za_s = "n/a" if c["z_arr"] is None else f"{c['z_arr']:.4f}"
        zv_d = "n/a" if not c["valuation_usd_b"] else f"{vs.get(c['valuation_usd_b']):.4f}"
        za_d = "n/a" if not c["arr_usd_m"] else f"{as_.get(c['arr_usd_m']):.4f}"
        L.append(f"{n[:37]:<38}{zv_s:>14}{zv_d:>10}{za_s:>15}{za_d:>10}"
                 f"{c['rank']:>12}{drank[n]:>7}")
    L.append("-" * W)
    L.append("")

    # The distributional difference that matters.
    L.append("=" * W)
    L.append("WHERE THE TWO SCALES DISAGREE MOST")
    L.append("=" * W)
    L.append("")
    have_arr = [c for c in rows if c["arr_usd_m"]]
    med_arr = sorted(c["arr_usd_m"] for c in have_arr)[len(have_arr) // 2]
    lo = min(c["arr_usd_m"] for c in have_arr)
    hi = max(c["arr_usd_m"] for c in have_arr)
    import math
    z_ship_med = (math.log10(med_arr) - 1) / 4
    z_d_med = as_.get(med_arr)
    L.append(f"  ARR axis, {len(have_arr)} rows with a value, range ${lo:,.0f}M - ${hi:,.0f}M")
    L.append(f"    median ARR ${med_arr:,.0f}M:")
    L.append(f"      shipped log + min-max : z = {z_ship_med:.4f}")
    L.append(f"      variant D percentile  : z = {z_d_med:.4f}")
    L.append("")
    n_at_med = sum(1 for c in have_arr if c["arr_usd_m"] == med_arr)
    n_below = sum(1 for c in have_arr if c["arr_usd_m"] < med_arr)
    L.append(f"    (that value is a {n_at_med}-way tie, with {n_below} rows below it, so its")
    L.append(f"     midrank percentile is {z_d_med:.4f} rather than exactly 0.5)")
    L.append("")
    L.append("  The middle of the list sits near the MIDDLE of the scale under D -")
    L.append("  by definition - and at 0.25 under the shipped log scale. That is the")
    L.append("  whole difference: log min-max preserves DISTANCE, and because")
    L.append("  ARR is a power law most companies sit near the bottom of the log")
    L.append("  scale; percentile preserves RANK, so the middle of the list gets")
    L.append("  the middle of the scale.")
    L.append("")
    below1b = sum(1 for c in have_arr if c["arr_usd_m"] < 1000)
    L.append(f"  {below1b} of the {len(have_arr)} rows with ARR are under $1B - a heavy")
    L.append("  bottom-load in dollars that percentile rank flattens out.")
    L.append("")

    # Why the proxies fall under D even though their absolute score rises.
    L.append("=" * W)
    L.append("WHY THE PROXY ROWS FALL UNDER D (their absolute score RISES)")
    L.append("=" * W)
    L.append("")
    L.append(f"{'company':<38}{'shipped':>12}{'D':>10}{'shipped rk':>12}{'D rk':>7}")
    for n in ["Palantir Technologies",
              "ByteDance (AI: Doubao + Seed + Volcano Engine)",
              "Midjourney", "Suno", "Otter.ai"]:
        c = by.get(n)
        if not c:
            continue
        L.append(f"{n[:37]:<38}{c['score']:>12.2f}{dsc[n]:>10.2f}"
                 f"{c['rank']:>12}{drank[n]:>7}")
    L.append("")
    L.append("  A proxy row has a high valuation percentile but NO ARR, so its ARR")
    L.append("  axis reads 0 and it cannot gain on the axis that most rows gain")
    L.append("  on. Its score rises in absolute terms and its RANK falls.")

    (ROOT / ".tmp_pctdemo.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
