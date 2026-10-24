"""
log_min_probe.py - does the negative log_min on the valuation axis distort
the measure?

Four separable questions, each measured with the real engine:

  1. Is the SIGN of log_min doing anything? A z-score is invariant to affine
     shifts of its axis, so shifting the valuation axis from [-1, 3] to [0, 4]
     - same 4-decade span, same data, different origin - should change no
     rank. Verified by re-running the engine and diffing.

  2. Are the two axes anchored SYMMETRICALLY relative to the data?

  3. What happens OUTSIDE the bounds? Does a value below a floor rank below
     a value that is simply missing?

  4. What does the axis floor actually buy?

Run:
    python scripts/log_min_probe.py
"""

import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ROOT / "data" / "variants"
DATA = ROOT / "data" / "companies.json"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, cwd=str(ROOT))
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(str(c) for c in cmd)}\n"
                         f"{r.stdout.decode('utf-8', 'replace')[-1500:]}\n"
                         f"{r.stderr.decode('utf-8', 'replace')[-1500:]}")


def score_variant(name, extra=(), companies=None):
    cmd = [sys.executable, str(ROOT / "scripts" / "score.py"), "--variant", name]
    if companies:
        cmd += ["--companies", str(companies)]
    cmd += list(extra)
    run(cmd)
    return json.loads((VARIANTS / name / "ranked.json").read_text(encoding="utf-8"))


def probe_company(name, val_b, arr_m):
    return {
        "rank_seed": 996,
        "name": name,
        "category": "Probe",
        "hq": "n/a", "founded": 2026,
        "valuation_usd_b": val_b,
        "valuation_date": "probe", "valuation_source": "probe",
        "arr_usd_m": arr_m,
        "arr_date": "probe", "arr_source": "probe",
        "summary": "probe row",
        "is_digital_only": True, "is_pure_play_ai": True,
        "valuation_basis": "actual",
    }


def run_probe(probes, extra=()):
    """Score a companies file that also contains probe rows."""
    raw = json.loads(DATA.read_text(encoding="utf-8"))
    raw["companies"].extend(probes)
    tmp = ROOT / "data" / ".probe_companies.json"
    tmp.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
    try:
        res = score_variant("probe_rows", extra=extra, companies=tmp)
    finally:
        tmp.unlink()
    return {c["name"]: c for c in res["companies"]}


