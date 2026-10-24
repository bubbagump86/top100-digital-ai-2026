"""
compare_levers.py - if you believe valuation is over-weighted, which lever
actually moves the list most?

Two candidate levers:

  A. re-weight the axes (0.50/0.50 -> 0.40/0.60 ARR) - a global change
  B. make the proxy tier policy-compliant - two rows carry their TOTAL
     company ARR on the AI-ARR axis although the model says a proxy row
     scores 0 on that axis (Cohesity, Talkdesk)

Lever B is not a weight change; it is a correction to two data rows. This
script measures both so their magnitudes can be compared directly.

Run:
    python scripts/compare_levers.py
"""

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
VARIANTS = ROOT / "data" / "variants"
COMPANIES = ROOT / "data" / "companies.json"

# Proxy rows whose arr_usd_m is their TOTAL company ARR, not AI-attributed.
NON_COMPLIANT = ["Cohesity", "Talkdesk"]


def run(cmd):
    r = subprocess.run(cmd, capture_output=True, cwd=str(ROOT))
    if r.returncode != 0:
        raise SystemExit(f"FAILED: {' '.join(str(c) for c in cmd)}\n"
                         f"{r.stdout.decode('utf-8', 'replace')[-1200:]}\n"
                         f"{r.stderr.decode('utf-8', 'replace')[-1200:]}")


def score(name, companies=None, weight_val=None, weight_arr=None):
    cmd = [sys.executable, str(ROOT / "scripts" / "score.py"), "--variant", name]
    if companies:
        cmd += ["--companies", str(companies)]
    if weight_val is not None:
        cmd += ["--weight-val", str(weight_val), "--weight-arr", str(weight_arr)]
    run(cmd)
    return json.loads((VARIANTS / name / "ranked.json").read_text(encoding="utf-8"))


def main():
    VARIANTS.mkdir(parents=True, exist_ok=True)
    ship = score("lever_ship")
    a = score("lever_reweight", weight_val=0.40, weight_arr=0.60)

    # Lever B: the two non-compliant proxy rows lose their total-company ARR.
    raw = json.loads(COMPANIES.read_text(encoding="utf-8"))
    for c in raw["companies"]:
        if c["name"] in NON_COMPLIANT:
            c["arr_usd_m"] = None
            c["arr_source"] = ("Policy-compliant proxy: no AI-attributed revenue "
                               "disclosed, so the ARR axis reads 0 under the "
                               "missing-ARR rule.")
    tmp = ROOT / "data" / ".lever_b_companies.json"
    tmp.write_text(json.dumps(raw, indent=2, ensure_ascii=False), encoding="utf-8")
    b = score("lever_proxyfix", companies=tmp)
    tmp.unlink()

    rs = {c["name"]: c for c in ship["companies"]}
    ra = {c["name"]: c for c in a["companies"]}
    rb = {c["name"]: c for c in b["companies"]}

    L = []
    L.append("=" * 104)
    L.append("TWO LEVERS ON 'VALUATION HAS TOO MUCH WEIGHT'")
    L.append("=" * 104)
    L.append("")
    L.append(f"A. Re-weight the axes to 0.40 val / 0.60 arr   "
             f"(every row's score changes)")
    L.append(f"B. Make the proxy tier policy-compliant       "
             f"(two rows: {', '.join(NON_COMPLIANT)})")
    L.append("")

    def movers(res, label):
        rows = []
        for n in rs:
            if n in res:
                rows.append((n, rs[n]["rank"], res[n]["rank"],
                             rs[n]["score"], res[n]["score"]))
        rows.sort(key=lambda x: -abs(x[1] - x[2]))
        L.append(f"{label}")
        L.append(f"  {'company':<44}{'shipped':>9}{'changed':>9}{'move':>7}")
        L.append("  " + "-" * 68)
        for n, o, nn, os_, ns_ in rows[:8]:
            L.append(f"  {n[:43]:<44}{o:>9}{nn:>9}{o - nn:>+7}")
        L.append(f"  rows moving 3+ places: "
                 f"{sum(1 for n in rs if n in res and abs(rs[n]['rank'] - res[n]['rank']) >= 3)}")
        L.append("")

    movers(ra, "A. re-weighted (0.40/0.60):")
    movers(rb, "B. proxy tier made policy-compliant:")

    L.append("=" * 104)
    L.append("THE TWO NON-COMPLIANT ROWS, UNDER EACH LEVER")
    L.append("=" * 104)
    L.append(f"{'company':<30}{'shipped':>22}{'A: re-weight':>22}{'B: proxy fix':>22}")
    L.append("-" * 104)
    for n in NON_COMPLIANT:
        def cell(res):
            c = res.get(n)
            return f"#{c['rank']} ({c['score']:.2f})" if c else "out"
        L.append(f"{n:<30}{cell(rs):>22}{cell(ra):>22}{cell(rb):>22}")
    L.append("-" * 104)
    L.append("")
    L.append("And what lever B does to the rows that actually depend on the proxy tier:")
    for n in ["Samsara", "Palantir Technologies",
              "ByteDance (AI: Doubao + Seed + Volcano Engine)",
              "Schrodinger"]:
        c = rs.get(n)
        if not c:
            continue
        L.append(f"  {n[:52]:<54} shipped #{c['rank']:<4} -> "
                 f"A #{(ra.get(n) or {}).get('rank', 'OUT'):<5} "
                 f"B #{(rb.get(n) or {}).get('rank', 'OUT')}")

    (ROOT / ".tmp_levers.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
