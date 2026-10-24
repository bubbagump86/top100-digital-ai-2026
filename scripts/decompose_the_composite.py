"""
decompose_the_composite.py - what do the two axes actually contribute?

For any pure-play, valuation and ARR are not independent: valuation IS
ARR x (a multiple). So the composite can be rewritten exactly:

    z_val = z_arr + (log10(multiple) - 1) / 4

    composite = 100 * (w_val * z_val + w_arr * z_arr)
              = 100 * ( z_arr  +  w_val * (log10 m - 1) / 4 )
                             \_ ARR _/    \_ multiple premium _/

The ARR LEVEL carries weight 1.0 no matter how the axes are split. The
valuation axis contributes only the MULTIPLE PREMIUM - how many times ARR
the market pays - at w_val / 4 per decade.

So "50/50 valuation and revenue" is not a 50/50 in substance. It is an
ARR-level model with a multiple-premium adjustment. Re-weighting revenue
does not shift the balance towards revenue level; it shrinks the multiple
premium by 20% and does nothing to the level term.

This script verifies the identity against the live dataset and reports how
much of the composite's spread each term explains.

Run:
    python scripts/decompose_the_composite.py
"""

import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
AXIS_SPAN = 4.0   # both anchored axes span 4 log decades


def main():
    ranked = json.loads((ROOT / "data" / "ranked.json").read_text(encoding="utf-8"))
    rows = ranked["companies"]
    w = ranked.get("weights", {"valuation": 0.5, "arr": 0.5})
    w_val = float(w["valuation"])

    L = []
    L.append("=" * 92)
    L.append("DECOMPOSING THE COMPOSITE: ARR level vs multiple premium")
    L.append("=" * 92)
    L.append("")
    L.append("For a pure-play, valuation = ARR x multiple, so:")
    L.append("    z_val = z_arr + (log10(multiple) - 1) / 4")
    L.append("    composite = 100 * ( z_arr + w_val * (log10 m - 1) / 4 )")
    L.append("              ^ ARR level     ^ multiple premium")
    L.append("")
    L.append("Checking the identity against the live dataset:")
    L.append("")
    L.append(f"{'company':<34}{'mult':>8}{'predicted':>11}{'actual':>9}{'err':>10}")
    L.append("-" * 92)

    errs = []
    pure = [c for c in rows
            if c["valuation_basis"] == "actual"
            and c.get("valuation_usd_b") and c.get("arr_usd_m")
            and c["z_val"] is not None and c["z_arr"] is not None]
    for c in sorted(pure, key=lambda x: -x["rank"])[:16]:
        m = c["valuation_usd_b"] * 1000.0 / c["arr_usd_m"]
        pred = c["z_arr"] + (math.log10(m) - 1) / AXIS_SPAN
        err = c["z_val"] - pred
        errs.append(abs(err))
        L.append(f"{c['name'][:33]:<34}{m:>8.1f}{pred:>11.4f}{c['z_val']:>9.4f}{err:>10.4f}")
    L.append("-" * 92)
    L.append(f"max |error| on the sampled pure-plays: {max(errs):.4f}  "
             f"(rounding in the stored valuation/ARR)")
    L.append("")

    # How much of the score's spread does each term explain?
    arr_term = [c["z_arr"] for c in pure]
    mult_term = [w_val * (math.log10(c["valuation_usd_b"] * 1000.0 / c["arr_usd_m"]) - 1) / AXIS_SPAN
                 for c in pure]
    var_arr = statistics.pvariance(arr_term)
    var_mult = statistics.pvariance(mult_term)
    var_total = statistics.pvariance([a + b for a, b in zip(arr_term, mult_term)])

    L.append("=" * 92)
    L.append(f"VARIANCE OF THE COMPOSITE ACROSS {len(pure)} PURE-PLAYS (shipped weights)")
    L.append("=" * 92)
    L.append(f"  ARR level term           variance {var_arr:>8.5f}   "
             f"({var_arr / var_total * 100:>5.1f}% of total)")
    L.append(f"  multiple premium term    variance {var_mult:>8.5f}   "
             f"({var_mult / var_total * 100:>5.1f}% of total)")
    L.append(f"  total                                              {var_total:>8.5f}")
    L.append("")
    L.append("  The multiple premium's influence scales with w_val / 4:")
    for wv in (0.5, 0.45, 0.4, 0.35, 0.3):
        L.append(f"    w_val={wv:.2f}  ->  {wv / AXIS_SPAN:.4f} per decade of multiple "
                 f"({wv / 0.5 * 100 - 100:+.0f}% vs shipped)")
    L.append("")
    L.append("  The ARR level term's weight is 1.0 at EVERY split. Re-weighting")
    L.append("  revenue does not change how much ARR level counts; it only shrinks")
    L.append("  the premium the market's multiple adds.")

    # The multiple range the model is actually paying for.
    mults = sorted(c["valuation_usd_b"] * 1000.0 / c["arr_usd_m"] for c in pure)
    L.append("")
    L.append(f"  Pure-play multiple range: {mults[0]:.1f}x (low) to {mults[-1]:.1f}x (high), "
             f"median {statistics.median(mults):.1f}x")
    L.append(f"  A 10x-to-323x spread is {math.log10(mults[-1]) - math.log10(mults[0]):.2f} "
             f"decades = {(math.log10(mults[-1]) - math.log10(mults[0])) * w_val / AXIS_SPAN * 100:.1f} "
             f"score points of premium at the shipped weights")
    L.append(f"  and {(math.log10(mults[-1]) - math.log10(mults[0])) * 0.4 / AXIS_SPAN * 100:.1f} "
             f"points at 0.40/0.60.")

    (ROOT / ".tmp_decompose.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