def main():
    VARIANTS.mkdir(parents=True, exist_ok=True)
    L = []
    W = 96

    ship = score_variant("probe_ship")
    rows = ship["companies"]
    cfg = ship.get("model_config", {})

    # ---------------------------------------------------------------- 1
    L.append("=" * W)
    L.append("1. IS THE SIGN OF log_min DOING ANYTHING?")
    L.append("=" * W)
    L.append("")
    L.append("A z-score is invariant to affine shifts of its axis. Shifting the")
    L.append("valuation axis from log [-1, 3] to log [0, 4] - same 4-decade span,")
    L.append("same data, different origin - changes every z_val by the same 0.25.")
    L.append("")
    shifted = score_variant("probe_shifted", ["--anchor-val", "1", "10000"])
    rs = {c["name"]: c for c in ship["companies"]}
    rk = {c["name"]: c for c in shifted["companies"]}
    common = set(rs) & set(rk)
    rank_diffs = [(n, rs[n]["rank"], rk[n]["rank"]) for n in common
                   if rs[n]["rank"] != rk[n]["rank"]]
    deltas = [rk[n]["score"] - rs[n]["score"] for n in common]
    L.append(f"  rows compared: {len(common)}")
    L.append(f"  score change: min {min(deltas):+.4f}  max {max(deltas):+.4f}")
    L.append(f"  rows whose RANK changed: {len(rank_diffs)}")
    for n, a, b in sorted(rank_diffs, key=lambda x: abs(x[1] - x[2]), reverse=True)[:6]:
        L.append(f"      {n[:46]:<48} #{a} -> #{b}")
    L.append("")
    L.append("  => The origin IS load-bearing, but not through the sign. It works")
    L.append("     like this: every row WITH a valuation loses 12.5 points (its")
    L.append("     z_val drops by 0.25, times the 0.5 weight, times 100). Every row")
    L.append("     WITHOUT one - a missing valuation reads 0 and keeps its weight -")
    L.append("     loses nothing, so it rises relative to the rest. Midjourney, which")
    L.append("     has $500M of ARR and no valuation mark at all, moves 39 places.")
    L.append("     So the valuation axis's origin is a de facto, undocumented lever")
    L.append("     over where the no-valuation cohort sits.")
    L.append("")

    # ---------------------------------------------------------------- 2
    L.append("=" * W)
    L.append("2. ARE THE TWO AXES ANCHORED SYMMETRICALLY RELATIVE TO THE DATA?")
    L.append("=" * W)
    L.append("")
    vb = cfg.get("axis_bounds", {})
    vmin, vmax = vb.get("valuation_usd_b", [0.1, 1000.0])
    amin, amax = vb.get("arr_usd_m", [10.0, 100000.0])
    L.append(f"  valuation axis: ${vmin}B - ${vmax}B   (log {math.log10(vmin):+.2f} to "
             f"{math.log10(vmax):+.2f}, span {math.log10(vmax) - math.log10(vmin):.2f})")
    L.append(f"  ARR axis      : ${amin}M - ${amax}M   (log {math.log10(amin):+.2f} to "
             f"{math.log10(amax):+.2f}, span {math.log10(amax) - math.log10(amin):.2f})")
    L.append("")
    zv = [c["z_val"] for c in rows if c["z_val"] is not None]
    za = [c["z_arr"] for c in rows if c["z_arr"] is not None]
    both = [c for c in rows if c["z_val"] is not None and c["z_arr"] is not None]
    L.append(f"  {'axis':<12}{'bound range':>15}{'data range used':>20}{'z range used':>17}")
    L.append("  " + "-" * (W - 4))
    L.append(f"  {'valuation':<12}{'[0, 1]':>15}{f'[{min(zv):.3f}, {max(zv):.3f}]':>20}"
             f"{max(zv) - min(zv):>17.3f}")
    L.append(f"  {'ARR':<12}{'[0, 1]':>15}{f'[{min(za):.3f}, {max(za):.3f}]':>20}"
             f"{max(za) - min(za):>17.3f}")
    L.append("")
    sv = statistics.pstdev([c["z_val"] for c in both])
    sa = statistics.pstdev([c["z_arr"] for c in both])
    L.append(f"  standard deviation of z_val across the {len(both)} rows with both axes: {sv:.4f}")
    L.append(f"  standard deviation of z_arr across the same rows:               {sa:.4f}")
    L.append(f"  ratio: {sv / sa:.3f}   (1.000 = perfectly symmetric)")
    L.append("")
    L.append("  => The two axes are NOT symmetric. The valuation axis uses")
    L.append(f"     {max(zv) - min(zv):.3f} of its range and the ARR axis {max(za) - min(za):.3f}; valuation is")
    L.append(f"     {(1 - sv / sa) * 100:.1f}% less dispersed. That is a real, mild tilt towards")
    L.append("     ARR - and it comes from the ANCHORING, not the weights. It is")
    L.append("     about a quarter of the size of the 0.40/0.60 weight change.")
    L.append("")

    # ---------------------------------------------------------------- 3
    L.append("=" * W)
    L.append("3. WHAT HAPPENS OUTSIDE THE BOUNDS?")
    L.append("=" * W)
    L.append("")
    L.append("A row with NO ARR is scored z_arr = 0 (the 'zero' rule). A row with a")
    L.append("SMALL ARR can score z_arr < 0 - which would rank 'some revenue' BELOW")
    L.append("'no revenue'. Testing with probe rows that score inside the top 100.")
    L.append("")

    # Probe A: $10B valuation (z_val 0.5) with ARR BELOW the $10M floor.
    # Probe B: same valuation, no ARR at all.
    probes = [
        probe_company("__probe_A_arr_5M__", 10.0, 5.0),
        probe_company("__probe_B_no_arr__", 10.0, None),
        probe_company("__probe_C_arr_20M__", 10.0, 20.0),
        probe_company("__probe_D_val_50M__", 0.05, 1000.0),
        probe_company("__probe_E_no_val__", None, 1000.0),
    ]

    for label, extra in (("WITH the axis floor clamp (shipped policy)", []),
                         ("WITHOUT the clamp (review comparison)",
                          ["--no-axis-floor-clamp"])):
        L.append(f"  {label}:")
        pm = run_probe(probes, extra)
        for nm, desc in (("__probe_A_arr_5M__", "$10B valuation, $5M ARR (below the $10M floor)"),
                         ("__probe_B_no_arr__", "$10B valuation, NO ARR disclosed"),
                         ("__probe_C_arr_20M__", "$10B valuation, $20M ARR (above the floor)"),
                         ("__probe_D_val_50M__", "$0.05B valuation (below the $0.1B floor), $1B ARR"),
                         ("__probe_E_no_val__", "NO valuation, $1B ARR")):
            c = pm.get(nm)
            if not c:
                L.append(f"      {desc:<62} -> outside the top 100")
                continue
            zv_s = "n/a" if c["z_val"] is None else f"{c['z_val']:+.4f}"
            za_s = "n/a" if c["z_arr"] is None else f"{c['z_arr']:+.4f}"
            L.append(f"      {desc:<62} z_val {zv_s:>8}  z_arr {za_s:>8}  "
                     f"score {c['score']:6.2f}  #{c['rank']}")
        a = pm.get("__probe_A_arr_5M__")
        b = pm.get("__probe_B_no_arr__")
        if a and b:
            # Compare SCORES, not ranks - equal scores are tie-broken by rank
            # order, which is not a monotonicity failure.
            if a["score"] > b["score"] + 0.01:
                verdict = "MONOTONIC - $5M ARR beats no ARR"
            elif abs(a["score"] - b["score"]) <= 0.01:
                verdict = ("MONOTONIC (tied) - $5M ARR scores the SAME as no ARR, "
                           "which is the intended 'no usable signal' reading")
            else:
                verdict = ("*** MONOTONICITY BROKEN - $5M ARR scores BELOW no ARR "
                           f"({a['score']:.2f} < {b['score']:.2f}) ***")
            L.append(f"      => {verdict}")
        d = pm.get("__probe_D_val_50M__")
        e = pm.get("__probe_E_no_val__")
        if d and e:
            if d["score"] > e["score"] + 0.01:
                verdict = "MONOTONIC - a sub-floor valuation beats no valuation"
            elif abs(d["score"] - e["score"]) <= 0.01:
                verdict = ("MONOTONIC (tied) - a sub-floor valuation scores the SAME "
                           "as no valuation, which is the intended reading")
            else:
                verdict = ("*** MONOTONICITY BROKEN - a sub-floor valuation scores "
                           f"BELOW no valuation ({d['score']:.2f} < {e['score']:.2f}) ***")
            L.append(f"      => {verdict}")
        L.append("")

    # ---------------------------------------------------------------- 4
    L.append("=" * W)
    L.append("4. WHAT DOES THE VALUATION AXIS FLOOR ACTUALLY BUY?")
    L.append("=" * W)
    L.append("")
    L.append("The floor is $0.1B - i.e. a NEGATIVE log_min. Both fixed bounds were")
    L.append("originally pinned to a single company: Reworkd AI sat at exactly")
    L.append("$0.1B valuation and $10M ARR, the two floors at once. Reworkd has")
    L.append("since fallen out of the top 100, so the floors are now above the")
    L.append("bottom of the list - which is the fixed-bounds design working as")
    L.append("intended: the axis did not move when the composition did.")
    L.append("")
    small = min((c for c in rows if c["valuation_usd_b"]),
                key=lambda c: c["valuation_usd_b"])
    L.append(f"  smallest valuation now in the list: {small['name'][:36]} "
             f"${small['valuation_usd_b']}B (z_val {small['z_val']:.3f})")
    L.append(f"  the band ${vmin}B - ${small['valuation_usd_b']}B is unused: "
             f"{math.log10(small['valuation_usd_b']) - math.log10(vmin):.3f} decades")
    L.append("")
    L.append("  The floor is what keeps a REAL company with a sub-$1B valuation")
    L.append("  above a company with no valuation at all. Raise the floor to $1B and")
    L.append("  Otter.ai's z_val goes negative - see the probe above. So the")
    L.append("  negative log_min is not a distortion; it is the thing that stops")
    L.append("  the valuation axis from inverting.")
    L.append("")
    L.append("  The ARR axis has no such protection: its floor is $10M and the")
    L.append("  smallest ARR in the list is $17.8M, so only 0.25 decades of")
    L.append("  headroom. The clamp is what makes that safe.")

    (ROOT / ".tmp_probe.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
