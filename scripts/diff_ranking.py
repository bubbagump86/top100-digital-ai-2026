"""diff_ranking.py - compare two ranked.json files and report membership and rank moves.

Usage:
    python scripts/diff_ranking.py OLD.json NEW.json [OUT.txt]
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def load(p):
    # "git:HEAD:data/ranked.json" reads a committed version straight from git
    # (avoids PowerShell redirection mangling the encoding).
    if p.startswith("git:"):
        import subprocess
        ref = p[4:]
        raw = subprocess.run(
            ["git", "-C", str(ROOT), "show", ref],
            check=True, capture_output=True,
        ).stdout
        return json.loads(raw.decode("utf-8"))
    p = Path(p)
    if not p.is_absolute():
        p = ROOT / p
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    old = load(sys.argv[1])
    new = load(sys.argv[2])
    out = Path(sys.argv[3]) if len(sys.argv) > 3 else ROOT / ".tmp_diff.txt"

    o = {c["name"]: c for c in old["companies"]}
    n = {c["name"]: c for c in new["companies"]}
    L = []

    L.append(f"old n={len(o)}  new n={len(n)}")
    L.append("")
    L.append("ENTERED THE TOP 100:")
    for k, v in sorted(n.items(), key=lambda x: x[1]["rank"]):
        if k not in o:
            L.append(f'  #{v["rank"]:<4} {k:<50} score {v["score"]:>6.2f}  '
                     f'val={v["valuation_usd_b"]} arr={v["arr_usd_m"]} basis={v["valuation_basis"]}')
    L.append("")
    L.append("DROPPED OUT OF THE TOP 100:")
    for k, v in sorted(o.items(), key=lambda x: x[1]["rank"]):
        if k not in n:
            L.append(f'  was #{v["rank"]:<4} {k:<50} score {v["score"]:>6.2f}  '
                     f'val={v["valuation_usd_b"]} arr={v["arr_usd_m"]}')
    L.append("")
    L.append("RANK MOVES (2 places or more):")
    for k, v in sorted(n.items(), key=lambda x: x[1]["rank"]):
        if k in o:
            d = o[k]["rank"] - v["rank"]
            if abs(d) >= 2:
                L.append(f'  {k:<50} {o[k]["rank"]:>4} -> {v["rank"]:<4} ({d:+d})')
    L.append("")
    L.append("SCORE CHANGES ON EXISTING ROWS (>=0.5 points):")
    for k, v in sorted(n.items(), key=lambda x: x[1]["rank"]):
        if k in o:
            ds = v["score"] - o[k]["score"]
            if abs(ds) >= 0.5:
                L.append(f'  {k:<50} {o[k]["score"]:>6.2f} -> {v["score"]:>6.2f} ({ds:+.2f})')

    out.write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
