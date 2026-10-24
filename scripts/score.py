"""
scoring/score.py  (v2 — three-basis model, October 2026)
=======================================================
Computes the Top 100 Pure-Play Digital AI Companies ranking.

THE PROBLEM
-----------
Valuation and ARR each span 5+ orders of magnitude ($10M - $100B ARR).
A direct linear sum would let one mega-company crush everything else.
So both axes are log-transformed and min-max rescaled.

THE BIG-TECH PROBLEM (and how we solve it)
-------------------------------------------
Alphabet, Meta, Microsoft, Amazon, Alibaba, Baidu and Tencent have real,
substantial, *disclosed* AI businesses - but they are not AI companies, and
their market caps are overwhelmingly priced on their non-AI businesses
(search, ads, e-commerce, gaming, Office). Dropping them would understate
the most important AI businesses on earth; using their full market caps
would let them dominate a ranking about AI on the strength of ad revenue.

We solve it with a THREE-BASIS model, applied consistently:

  1. pure_play  - the company IS an AI business. Its market/transaction
                  valuation is already an AI valuation. Used as-is.
                  These rows also form the PEER POOL for the multiple.

  2. derived    - the company is diversified but discloses AI-attributed
                  revenue. We value that revenue at the pure-play median
                  EV/Revenue multiple:

                      implied AI valuation = AI ARR x peer median multiple

                  This answers: "what would this AI business be worth if
                  it were a standalone AI company at peer multiples?"

                  HARD CONSTRAINT: a derived valuation can never exceed the
                  company's own actual valuation (market cap). A part cannot
                  be worth more than the whole. If the peer multiple implies
                  more than the market values the entire company, the market
                  cap binds and the valuation axis is capped there. The
                  uncapped figure is kept and published alongside.

  3. proxy      - no AI-revenue disclosure at all. No AI valuation can be
                  derived. Full market cap is used as a flagged proxy and
                  the ARR axis is scored at 0. Weakest evidence in the list.

The peer multiple is computed from the pure-play pool only (so the
imputation never feeds back into its own input), then applied once.

COMPOSITE
----------
    S = 100 * (0.5 * z_log(valuation) + 0.5 * z_log(ARR))

MODEL OPTIONS (added for the live-list revision; defaults = current behaviour)
---------------------------------------------------------------------------
  --anchored            Use FIXED axis bounds instead of the sample's own
                        min/max. A live list that recomputes its bounds on
                        every update re-bases everyone's score when a new
                        record-holder appears, which shows up as rank churn
                        rather than as any visible score change.
                        Bounds: --anchor-val / --anchor-arr.

MODEL POLICY
-------------
The default model is read from data/model_config.json - a version-controlled
policy file, not code. It pins:

  axis bounds      fixed, not derived from the sample. A live list that
                   recomputes its bounds on every update re-bases everyone's
                   score when a new record-holder appears, which shows up as
                   rank churn rather than as any visible score change.

  peer multiple    pinned at the pure-play median as measured on the
                   2026-10 edition. The median is itself a sample-dependent
                   number: adding one company at 90.9x moves it from 20.00x
                   to 20.42x and shifts every derived megacap row.

  missing-ARR rule a row with no ARR scores 0 on the ARR axis and KEEPS its
                   50% weight (composite = 0.5 * z_val). 'missing' is not
                   'zero revenue', but the alternative rules were tested and
                   rejected for now - see data/model_config.json.

  axis weights    the composite's split between the two axes. Held in
                   data/model_config.json as policy, not as a constant here,
                   so the most contestable number in the model is version
                   controlled in one place rather than duplicated across
                   scripts.

Overrides for review work (defaults come from the policy file):

  --axis {anchored,sample}
  --anchor-val MIN MAX       fixed valuation bounds in $B
  --anchor-arr MIN MAX       fixed ARR bounds in $M
  --weight-val W             weight on the valuation axis (must sum to 1
  --weight-arr W             with the ARR axis)
  --peer-multiple N          pin the peer multiple; 0 = recompute the median
  --missing-rule {zero,alone,hybrid}
                          zero   - ARR axis reads 0 and KEEPS its 50% weight
                                   (composite = 0.5 * z_val)   [ADOPTED]
                          alone  - the ARR axis is dropped and the remaining
                                   axis carries full weight (composite = z_val)
                          hybrid - 'alone' when the valuation IS an AI
                                   valuation (pure-play), 'zero' when the
                                   valuation is a whole-company market cap
                                   (proxy), because a proxy's number already
                                   contains all of its non-AI businesses.

  --variant NAME        Write outputs to data/variants/NAME/ and leave the
                        live data/ranked.json, data/ranked.csv and the site
                        ranked.json untouched. Use for dry runs.
  --companies PATH      Score a different companies.json (default:
                        data/companies.json)

Output:
  - data/ranked.json, data/ranked.csv, ranked.json  (default run)
  - data/variants/NAME/ranked.json, .../ranked.csv  (--variant)

Run:
  python scripts/score.py
  python scripts/score.py --variant review --axis sample --peer-multiple 0
"""

