"""
anchor_headroom.py - how much room is left before the fixed bounds need
re-anchoring?

The bounds are fixed policy, and the policy has two different tripwires:

  * the RE-ANCHOR TRIGGER: "a company has breached a bound by more than one
    third of the axis span - i.e. an anchor that is about to be crossed
    rather than one that has been crossed"
  * the STALE-ANCHOR SCORE FLAG: scores are not clipped, so a score above 100
    is the signal that an anchor is stale

These two can disagree. If the score flag fires long before the re-anchor
trigger, the policy tells you to do something (review) that it also says is
premature (don't re-anchor yet). This script measures the actual margins.

Run:
    python scripts/anchor_headroom.py
"""

import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    ranked = json.loads((ROOT / "data" / "ranked.json").read_text(encoding="utf-8"))
    rows = ranked["companies"]
    cfg = json.loads((ROOT / "data" / "model_config.json").read_text(encoding="utf-8"))

    vmin, vmax = cfg["axis"]["valuation_usd_b"]
    amin, amax = cfg["axis"]["arr_usd_m"]
    vspan = math.log10(vmax) - math.log10(vmin)
    aspan = math.log10(amax) - math.log10(amin)
    third_v = vspan / 3.0
    third_a = aspan / 3.0

    L = []
    W = 100
    L.append("=" * W)
    L.append("ANCHOR HEADROOM - margin on each fixed bound")
    L.append("=" * W)
    L.append("")
    L.append(f"  valuation axis: ${vmin}B - ${vmax}B   span {vspan:.2f} decades, "
             f"re-anchor trigger = {third_v:.2f} decades past a bound")
    L.append(f"  ARR axis      : ${amin}M - ${amax}M   span {aspan:.2f} decades, "
             f"re-anchor trigger = {third_a:.2f} decades past a bound")
    L.append("")

    top = max(rows, key=lambda c: c["score"])
    L.append(f"  top row today: {top['name'][:34]}  score {top['score']:.2f}  "
             f"z_val {top['z_val']:.4f}  z_arr {top['z_arr']:.4f}")
    L.append("")

    # --- the score flag ----------------------------------------------------
    L.append("-" * W)
    L.append("WHEN DOES THE #1 SCORE CROSS 100? (the stale-anchor signal)")
    L.append("-" * W)
    L.append("")
    # score = 50 * (z_val + z_arr) > 100  ->  z_val + z_arr > 2
    need_z = 2.0 - top["z_val"]
    log_arr_needed = amin_log = math.log10(amin)
    log_arr_needed = log_arr_needed + need_z * aspan
    arr_needed = 10 ** log_arr_needed
    L.append(f"  Anthropic's z_val is {top['z_val']:.4f}, so the score crosses 100 when")
    L.append(f"  z_arr reaches {need_z:.4f}, i.e. ARR of ${arr_needed:,.0f}M "
             f"(${arr_needed / 1000:,.1f}B)")
    L.append(f"  Anthropic's ARR is ${top['arr_usd_m']:,.0f}M - so the flag fires at "
             f"{arr_needed / top['arr_usd_m']:.3f}x its current ARR.")
    L.append("")

    # --- each bound --------------------------------------------------------
    L.append("-" * W)
    L.append("MARGIN ON EACH BOUND")
    L.append("-" * W)
    L.append("")

    checks = [
        ("valuation top", vmax, max, "valuation_usd_b", "B", vspan, third_v),
        ("valuation floor", vmin, min, "valuation_usd_b", "B", vspan, third_v),
        ("ARR top", amax, max, "arr_usd_m", "M", aspan, third_a),
        ("ARR floor", amin, min, "arr_usd_m", "M", aspan, third_a),
    ]
    for label, bound, pick, field, unit, span, third in checks:
        cand = [c for c in rows if c.get(field) is not None]
        extreme = pick(cand, key=lambda c: c[field])
        ev = extreme[field]
        if pick is max:
            trigger = bound * (10 ** third)
            margin = trigger / ev
            direction = "above"
        else:
            trigger = bound / (10 ** third)
            margin = ev / trigger
            direction = "below"
        L.append(f"  {label:<16} bound ${bound:,.10g}{unit}   "
                 f"nearest row {extreme['name'][:26]:<28} ${ev:,.10g}{unit}")
        L.append(f"  {'':<16} re-anchor trigger at ${trigger:,.10g}{unit} "
                 f"({direction} the bound) = {margin:,.1f}x away")
    L.append("")

    # --- how were the bounds pinned? --------------------------------------
    L.append("-" * W)
    L.append("HOW WERE THE BOUNDS CHOSEN?")
    L.append("-" * W)
    L.append("")
    src = json.loads((ROOT / "data" / "companies.json").read_text(encoding="utf-8"))["companies"]
    rw = next((c for c in src if c["name"] == "Reworkd AI"), None)
    L.append("  The four bounds trace back to two companies:")
    if rw:
        L.append(f"    Reworkd AI   valuation ${rw.get('valuation_usd_b')}B   "
                 f"ARR ${rw.get('arr_usd_m')}M   <- the two FLOORS")
    an = next((c for c in rows if c["name"] == "Anthropic"), None)
    if an:
        L.append(f"    Anthropic   valuation ${an['valuation_usd_b']}B   "
                 f"ARR ${an['arr_usd_m']}M   <- the two CEILINGS")
    L.append("")
    inlist = [c["name"] for c in rows]
    L.append(f"    Reworkd AI is in the Top 100 today: {'Reworkd AI' in inlist}")
    L.append("")
    L.append("  So the axis is pinned at the bottom to a company that has fallen out")
    L.append("  of the list, and at the top to the company that is still #1. The")
    L.append("  consequence is asymmetric headroom:")
    L.append("    - at the BOTTOM, dead space (the floor no longer touches the data)")
    L.append("    - at the TOP, almost none on ARR (Anthropic sits exactly on it)")

    (ROOT / ".tmp_headroom.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
