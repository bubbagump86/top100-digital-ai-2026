"""scan_numbers.py - find numeric claims in the site HTML that may need updating.

Usage: python scripts/scan_numbers.py [file ...]
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Claims known to move when the dataset changes.
PATTERNS = [
    r"\b81\b", r"\b85\b", r"\b89\b", r"\b33\.6\b", r"\b25\.5\b", r"\b37\.7\b",
    r"\b27\.3\b", r"\b20\.0?8?3?\b", r"\b87\b", r"\b90\b", r"\b0\.937\b",
    r"\b0\.831\b", r"\b0\.854\b", r"\b0\.789\b", r"\b0\.979\b", r"\b0\.912\b",
    r"\b0\.919\b", r"\b0\.806\b", r"\b0\.850\b", r"\b0\.774\b", r"\b0\.981\b",
    r"\b0\.910\b", r"\b323\.5\b", r"\b100M\b", r"\bTop 11\b", r"\btop 11\b",
    r"\bn=81\b", r"\b13% of\b", r"\b71 of\b", r"\b2 of 100\b",
]


def main():
    files = sys.argv[1:] or ["index.html", "methodology.html", "about.html",
                             "exclusions.html", "app.js"]
    out = []
    for f in files:
        p = ROOT / f
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        lines = t.split("\n")
        for i, ln in enumerate(lines, 1):
            for pat in PATTERNS:
                if re.search(pat, ln):
                    clean = re.sub(r"\s+", " ", ln.strip())
                    out.append(f"{f}:{i}  [{pat}]  {clean[:400]}")
                    break
    dest = ROOT / ".tmp_numbers.txt"
    dest.write_text("\n".join(out), encoding="utf-8")
    print(f"{len(out)} candidate lines -> {dest.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