import argparse
import csv
import json
import math
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "companies.json"
POLICY = ROOT / "data" / "model_config.json"
OUT_JSON = ROOT / "data" / "ranked.json"
OUT_CSV = ROOT / "data" / "ranked.csv"
OUT_PUBLIC_RANKED = ROOT / "ranked.json"

# The composite's axis weights live in data/model_config.json (policy), not
# here, so that the most contestable number in the model is version-controlled
# in one place instead of being a constant duplicated across three scripts.
DEFAULT_W_VAL = 0.5
DEFAULT_W_ARR = 0.5


def load_policy():
    """Model policy: version-controlled, reviewed quarterly."""
    try:
        return json.loads(POLICY.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise SystemExit(f"Model policy not found: {POLICY}")


def policy_weights(policy):
    """Read the axis weights out of the policy file."""
    w = (policy or {}).get("weights") or {}
    return (float(w.get("valuation", DEFAULT_W_VAL)),
            float(w.get("arr", DEFAULT_W_ARR)))


def rel(p):
    """Path relative to the repo root when possible, else absolute."""
    p = Path(p).resolve()
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def parse_args(argv=None):
    pol = load_policy()
    axis_pol = pol.get("axis", {})
    p = argparse.ArgumentParser(
        description="Score the Top 100 Digital AI Companies.")
    p.add_argument("--axis", choices=["anchored", "sample"],
                   default=axis_pol.get("bounds_source", "anchored"),
                   help="axis bounds source (default: from model_config.json)")
    p.add_argument("--anchor-val", type=float, nargs=2, metavar=("MIN", "MAX"),
                   default=axis_pol.get("valuation_usd_b", [0.1, 1000.0]),
                   help="fixed valuation bounds in $B")
    p.add_argument("--anchor-arr", type=float, nargs=2, metavar=("MIN", "MAX"),
                   default=axis_pol.get("arr_usd_m", [10.0, 100000.0]),
                   help="fixed ARR bounds in $M")
    p.add_argument("--peer-multiple", type=float,
                   default=pol.get("peer_multiple", 20.0),
                   help="pin the peer EV/Revenue multiple; 0 = recompute the "
                        "pure-play median each run")
    p.add_argument("--missing-rule", choices=["zero", "alone", "hybrid"],
                   default=pol.get("missing_arr_rule", "zero"),
                   help="how a row with no ARR is scored")
    pol_w_val, pol_w_arr = policy_weights(pol)
    p.add_argument("--weight-val", type=float, default=pol_w_val,
                   help="weight on the valuation axis (default: from "
                        "data/model_config.json)")
    p.add_argument("--weight-arr", type=float, default=pol_w_arr,
                   help="weight on the ARR axis (default: from "
                        "data/model_config.json)")
    p.add_argument("--axis-floor-clamp", dest="axis_floor_clamp",
                   action="store_true", default=bool(pol.get("axis_floor_clamp", True)),
                   help="a value below the axis floor reads 0, like a missing "
                        "value (default: from data/model_config.json)")
    p.add_argument("--no-axis-floor-clamp", dest="axis_floor_clamp",
                   action="store_false",
                   help="disable the axis floor clamp (review use only)")
    p.add_argument("--variant", default=None, metavar="NAME",
                   help="write to data/variants/NAME/ and leave live outputs "
                        "untouched")
    p.add_argument("--companies", default=None, metavar="PATH",
                   help="input companies.json (default: data/companies.json)")
    return p.parse_args(argv)


def is_skipped(company: dict) -> bool:
    """Skip placeholders, duplicates, entities rolled up into another row,
    and rows with no usable data at all."""
    cat = (company.get("category") or "").lower().strip()
    name = (company.get("name") or "").lower().strip()
    if cat in {"skip", "duplicate"}:
        return True
    if "duplicate" in cat or "duplicate" in name:
        return True
    if "now part of" in name or "rolls into" in name:
        return True
    if company.get("duplicate_in_ranking_with"):
        return True
    val = company.get("valuation_usd_b")
    arr = company.get("arr_usd_m")
    if val is None and arr is None:
        return True
    return False


def log_safe(x):
    return math.log10(x) if x and x > 0 else None


def ev_revenue(val_usd_b, arr_usd_m):
    """EV/Revenue multiple, both sides in the same unit."""
    if not val_usd_b or not arr_usd_m:
        return None
    return (val_usd_b * 1000.0) / arr_usd_m


def main(argv=None) -> None:
    args = parse_args(argv)
    policy = load_policy()

    # The two axis weights must sum to 1 - the composite is a weighted mean of
    # two [0,1] axes, so anything else is not a score on the same scale.
    w_val, w_arr = float(args.weight_val), float(args.weight_arr)
    if abs((w_val + w_arr) - 1.0) > 1e-9:
        raise SystemExit(
            f"Axis weights must sum to 1.0 (got {w_val} + {w_arr} = "
            f"{w_val + w_arr}).")
    if w_val < 0 or w_arr < 0:
        raise SystemExit("Axis weights must not be negative.")

    data_path = Path(args.companies) if args.companies else DATA
    with data_path.open(encoding="utf-8") as fh:
        raw = json.load(fh)

    companies = [c for c in raw["companies"] if not is_skipped(c)]

    # ------------------------------------------------------------------
    # PASS 1 - derive the peer EV/Revenue multiple from the pure-play pool
    # ------------------------------------------------------------------
    peer_pool = []
    for c in companies:
        if not c.get("is_pure_play_ai", True):
            continue
        if c.get("valuation_basis", "actual") != "actual":
            continue
        m = ev_revenue(c.get("valuation_usd_b"), c.get("arr_usd_m"))
        if m:
            peer_pool.append((c["name"], m))

    multiples = sorted(m for _, m in peer_pool)
    if not multiples:
        raise SystemExit("No pure-play peers with both valuation and ARR - "
                         "cannot derive the peer multiple.")

    computed_median = statistics.median(multiples)
    if args.peer_multiple:
        peer_multiple = args.peer_multiple
    else:
        peer_multiple = computed_median
    p25 = multiples[max(0, int(len(multiples) * 0.25) - 1)]
    p75 = multiples[min(len(multiples) - 1, int(len(multiples) * 0.75))]

    # ------------------------------------------------------------------
    # PASS 2 - resolve the valuation axis
    # ------------------------------------------------------------------
    resolved = []
    for c in companies:
        basis = c.get("valuation_basis", "actual")
        val_b = c.get("valuation_usd_b")
        arr_m = c.get("arr_usd_m")

        derived_val = None
        uncapped_val = None
        cap_applied = False
        mcap = c.get("market_cap_usd_b")

        if basis == "derived":
            if arr_m:
                uncapped_val = (arr_m * peer_multiple) / 1000.0
                derived_val = round(uncapped_val, 2)
                # HARD CONSTRAINT
                # -----------------
                # A derived AI valuation can never be worth more than the
                # company it belongs to. If AI ARR x peer multiple implies
                # more than the whole company is actually valued at, the
                # market cap binds and the valuation axis is capped there.
                # Without this, a diversified row could claim an implied AI
                # valuation larger than its entire market cap - which is not
                # a valuation of anything.
                if mcap is not None and derived_val > mcap:
                    derived_val = round(mcap, 2)
                    cap_applied = True
                val_b = derived_val
            else:
                # Nothing to derive from -> cannot score, treat as proxy.
                basis = "proxy"
                if val_b is None:
                    val_b = mcap
        elif basis == "proxy":
            # Keep the market cap, but the ARR axis scores 0.
            if val_b is None:
                val_b = mcap

        # --- coherence cross-check -------------------------------------
        # For a derived row, what multiple is the market itself paying per
        # dollar of the company's AI revenue? If the derivation overran the
        # whole market cap it was already capped above, so the check here is
        # to publish what the market thinks and to flag the row as
        # indicative - never to publish a valuation that cannot exist.
        market_implied_multiple = None
        derived_pct_of_market_cap = None
        coherence_flag = None
        coherence_ok = None
        if basis == "derived" and arr_m and mcap:
            market_implied_multiple = round((mcap * 1000.0) / arr_m, 1)
            derived_pct_of_market_cap = round((derived_val / mcap) * 100, 1)
            coherence_ok = derived_val <= mcap
            if cap_applied:
                coherence_flag = (
                    "CAPPED AT MARKET CAP: the uncapped derivation "
                    f"(${uncapped_val:,.1f}B) exceeded the company's entire "
                    f"market cap (${mcap:,.1f}B), so the valuation axis is "
                    "capped at the market cap. The market prices this AI "
                    f"revenue at only {market_implied_multiple}x, against a "
                    f"peer median of {peer_multiple:.0f}x - it treats the "
                    "segment as re-segmented legacy revenue rather than a new "
                    "business. Treat this row's rank as indicative only."
                )
            elif derived_pct_of_market_cap >= 99.0:
                coherence_flag = (
                    "AT MARKET CAP: the derived AI valuation equals the "
                    "company's entire market cap. There is no headroom left "
                    "under the constraint that a derived valuation cannot "
                    "exceed the company's actual valuation."
                )
        elif basis == "proxy" and mcap:
            market_implied_multiple = None
            derived_pct_of_market_cap = None
            coherence_flag = (
                "Market-cap proxy: no AI revenue disclosed, so the valuation "
                "axis includes the whole company and the ARR axis is 0."
            )

        resolved.append({
            "name": c["name"],
            "category": c.get("category"),
            "hq": c.get("hq"),
            "founded": c.get("founded"),
            "summary": c.get("summary"),
            "valuation_usd_b": val_b,
            "valuation_date": c.get("valuation_date"),
            "valuation_source": c.get("valuation_source"),
            "arr_usd_m": arr_m,
            "arr_date": c.get("arr_date"),
            "arr_source": c.get("arr_source"),
            "arr_total_usd_m": c.get("arr_total_usd_m"),
            "arr_attribution_note": c.get("arr_attribution_note"),
            "valuation_basis": basis,
            "is_pure_play_ai": c.get("is_pure_play_ai", True),
            "market_cap_usd_b": mcap,
            "market_cap_date": c.get("market_cap_date"),
            "market_implied_multiple": market_implied_multiple,
            "derived_pct_of_market_cap": derived_pct_of_market_cap,
            "coherence_flag": coherence_flag,
            "coherence_ok": coherence_ok,
            "valuation_capped": cap_applied,
            "uncapped_derived_usd_b": round(uncapped_val, 2) if uncapped_val else None,
            "corporate_status": c.get("corporate_status"),
            "derived_valuation_usd_b": derived_val,
        })

    # ------------------------------------------------------------------
    # PASS 3 - normalise, score, rank
    # ------------------------------------------------------------------
    val_logs = [log_safe(r["valuation_usd_b"]) for r in resolved
                if r["valuation_usd_b"]]
    arr_logs = [log_safe(r["arr_usd_m"]) for r in resolved if r["arr_usd_m"]]
    val_logs = [v for v in val_logs if v is not None]
    arr_logs = [a for a in arr_logs if a is not None]

    if args.axis == "anchored":
        # FIXED bounds: published policy, not the sample's own extremes.
        # Keeps a data update from re-basing every other company's score.
        val_min = math.log10(args.anchor_val[0])
        val_max = math.log10(args.anchor_val[1])
        arr_min = math.log10(args.anchor_arr[0])
        arr_max = math.log10(args.anchor_arr[1])
        bounds_source = "anchored"
    else:
        val_min, val_max = min(val_logs), max(val_logs)
        arr_min, arr_max = min(arr_logs), max(arr_logs)
        bounds_source = "sample"
    val_span = (val_max - val_min) or 1
    arr_span = (arr_max - arr_min) or 1

    for r in resolved:
        z_v = z_a = None
        if r["valuation_usd_b"]:
            z_v = (math.log10(r["valuation_usd_b"]) - val_min) / val_span
        if r["arr_usd_m"]:
            z_a = (math.log10(r["arr_usd_m"]) - arr_min) / arr_span

        # --- axis floor ---------------------------------------------------
        # A value BELOW the axis floor reads 0, exactly like a missing value.
        # Without this, a company with a little revenue scores BELOW a
        # company with none, because "no revenue" is scored 0 and a
        # sub-floor revenue figure scores negative. The top end is NOT
        # clamped: a score above 100 is the signal that an anchor is stale.
        if args.axis_floor_clamp:
            if z_v is not None and z_v < 0:
                z_v = 0.0
            if z_a is not None and z_a < 0:
                z_a = 0.0

        # --- how a missing axis is scored -------------------------------
        # 'zero'   the axis reads 0 and KEEPS its weight  -> w_other * z_other
        # 'alone'  the axis is dropped, the other carries full weight -> z_other
        # 'hybrid' 'alone' when the valuation IS an AI valuation (pure-play),
        #          'zero' when it is a whole-company market cap (proxy)
        if z_v is None and z_a is None:
            score, missing = 0.0, "both"
        elif z_v is None:
            score, missing = 100.0 * (w_arr * z_a), "valuation"
        elif z_a is None:
            if args.missing_rule == "alone":
                score, missing = 100.0 * z_v, "arr"
            elif args.missing_rule == "hybrid":
                if r["valuation_basis"] == "actual":
                    score, missing = 100.0 * z_v, "arr"
                else:
                    score, missing = 100.0 * (w_val * z_v), "arr"
            else:
                score, missing = 100.0 * (w_val * z_v), "arr"
        else:
            score, missing = 100.0 * (w_val * z_v + w_arr * z_a), ""

        r["z_val"] = round(z_v, 4) if z_v is not None else None
        r["z_arr"] = round(z_a, 4) if z_a is not None else None
        r["missing_axes"] = missing
        r["score"] = round(score, 2)
        r["missing_rule_applied"] = (
            "alone" if (z_a is None and r["valuation_basis"] == "actual"
                        and args.missing_rule in ("alone", "hybrid"))
            else "zero" if z_a is None
            else ""
        )

    resolved.sort(key=lambda r: r["score"], reverse=True)
    top = resolved[:100]
    for i, r in enumerate(top, start=1):
        r["rank"] = i

    payload = {
        "metadata": raw["metadata"],
        "counts": {
            "input": len(raw["companies"]),
            "after_filter": len(companies),
            "ranked": len(top),
            "pure_play": sum(1 for r in top if r["valuation_basis"] == "actual"),
            "derived": sum(1 for r in top if r["valuation_basis"] == "derived"),
            "proxy": sum(1 for r in top if r["valuation_basis"] == "proxy"),
        },
        "axes": {
            "valuation_usd_b": {"log_min": val_min, "log_max": val_max},
            "arr_usd_m": {"log_min": arr_min, "log_max": arr_max},
            "bounds_source": bounds_source,
        },
        "weights": {"valuation": w_val, "arr": w_arr},
        "model_config": {
            "policy_version": policy.get("policy_version"),
            "reviewed": policy.get("reviewed"),
            "axis": args.axis,
            "anchor_val_usd_b": list(args.anchor_val),
            "anchor_arr_usd_m": list(args.anchor_arr),
            "peer_multiple": peer_multiple,
            "peer_multiple_pinned": bool(args.peer_multiple),
            "computed_peer_median": round(computed_median, 2),
            "missing_rule": args.missing_rule,
            "variant": args.variant,
        },
        "valuation_cap": {
            "rule": ("A derived AI valuation may never exceed the company's own "
                     "actual valuation (market cap). If AI ARR x peer multiple "
                     "implies more than the whole company is worth, the market "
                     "cap binds and the valuation axis is capped there."),
            "peer_multiple_used": round(peer_multiple, 2),
            "rows_capped": [
                {
                    "name": r["name"],
                    "uncapped_usd_b": r["uncapped_derived_usd_b"],
                    "capped_to_usd_b": r["valuation_usd_b"],
                    "market_cap_usd_b": r["market_cap_usd_b"],
                    "market_implied_multiple": r["market_implied_multiple"],
                }
                for r in top if r.get("valuation_capped")
            ],
            "rows_at_cap": [
                {
                    "name": r["name"],
                    "valuation_usd_b": r["valuation_usd_b"],
                    "market_cap_usd_b": r["market_cap_usd_b"],
                    "pct": r["derived_pct_of_market_cap"],
                }
                for r in top
                if r.get("derived_pct_of_market_cap") is not None
                and r["derived_pct_of_market_cap"] >= 99.0
                and not r.get("valuation_capped")
            ],
        },
        "peer_multiple": {
            "median_ev_revenue": round(peer_multiple, 2),
            "p25": round(p25, 2),
            "p75": round(p75, 2),
            "min": round(multiples[0], 2),
            "max": round(multiples[-1], 2),
            "mean": round(statistics.mean(multiples), 2),
            "pool_size": len(multiples),
            "pool": [{"name": n, "multiple": round(m, 2)} for n, m in peer_pool],
        },
        "exclusions": raw.get("exclusions", {}),
        "companies": top,
    }

    # ------------------------------------------------------------------
    # Output routing. A --variant run writes to data/variants/<name>/ and
    # never touches the live outputs, so a dry run cannot publish itself.
    # ------------------------------------------------------------------
    if args.variant:
        out_dir = ROOT / "data" / "variants" / args.variant
        out_dir.mkdir(parents=True, exist_ok=True)
        out_json = out_dir / "ranked.json"
        out_csv = out_dir / "ranked.csv"
        out_public = out_dir / "ranked.site.json"
        print(f"Variant output  : {rel(out_dir)}/  "
              f"(live outputs untouched)")
    else:
        out_json, out_csv, out_public = OUT_JSON, OUT_CSV, OUT_PUBLIC_RANKED

    out_json.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    out_public.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    with out_csv.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow([
            "rank", "name", "category", "hq", "founded",
            "valuation_usd_b", "valuation_basis", "valuation_date",
            "arr_usd_m", "arr_date", "score", "z_val", "z_arr",
            "missing_axes", "summary",
        ])
        for r in top:
            w.writerow([
                r["rank"], r["name"], r["category"], r["hq"], r["founded"],
                "" if r["valuation_usd_b"] is None else r["valuation_usd_b"],
                r["valuation_basis"], r["valuation_date"] or "",
                "" if r["arr_usd_m"] is None else r["arr_usd_m"],
                r["arr_date"] or "",
                r["score"], r["z_val"], r["z_arr"],
                r["missing_axes"], r["summary"],
            ])

    # ------------------------------------------------------------------ console report
    print(f"Input companies : {len(raw['companies'])}")
    print(f"After filter    : {len(companies)}")
    print(f"Ranked (top 100): {len(top)}")
    print(f"  basis  actual  : {payload['counts']['pure_play']}")
    print(f"  basis  derived : {payload['counts']['derived']}")
    print(f"  basis  proxy   : {payload['counts']['proxy']}")
    print()
    print("Model config:")
    print(f"  axis bounds     : {bounds_source}"
          + (f"  (val {args.anchor_val[0]}..{args.anchor_val[1]}B, "
             f"arr {args.anchor_arr[0]}..{args.anchor_arr[1]}M)"
             if args.axis == "anchored" else ""))
    print(f"  peer multiple   : {peer_multiple:.2f}x"
          + (f"  (pinned; computed median {computed_median:.2f}x)"
             if args.peer_multiple else "  (computed median)"))
    print(f"  missing ARR rule: {args.missing_rule}")
    print(f"  axis weights    : {w_val:.2f} valuation / {w_arr:.2f} ARR")
    print()
    print(f"Peer EV/Revenue multiple (pure-play pool, n={len(multiples)}):")
    print(f"  median={peer_multiple:.2f}x  p25={p25:.2f}x  p75={p75:.2f}x  "
          f"min={multiples[0]:.2f}x  max={multiples[-1]:.2f}x")
    print()
    print(f"Valuation axis log10: min={val_min:.2f}  max={val_max:.2f}")
    print(f"ARR       axis log10: min={arr_min:.2f}  max={arr_max:.2f}")
    print()
    print("Valuation cap (derived <= market cap):")
    capped = [r for r in top if r.get("valuation_capped")]
    if capped:
        for r in capped:
            print(f"  CAPPED  {r['name'][:36]:<36} ${r['uncapped_derived_usd_b']}B "
                  f"-> ${r['valuation_usd_b']}B (mkt cap ${r['market_cap_usd_b']}B, "
                  f"market implies {r['market_implied_multiple']}x)")
    else:
        print("  no derived row exceeded its market cap")
    at_cap = [r for r in top
              if r.get("derived_pct_of_market_cap") is not None
              and r["derived_pct_of_market_cap"] >= 99.0
              and not r.get("valuation_capped")]
    for r in at_cap:
        print(f"  AT CAP  {r['name'][:36]:<36} ${r['valuation_usd_b']}B == mkt cap "
              f"${r['market_cap_usd_b']}B ({r['derived_pct_of_market_cap']}%)")
    print()
    print("Top 15:")
    for r in top[:15]:
        tag = {"actual": "P", "derived": "D", "proxy": "X"}[r["valuation_basis"]]
        print(f"  {r['rank']:>3}. [{tag}] {r['name'][:36]:<36} "
              f"val=${r['valuation_usd_b']}B  arr=${r['arr_usd_m']}M  score={r['score']}")
    print()
    print("Bottom 5:")
    for r in top[-5:]:
        tag = {"actual": "P", "derived": "D", "proxy": "X"}[r["valuation_basis"]]
        print(f"  {r['rank']:>3}. [{tag}] {r['name'][:36]:<36} "
              f"val=${r['valuation_usd_b']}B  arr=${r['arr_usd_m']}M  score={r['score']}")


if __name__ == "__main__":
    main()
