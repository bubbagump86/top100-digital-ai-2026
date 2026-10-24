"""inspect_weight_movers.py - detail on the rows that move most when ARR is
weighted more heavily, plus the proxy-row effect.

Run: python scripts/inspect_weight_movers.py
"""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
V = ROOT / "data" / "variants"

WATCH = [
    "Midjourney", "Otter.ai", "Mercor", "HeyGen",
    "Palantir Technologies",
    "ByteDance (AI: Doubao + Seed + Volcano Engine)",
    "Samsara", "Cohesity", "Talkdesk", "Schrodinger",
    "VAST Data", "Scale AI", "Mistral AI", "Manus AI", "DeepL",
    "Anthropic", "OpenAI",
]


def load(name):
    return json.loads((V / name / "ranked.json").read_text(encoding="utf-8"))


def main():
    a = load("w050")
    b = load("w040")
    ra = {c["name"]: c for c in a["companies"]}
    rb = {c["name"]: c for c in b["companies"]}

    L = []
    L.append("50/50 vs 40/60 - the rows that move")
    L.append("-" * 118)
    hdr = (f"{'company':<46}{'50/50':>6}{'40/60':>7}{'move':>6}  "
           f"{'val $B':>9}{'ARR $M':>8}{'basis':>9}  {'z_val':>7}{'z_arr':>7}")
    L.append(hdr)
    L.append("-" * 118)
    for n in WATCH:
        ca, cb = ra.get(n), rb.get(n)
        if not ca:
            continue
        rk = cb["rank"] if cb else None
        L.append(f"{n[:45]:<46}{ca['rank']:>6}"
                 f"{(rk if rk else 'OUT'):>7}"
                 f"{(ca['rank'] - rk if rk else 0):>+6}  "
                 f"{str(ca['valuation_usd_b']):>9}{str(ca['arr_usd_m']):>8}"
                 f"{ca['valuation_basis']:>9}  "
                 f"{(ca['z_val'] if ca['z_val'] is not None else 0):>7.3f}"
                 f"{(ca['z_arr'] if ca['z_arr'] is not None else 0):>7.3f}")
    L.append("-" * 118)
    L.append("")
    L.append("Rows leaving the top 100 under 40/60:")
    L.append("  " + ", ".join(sorted(set(ra) - set(rb))) or "  (none)")
    L.append("Rows entering the top 100 under 40/60:")
    L.append("  " + ", ".join(sorted(set(rb) - set(ra))) or "  (none)")

    # The proxy rows specifically: their ARR axis is structurally zero.
    L.append("")
    L.append("PROXY ROWS - market cap on the valuation axis, no AI ARR on the other")
    L.append("-" * 118)
    L.append(f"{'company':<46}{'50/50':>6}{'40/60':>7}{'move':>6}{'score 50/50':>14}{'score 40/60':>14}")
    for n in WATCH:
        ca, cb = ra.get(n), rb.get(n)
        if not ca or ca["valuation_basis"] != "proxy":
            continue
        L.append(f"{n[:45]:<46}{ca['rank']:>6}"
                 f"{(cb['rank'] if cb else 'OUT'):>7}"
                 f"{(ca['rank'] - cb['rank'] if cb else 0):>+6}"
                 f"{ca['score']:>14.2f}{(cb['score'] if cb else 0):>14.2f}")

    (ROOT / ".tmp_movers.txt").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
