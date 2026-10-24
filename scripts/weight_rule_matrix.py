"""
weight_rule_matrix.py - do the axis weights and the missing-ARR rule interact?

Yes, and the interaction is the whole story. The published "zero" rule scores
a row with no ARR as w_val * z_val, so a row with no AI revenue disclosure
(proxy basis: Palantir, ByteDance, Samsara, Schrodinger) is already getting
only the valuation axis. Raising the ARR weight does not just reward rows
that HAVE revenue - it shrinks the axis that the rows WITHOUT disclosed
revenue are scored on.

This script runs the matrix so the interaction is measured rather than
argued:

    weight split      x      missing-ARR rule      x      rank outcome

Live outputs are untouched - everything goes to data/variants/<name>/.

Run:
    python scripts/weight_rule_matrix.py
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ROOT / "data" / "variants"

CASES = [
    (0.50, 0.50, "zero",   "w050zero",  "SHIPPED"),
    (0.40, 0.60, "zero",   "w040zero",  "proposed split, current rule"),
    (0.40, 0.60, "hybrid", "w040hyb",   "proposed split + Option B"),
    (0.40, 0.60, "alone",  "w040alone", "proposed split + axis dropped"),
    (0.50, 0.50, "hybrid", "w050hyb",   "current split + Option B"),
    (0.50, 0.50, "alone",  "w050alone", "current split + axis dropped"),
]

WATCH = [
    "Palantir Technologies",
    "ByteDance (AI: Doubao + Seed + Volcano Engine)",
    "Samsara", "Schrodinger", "Cohesity", "Talkdesk",
    "Midjourney", "Suno",
    "Safe Superintelligence (SSI)", "Thinking Machines Lab", "Moonshot AI",
    "Anthropic", "OpenAI",
]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, cwd=str(ROOT))
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(str(c) for c in cmd)}\n"
                         f"{r.stdout.decode('utf-8', 'replace')[-1500:]}\n"
                         f"{r.stderr.decode('utf-8', 'replace')[-1500:]}")


def score_variant(w_val, w_arr, rule, name):
    run([sys.executable, str(ROOT / "scripts" / "score.py"),
         "--variant", name, "--weight-val", str(w_val),
         "--weight-arr", str(w_arr), "--missing-rule", rule])
    return json.loads((VARIANTS / name / "ranked.json").read_text(encoding="utf-8"))


def main():
    VARIANTS.mkdir(parents=True, exist_ok=True)
    L = []
    W = 116
    L.append("=" * W)
    L.append("WEIGHT x MISSING-ARR-RULE MATRIX")
    L.append("=" * W)
    L.append("")

    cases = []
    for w_val, w_arr, rule, name, label in CASES:
        ranked = score_variant(w_val, w_arr, rule, name)
        cases.append({"label": label, "name": name, "w_val": w_val,
                      "w_arr": w_arr, "rule": rule,
                      "rows": {c["name"]: c for c in ranked["companies"]},
                      "top12": [c["name"] for c in
                                sorted(ranked["companies"],
                                       key=lambda x: x["rank"])[:12]]})
        print(f"  ran {name}")

    ship = cases[0]
    L.append(f"{'case':<34}{'w_val/w_arr':>13}{'rule':>8}   "
             f"{'top-12 kept vs shipped':>24}")
    L.append("-" * W)
    for c in cases:
        kept = len(set(c["top12"]) & set(ship["top12"]))
        L.append(f"{c['label']:<34}{c['w_val']:.2f}/{c['w_arr']:.2f}{c['rule']:>8}   "
                 f"{kept:>21}/12")
    L.append("")

    L.append("=" * W)
    L.append("RANK OF THE ROWS THAT CARRY THE WEIGHT CHANGE")
    L.append("=" * W)
    hdr = f"{'company':<46}" + "".join(f"{c['label'].split(',')[0][:16]:>17}"
                                       for c in cases)
    L.append(hdr)
    L.append("-" * W)
    for n in WATCH:
        line = f"{n[:45]:<46}"
        for c in cases:
            row = c["rows"].get(n)
            line += f"{(('#' + str(row['rank'])) if row else 'OUT'):>17}"
        L.append(line)
    L.append("-" * W)
    L.append("")

    L.append("=" * W)
    L.append("SCORE OF A ROW WITH NO DISCLOSED AI REVENUE (proxy basis)")
    L.append("=" * W)
    L.append("Under the 'zero' rule these rows are scored w_val * z_val only, so")
    L.append("raising the ARR weight shrinks the axis they are scored on.")
    L.append("")
    L.append(f"{'company':<46}" + "".join(f"{c['label'].split(',')[0][:16]:>17}"
                                          for c in cases))
    L.append("-" * W)
    for n in WATCH:
        row0 = ship["rows"].get(n)
        if not row0 or row0["valuation_basis"] != "proxy":
            continue
        line = f"{n[:45]:<46}"
        for c in cases:
            row = c["rows"].get(n)
            cell = f"{row['score']:.2f}" if row else "OUT"
            line += f"{cell:>17}"
        L.append(line)
    L.append("-" * W)

    (ROOT / ".tmp_matrix.txt").write_text("\n".join(L), encoding="utf-8")
    print()
    print("\n".join(L))


if __name__ == "__main__":
    main()
