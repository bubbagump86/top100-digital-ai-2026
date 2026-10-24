"""
coverage.py - coverage audit for the Top 100 Digital AI Companies list.

WHY THIS EXISTS
---------------
A ranking that only publishes what it included has an invisible hole: a
company can be missing simply because nobody checked. The failure mode is
exactly what this audit was built to catch - 19 names from a third-party
list had no disposition at all, not even an exclusion.

The rule this script enforces: every name on a watchlist must resolve to
EXACTLY ONE disposition.

    RANKED    it is in the published Top 100
    FOLDED    it is not ranked on its own because it is a division of a
              ranked company, and the roll-up is disclosed
    EXCLUDED  it is not eligible, and the reason is published on the
              exclusions page
    GAP       it has no disposition - a COVERAGE GAP, which is a bug

A GAP is a release blocker. Close it by adding the company to
data/companies.json (ranked or as a roll-up) or to the exclusions list.

Run:
    python scripts/coverage.py
    python scripts/coverage.py --json-only
"""

import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
WATCHLIST = ROOT / "data" / "coverage_watchlist.json"
COMPANIES = ROOT / "data" / "companies.json"
RANKED = ROOT / "data" / "ranked.json"
OUT = ROOT / "data" / "coverage.json"


def norm(s):
    """Normalise for matching: lowercase, alphanumerics only."""
    return re.sub(r"[^a-z0-9]", "", (s or "").lower())


def parse_args(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--json-only", action="store_true",
                   help="write data/coverage.json without printing the report")
    p.add_argument("--out", default=str(OUT))
    return p.parse_args(argv)


def resolve(entry, companies, ranked, exclusions):
    """Resolve one watchlist entry to a disposition."""
    name = entry["name"]
    explicit = entry.get("match")

    # ---- RANKED -------------------------------------------------------
    # An explicit match wins; otherwise try exact then normalised.
    candidates = []
    if explicit:
        candidates.append(explicit)
    candidates.append(name)

    ranked_by_name = {c["name"]: c for c in ranked["companies"]}
    ranked_by_norm = {norm(c["name"]): c for c in ranked["companies"]}

    for cand in candidates:
        if cand in ranked_by_name:
            r = ranked_by_name[cand]
            return {"status": "RANKED", "as": cand, "rank": r["rank"],
                    "score": r["score"], "basis": r["valuation_basis"]}
    for cand in candidates:
        n = norm(cand)
        if n in ranked_by_norm:
            r = ranked_by_norm[n]
            return {"status": "RANKED", "as": r["name"], "rank": r["rank"],
                    "score": r["score"], "basis": r["valuation_basis"]}

    # ---- FOLDED -------------------------------------------------------
    # A company row that is skipped for ranking but points at the row it
    # rolls into (duplicate_in_ranking_with), or whose name says so.
    for c in companies:
        target = c.get("duplicate_in_ranking_with")
        if not target:
            continue
        if norm(c["name"]) == norm(name) or norm(target) == norm(name):
            host = ranked_by_name.get(target) or ranked_by_norm.get(norm(target))
            return {"status": "FOLDED", "as": c["name"], "into": target,
                    "rank": host["rank"] if host else None}

    # ---- EXCLUDED -----------------------------------------------------
    # The explicit match wins here too - the exclusion list carries the
    # disambiguated name ("Prometheus (prometheus.ai)") while the watchlist
    # carries the bare name the third-party list used.
    for ex in exclusions.get("examples", []):
        if norm(ex.get("name", "")) == norm(name):
            return {"status": "EXCLUDED", "as": ex["name"], "why": ex.get("why")}
    if explicit:
        for ex in exclusions.get("examples", []):
            if norm(ex.get("name", "")) == norm(explicit):
                return {"status": "EXCLUDED", "as": ex["name"], "why": ex.get("why")}

    # ---- GAP ----------------------------------------------------------
    return {"status": "GAP", "as": name}


def main(argv=None):
    args = parse_args(argv)

    watch = json.loads(WATCHLIST.read_text(encoding="utf-8"))
    companies = json.loads(COMPANIES.read_text(encoding="utf-8"))["companies"]
    ranked = json.loads(RANKED.read_text(encoding="utf-8"))
    exclusions = ranked.get("exclusions", {})

    results = []
    for entry in watch["entries"]:
        r = resolve(entry, companies, ranked, exclusions)
        r["watchlist_name"] = entry["name"]
        r["claimed_rank"] = entry.get("claimed_rank")
        results.append(r)

    counts = {}
    for r in results:
        counts[r["status"]] = counts.get(r["status"], 0) + 1
    gaps = [r for r in results if r["status"] == "GAP"]

    payload = {
        "policy_version": watch.get("policy_version"),
        "reviewed": watch.get("reviewed"),
        "watchlist_size": len(results),
        "counts": counts,
        "coverage_complete": not gaps,
        "gaps": [g["watchlist_name"] for g in gaps],
        "results": results,
    }
    outp = Path(args.out)
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")

    if args.json_only:
        print(f"wrote {outp.relative_to(ROOT)}  "
              f"gaps={len(gaps)}  coverage_complete={not gaps}")
        return

    line = "=" * 78
    print(line)
    print("COVERAGE AUDIT - every watchlist name must have a disposition")
    line = "=" * 78
    print(f"  watchlist      : {len(results)} names")
    for k in ("RANKED", "FOLDED", "EXCLUDED", "GAP"):
        print(f"  {k:<14} : {counts.get(k, 0)}")
    print()
    print(f"  COVERAGE COMPLETE: {'YES' if not gaps else 'NO - ' + str(len(gaps)) + ' GAP(S)'}")
    print()

    for status in ("GAP", "EXCLUDED", "FOLDED", "RANKED"):
        rows = [r for r in results if r["status"] == status]
        if not rows:
            continue
        print("-" * 78)
        print(f"{status}  ({len(rows)})")
        print("-" * 78)
        for r in sorted(rows, key=lambda x: (x.get("claimed_rank") or 99999)):
            claimed = r.get("claimed_rank")
            claimed_s = f"claimed #{claimed}" if claimed else "claimed n/a"
            if status == "RANKED":
                print(f"  {r['watchlist_name'][:42]:<43} -> {r['as'][:34]:<35} "
                      f"#{r['rank']:<4} score {r['score']:>6.2f}  [{r['basis']}]  ({claimed_s})")
            elif status == "FOLDED":
                print(f"  {r['watchlist_name'][:42]:<43} -> inside {r['into'][:34]:<35} "
                      f"#{r['rank']}  ({claimed_s})")
            elif status == "EXCLUDED":
                why = (r.get("why") or "")[:70]
                print(f"  {r['watchlist_name'][:42]:<43} EXCLUDED: {why}  ({claimed_s})")
            else:
                print(f"  {r['watchlist_name'][:42]:<43} ** NO DISPOSITION **  ({claimed_s})")
        print()

    print(f"wrote {outp.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
