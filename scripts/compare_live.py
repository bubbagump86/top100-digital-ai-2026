"""
compare_live.py - side-by-side comparison of two scoring configurations.

Used to review a proposed model revision before it touches the live site.
It re-scores with the real engine (scripts/score.py) so there is no second
copy of the model to drift.

  python scripts/compare_live.py --baseline data/ranked.json \
                                 --variant  data/variants/live-v2/ranked.json \
                                 --out data/variants/live-v2/comparison.json

The churn simulation re-scores a set of plausible data events under both
configurations and reports how much each one disturbs the list.
"""

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCORE = ROOT / "scripts" / "score.py"
COMPANIES = ROOT / "data" / "companies.json"

# Model flags for each side, as passed to score.py.
LIVE_FLAGS = []
VARIANT_FLAGS = ["--anchored", "--fixed-multiple", "20", "--missing-rule", "hybrid"]


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--baseline", default=str(ROOT / "data" / "ranked.json"))
    p.add_argument("--variant", required=True)
    p.add_argument("--out", default=None)
    p.add_argument("--variant-flags", default=None,
                   help="space-separated score.py flags for the variant")
    p.add_argument("--baseline-flags", default="")
    p.add_argument("--keep-temp", action="store_true")
    return p.parse_args(argv)


def load(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def rel(path):
    """Path relative to the repo root, for display."""
    p = Path(path).resolve()
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def by_name(payload):
    return {c["name"]: c for c in payload["companies"]}


def spearman(a, b):
    ra = {n: i for i, (n, _) in enumerate(a)}
    rb = {n: i for i, (n, _) in enumerate(b)}
    n = len(ra)
    d2 = sum((ra[k] - rb[k]) ** 2 for k in ra)
    return 1 - 6 * d2 / (n * (n * n - 1))


def order(payload):
    return [(c["name"], c["score"]) for c in payload["companies"]]


# --------------------------------------------------------------------------
# churn scenarios: (label, mutator)
# --------------------------------------------------------------------------
def scenario_cases(raw):
    """Each case returns a mutated companies.json payload."""
    cases = []

    def clone():
        return json.loads(json.dumps(raw))

    def new_company(name, val, arr, cat="AI Data + AI Platform"):
        def f():
            d = clone()
            d["companies"].append({
                "name": name, "category": cat, "hq": "Testland, USA",
                "founded": 2026, "valuation_usd_b": val,
                "valuation_date": "2026", "valuation_source": "test",
                "arr_usd_m": arr, "arr_date": "2026", "arr_source": "test",
                "is_digital_only": True, "is_pure_play_ai": True,
                "valuation_basis": "actual",
                "summary": "Synthetic scenario company.",
            })
            return d
        return f

    def set_field(name, key, value):
        def f():
            d = clone()
            for c in d["companies"]:
                if c["name"] == name:
                    c[key] = value
            return d
        return f

    cases.append(("new company enters, $1M ARR (new floor)",
                  new_company("Newco Tiny", 0.5, 1.0)))
    cases.append(("new company enters, $5M ARR",
                  new_company("Newco Small", 1.0, 5.0)))
    cases.append(("new company enters, $300B ARR (new ceiling)",
                  new_company("Newco Big", 300.0, 300000.0)))
    cases.append(("Reworkd AI ARR slips $10M -> $5M (floor moves)",
                  set_field("Reworkd AI", "arr_usd_m", 5.0)))
    cases.append(("Anthropic ARR revised $100B -> $80B",
                  set_field("Anthropic", "arr_usd_m", 80000.0)))
    cases.append(("Anthropic ARR revised $100B -> $150B",
                  set_field("Anthropic", "arr_usd_m", 150000.0)))
    cases.append(("OpenAI ARR $50B -> $120B (overtakes Anthropic)",
                  set_field("OpenAI", "arr_usd_m", 120000.0)))
    return cases


def score_with(companies_payload, flags, tmpdir, tag):
    """Run score.py against a payload and return the resulting ranking."""
    src = Path(tmpdir) / f"companies_{tag}.json"
    src.write_text(json.dumps(companies_payload, indent=2, ensure_ascii=False),
                   encoding="utf-8")
    out = Path(tmpdir) / f"out_{tag}"
    cmd = [sys.executable, str(SCORE), "--companies", str(src),
           "--variant", str(out)] + flags
    res = subprocess.run(cmd, capture_output=True, text=True, cwd=str(ROOT))
    if res.returncode != 0:
        raise SystemExit(f"score.py failed for {tag}:\n{res.stdout}\n{res.stderr}")
    return load(out / "ranked.json")


def main(argv=None):
    args = parse_args(argv)
    base = load(args.baseline)
    var = load(args.variant)

    bflags = args.baseline_flags.split() if args.baseline_flags else []
    vflags = args.variant_flags.split() if args.variant_flags else VARIANT_FLAGS

    print("=" * 78)
    print("MODEL COMPARISON")
    print("=" * 78)
    print(f"  baseline : {rel(args.baseline)}")
    print(f"             {base.get('model_config', {})}")
    print(f"  variant  : {rel(args.variant)}")
    print(f"             {var.get('model_config', {})}")
    print()

    # ---------------- top 20 side by side -------------------------------
    print("-" * 78)
    print("TOP 20 - side by side")
    print("-" * 78)
    print(f"  {'#':>3}  {'baseline':<38} {'score':>7}  |  {'variant':<38} {'score':>7}")
    print("  " + "-" * 74)
    for i in range(20):
        b = base["companies"][i]
        v = var["companies"][i]
        mark = "" if b["name"] == v["name"] else "  *"
        print(f"  {i + 1:>3}  {b['name'][:37]:<38} {b['score']:>7.2f}  |  "
              f"{v['name'][:37]:<38} {v['score']:>7.2f}{mark}")
    print()

    # ---------------- rank diff -----------------------------------------
    bn, vn = by_name(base), by_name(var)
    moved = []
    for name, b in bn.items():
        v = vn.get(name)
        if v is None:
            continue
        moved.append((v["rank"] - b["rank"], name, b["rank"], v["rank"],
                      b["score"], v["score"]))
    moved.sort()
    up = [m for m in moved if m[0] < 0]
    down = [m for m in moved if m[0] > 0]
    same = [m for m in moved if m[0] == 0]
    print("-" * 78)
    print("RANK MOVEMENT")
    print("-" * 78)
    print(f"  unchanged : {len(same):>3} / {len(moved)}")
    print(f"  up        : {len(up):>3}")
    print(f"  down      : {len(down):>3}")
    print(f"  Spearman rho baseline vs variant: {spearman(order(base), order(var)):+.4f}")
    print()
    print("  biggest movers:")
    for d, name, r0, r1, s0, s1 in sorted(moved, key=lambda x: -abs(x[0]))[:12]:
        print(f"    {'UP  ' if d < 0 else 'DOWN'} {name[:40]:<42} "
              f"#{r0:<4} -> #{r1:<4} ({d:+d})   {s0:>6.2f} -> {s1:>6.2f}")
    print()

    # ---------------- distribution --------------------------------------
    print("-" * 78)
    print("DISTRIBUTION OF THE 100")
    print("-" * 78)
    for label, p in (("baseline", base), ("variant", var)):
        sc = [c["score"] for c in p["companies"]]
        s = sorted(sc)
        med = (s[49] + s[50]) / 2
        print(f"  {label:<9} rows<5pts {sum(1 for x in sc if x < 5):>3}/100   "
              f"median {med:>6.2f}   p10 {s[9]:.2f}  p90 {s[89]:.2f}  "
              f"max {s[-1]:.2f}")
    print()

    # ---------------- churn simulation ---------------------------------
    print("-" * 78)
    print("CHURN SIMULATION - how much does each data event disturb the list?")
    print("-" * 78)
    raw = load(COMPANIES)
    churn = []
    with tempfile.TemporaryDirectory() as tmp:
        for i, (label, mutator) in enumerate(scenario_cases(raw)):
            payload = mutator()
            b1 = score_with(payload, bflags, tmp, f"b{i}")
            v1 = score_with(payload, vflags, tmp, f"v{i}")
            bm = by_name(b1)
            vm = by_name(v1)
            b1o = {c["name"]: c["rank"] for c in b1["companies"]}
            v1o = {c["name"]: c["rank"] for c in v1["companies"]}

            def churn_of(old_payload, new_payload):
                """Median score shift and rank churn: same model, before vs after."""
                old_r = {c["name"]: c["rank"] for c in old_payload["companies"]}
                new_r = {c["name"]: c["rank"] for c in new_payload["companies"]}
                new_by = {c["name"]: c for c in new_payload["companies"]}
                shifts, churned = [], 0
                for c in old_payload["companies"]:
                    name = c["name"]
                    d = new_by.get(name)
                    if d is None:
                        continue
                    shifts.append(d["score"] - c["score"])
                    if name in new_r and abs(new_r[name] - old_r[name]) >= 3:
                        churned += 1
                shifts.sort()
                return shifts[len(shifts) // 2], churned

            bmed, bch = churn_of(base, b1)
            vmed, vch = churn_of(var, v1)
            print(f"  {label}")
            print(f"      baseline: median score {bmed:+6.2f}   "
                  f"{bch:>3} companies change rank by >=3")
            print(f"      variant : median score {vmed:+6.2f}   "
                  f"{vch:>3} companies change rank by >=3")
            churn.append({
                "event": label,
                "baseline_median_score_shift": round(bmed, 2),
                "baseline_rank_churn_ge3": bch,
                "variant_median_score_shift": round(vmed, 2),
                "variant_rank_churn_ge3": vch,
                "baseline_leader": b1["companies"][0]["name"],
                "variant_leader": v1["companies"][0]["name"],
            })
    print()

    # ---------------- write ---------------------------------------------
    out = {
        "baseline": {
            "path": rel(args.baseline),
            "model_config": base.get("model_config", {}),
            "axes": base.get("axes", {}),
            "peer_multiple": base["peer_multiple"]["median_ev_revenue"],
        },
        "variant": {
            "path": rel(args.variant),
            "model_config": var.get("model_config", {}),
            "axes": var.get("axes", {}),
            "peer_multiple": var["peer_multiple"]["median_ev_revenue"],
        },
        "summary": {
            "spearman": round(spearman(order(base), order(var)), 4),
            "unchanged": len(same),
            "up": len(up),
            "down": len(down),
            "top20_moved": sum(
                1 for i in range(20)
                if base["companies"][i]["name"] != var["companies"][i]["name"]),
        },
        "rank_movement": [
            {"name": n, "from": r0, "to": r1, "delta": d,
             "baseline_score": s0, "variant_score": s1}
            for d, n, r0, r1, s0, s1 in moved
        ],
        "churn": churn,
    }
    outp = Path(args.out) if args.out else Path(args.variant).parent / "comparison.json"
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(out, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"  wrote {rel(outp)}")


if __name__ == "__main__":
    main()
