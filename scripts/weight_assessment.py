"""
weight_assessment.py - how much does the composite's axis weighting matter?

The composite is S = 100 * (w_val * z_log(val) + w_arr * z_log(arr)). The
shipped split is 50/50. This script measures what happens if ARR is weighted
more heavily - the change most often proposed for this model, on the argument
that revenue is the harder number to fake and valuation is a negotiated round
price.

For each candidate split it re-runs the REAL pipeline (scripts/score.py) into
a variant directory, then runs the two robustness analyses against that
variant, and reports:

  * rank correlation vs the shipped 50/50 list, and how many rows move
  * whether the top 11 survives the change
  * whether the top 11 still survives the peer multiple at 10x-40x
  * how the scale-choice sensitivity (log vs raw) shifts under the new weights
  * what happens to pre-revenue labs, which have no ARR axis to score on

Nothing here writes to the live outputs: every run goes to
data/variants/<name>/ (git-ignored) and every analysis output goes to a
temporary file.

Run:
    python scripts/weight_assessment.py
"""

import json
import math
import statistics
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ROOT / "data" / "variants"
SHIPPED = "w050"

# (w_val, w_arr) pairs to test. w_arr is the parameter under discussion.
SPLITS = [
    (0.50, 0.50),   # shipped
    (0.45, 0.55),
    (0.40, 0.60),   # the proposed change
    (0.35, 0.65),
    (0.30, 0.70),
]

MULTIPLES = [10, 12, 15, 20, 25, 30, 40]


def name_for(w_val, w_arr):
    return f"w{int(round(w_val * 100)):03d}"


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, cwd=str(ROOT))
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(str(c) for c in cmd)}\n"
                         f"{r.stdout.decode('utf-8', 'replace')[-2000:]}\n"
                         f"{r.stderr.decode('utf-8', 'replace')[-2000:]}")
    return r.stdout.decode("utf-8", "replace")


def score_variant(w_val, w_arr):
    name = name_for(w_val, w_arr)
    run([sys.executable, str(ROOT / "scripts" / "score.py"),
         "--variant", name, "--weight-val", str(w_val),
         "--weight-arr", str(w_arr)])
    return name


def analyse_variant(name):
    """Run the two robustness analyses against a variant ranking."""
    ranked = json.loads((VARIANTS / name / "ranked.json").read_text(encoding="utf-8"))

    mc_out = VARIANTS / name / "multiple_check.json"
    run([sys.executable, str(ROOT / "scripts" / "multiple_check.py"),
         "--input", str(VARIANTS / name / "ranked.json"),
         "--out", str(mc_out)])
    mc = json.loads(mc_out.read_text(encoding="utf-8"))

    sens_out = VARIANTS / name / "sensitivity.json"
    run([sys.executable, str(ROOT / "scripts" / "sensitivity.py"),
         "--input", str(VARIANTS / name / "ranked.json"),
         "--out", str(sens_out)])
    sens = json.loads(sens_out.read_text(encoding="utf-8"))

    return ranked, mc, sens


def ranks_of(ranked):
    return {c["name"]: c["rank"] for c in ranked["companies"]}


def scores_of(ranked):
    return {c["name"]: c["score"] for c in ranked["companies"]}


def spearman(a, b):
    """Rank correlation between two {name: rank} dicts over common names."""
    keys = set(a) & set(b)
    n = len(keys)
    if n < 2:
        return 1.0
    d2 = sum((a[k] - b[k]) ** 2 for k in keys)
    return 1 - 6 * d2 / (n * (n * n - 1))


def main():
    VARIANTS.mkdir(parents=True, exist_ok=True)
    results = []

    for w_val, w_arr in SPLITS:
        name = score_variant(w_val, w_arr)
        ranked, mc, sens = analyse_variant(name)
        rows = ranked["companies"]
        results.append({
            "name": name,
            "w_val": w_val,
            "w_arr": w_arr,
            "ranks": ranks_of(ranked),
            "scores": scores_of(ranked),
            "top11_always": mc["top11_stability"]["always_present"],
            "top11_count": mc["top11_stability"]["min_always_count"],
            "sens": {k: {"rho": v["spearman_vs_shipped"],
                         "tau": v["kendall_tau_vs_shipped"],
                         "below5": v["rows_below_5_points"]}
                     for k, v in sens["variants"].items()},
            "rows": rows,
        })
        print(f"  scored + analysed {name}  ({w_val} val / {w_arr} arr)")

    ship = next(r for r in results if r["name"] == SHIPPED)

    L = []
    W = 78
    L.append("=" * W)
    L.append("AXIS WEIGHT ASSESSMENT - valuation vs AI-attributed ARR")
    L.append("=" * W)
    L.append("")
    L.append(f"{'split':>16}  {'rho vs 50/50':>12}  {'moved 5+':>9}  {'moved 10+':>10}  "
             f"{'top-11 kept':>12}  {'top-11 stable 10-40x':>22}")
    L.append("-" * W)

    for r in results:
        rho = spearman(ship["ranks"], r["ranks"])
        common = set(ship["ranks"]) & set(r["ranks"])
        dropped = sorted(set(ship["ranks"]) - set(r["ranks"]))
        entered = sorted(set(r["ranks"]) - set(ship["ranks"]))
        moved5 = sum(1 for n in common
                     if abs(ship["ranks"][n] - r["ranks"][n]) >= 5)
        moved10 = sum(1 for n in common
                      if abs(ship["ranks"][n] - r["ranks"][n]) >= 10)
        kept = len(set(ship["top11_always"]) & set(r["top11_always"]))
        stable = f"{r['top11_count']}/11 at every multiple"
        L.append(f"{r['w_val']:.2f} val / {r['w_arr']:.2f} arr  {rho:>12.3f}  "
                 f"{moved5:>9}  {moved10:>10}  {kept:>9}/11  {stable:>22}")
        r["rho"] = rho
        r["moved5"] = moved5
        r["moved10"] = moved10
        r["kept"] = kept
        r["dropped"] = dropped
        r["entered"] = entered

    prop = next(r for r in results if r["name"] == name_for(0.40, 0.60))

    # --- what actually moves ---------------------------------------------
    L.append("")
    L.append("=" * W)
    L.append("PROPOSED SPLIT (0.40 val / 0.60 arr) vs SHIPPED (0.50 / 0.50)")
    L.append("=" * W)
    movers = sorted(((n, rk) for n, rk in prop["ranks"].items()
                     if n in ship["ranks"]),
                    key=lambda kv: abs(ship["ranks"][kv[0]] - kv[1]),
                    reverse=True)
    L.append("")
    L.append(f"{'company':<46} {'50/50':>6} {'40/60':>6} {'move':>6}  note")
    L.append("-" * W)
    rows_by_name = {c["name"]: c for c in prop["rows"]}
    for n, rk in movers[:22]:
        c = rows_by_name[n]
        old = ship["ranks"][n]
        note = []
        if c.get("arr_usd_m") is None:
            note.append("no ARR")
        if c.get("valuation_basis") == "proxy":
            note.append("proxy")
        if c.get("valuation_basis") == "derived":
            note.append("derived")
        L.append(f"{n[:45]:<46} {old:>6} {rk:>6} {old - rk:>+6}  "
                  f"{', '.join(note)}")

    # --- pre-revenue labs -------------------------------------------------
    L.append("")
    L.append("=" * W)
    L.append("PRE-REVENUE LABS (no ARR axis) - the ones a revenue-weighted model hurts")
    L.append("=" * W)
    L.append(f"{'company':<46} {'50/50':>6} {'40/60':>6} {'move':>6}  score 50/50 -> 40/60")
    L.append("-" * W)
    prerev = [c for c in prop["rows"] if c.get("arr_usd_m") is None]
    prerev.sort(key=lambda c: ship["ranks"][c["name"]])
    for c in prerev:
        n = c["name"]
        if n not in prop["ranks"]:
            L.append(f"{n[:45]:<46} {ship['ranks'][n]:>6} {'OUT':>6} {'OUT':>6}  "
                     f"{ship['scores'][n]:>6.2f} -> out of the top 100")
            continue
        L.append(f"{n[:45]:<46} {ship['ranks'][n]:>6} {prop['ranks'][n]:>6} "
                 f"{ship['ranks'][n] - prop['ranks'][n]:>+6}  "
                 f"{ship['scores'][n]:>6.2f} -> {prop['scores'][n]:>6.2f}")

    # --- sensitivity to the scale choice ----------------------------------
    L.append("")
    L.append("=" * W)
    L.append("SCALE CHOICE UNDER EACH WEIGHT SPLIT (rank correlation vs that split's own variant A)")
    L.append("=" * W)
    L.append(f"{'split':>16}  {'B raw+minmax':>26}  {'C raw+zscore':>24}  {'D percentile':>24}")
    L.append("-" * W)
    for r in results:
        b = r["sens"].get("raw_minmax", {})
        c = r["sens"].get("raw_zscore", {})
        d = r["sens"].get("raw_percentile", {})
        L.append(f"{r['w_val']:.2f} val / {r['w_arr']:.2f} arr  "
                 f"rho {b.get('rho'):>6}  {b.get('below5'):>2}/100 below 5   "
                 f"rho {c.get('rho'):>6}  {c.get('below5'):>2}/100 below 5   "
                 f"rho {d.get('rho'):>6}  {d.get('below5'):>2}/100 below 5")

    # --- the top of the list under each split ------------------------------
    L.append("")
    L.append("=" * W)
    L.append("TOP 15 UNDER EACH SPLIT")
    L.append("=" * W)
    for r in results:
        L.append(f"  {r['w_val']:.2f} val / {r['w_arr']:.2f} arr")
        for c in sorted(r["rows"], key=lambda x: x["rank"])[:15]:
            L.append(f"    {c['rank']:>3}. {c['name'][:48]:<50} {c['score']:>6.2f}")

    out = ROOT / "data" / "weight_assessment.json"
    out.write_text(json.dumps({
        "note": "Generated by scripts/weight_assessment.py. Live outputs untouched.",
        "splits": [{"w_val": r["w_val"], "w_arr": r["w_arr"],
                    "spearman_vs_shipped": round(r["rho"], 4),
                    "rows_moved_5plus": r["moved5"],
                    "rows_moved_10plus": r["moved10"],
                    "top11_kept": r["kept"],
                    "top11_stable_across_multiples": r["top11_count"],
                    "dropped_from_top_100": r["dropped"],
                    "entered_top_100": r["entered"],
                    "sensitivity": r["sens"]} for r in results],
    }, indent=2) + "\n", encoding="utf-8")

    text = "\n".join(L)
    (ROOT / ".tmp_weight_report.txt").write_text(text, encoding="utf-8")
    print()
    print(text)
    print(f"\nwrote {out.relative_to(ROOT)} and .tmp_weight_report.txt")


if __name__ == "__main__":
    main()
