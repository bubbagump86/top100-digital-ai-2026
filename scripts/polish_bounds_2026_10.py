"""
polish_bounds_2026_10.py - make the "why the bounds are fixed" claim
reproducible, and correct a stale figure in section 4.

Two fixes:

1. Section 5 published a measured claim ("shifts the median score by 2.53
   points... reorders 13 companies... A $1M entrant reorders 39") that could
   not be re-run, so it could not be checked and drifted as the pool changed.
   scripts/measure_bound_churn.py now reproduces it exactly with the real
   engine, and the page publishes the current measurement plus the code
   path.

2. Section 4 said a single company "becomes ~40% of the entire axis range".
   On the current data Anthropic is the maximum on BOTH axes, so it owns
   100% of each range - which is what section 5b already says. Corrected so
   the two sections agree.

Run:
    python scripts/polish_bounds_2026_10.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def apply(path, pairs):
    p = ROOT / path
    t = p.read_text(encoding="utf-8")
    for old, new in pairs:
        n = t.count(old)
        if n != 1:
            raise SystemExit(
                f"FAIL {path}: expected 1 occurrence, found {n} for:\n{old[:200]!r}")
        t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    print(f"  {path}: {len(pairs)} edit(s)")


METHODOLOGY = [
    # -- section 4: the axis-share figure -----------------------------------
    ('          eligible set. In a linear scale, Anthropic\'s $100B ARR is\n'
     '          <strong>10,000&times;</strong> Reworkd AI\'s $10M ARR &mdash; a single company\n'
     '          becomes ~40% of the entire axis range just from being the largest.\n'
     '          The histogram becomes unrecoverable below the giants.\n',
     '          eligible set. In a linear scale, Anthropic\'s $100B ARR is\n'
     '          <strong>10,000&times;</strong> Reworkd AI\'s $10M ARR &mdash; and because\n'
     '          Anthropic is also the most valuable company in the set, it sits at\n'
     '          the top of both axes and owns <strong>100% of each axis\'s range</strong>.\n'
     '          The histogram becomes unrecoverable below the giants.\n'),

    # -- section 5: the measured bound-churn claim ---------------------------
    ('          having changed. We measured it &mdash; a company joining with $5M of ARR\n'
     '          shifts the median score by 2.53 points, which nobody would report, and\n'
     '          still reorders 13 companies by three or more places. A $1M entrant\n'
     '          reorders 39.\n',
     '          having changed.\n'
     '        </p>\n'
     '        <p>\n'
     '          We measured it, and the measurement is re-runnable rather than a\n'
     '          number someone typed once: <code>scripts/measure_bound_churn.py</code>\n'
     '          scores the list twice with the real engine &mdash; once with\n'
     '          sample-derived bounds and once with the shipped anchored bounds\n'
     '          &mdash; each time with and without a hypothetical entrant. Output:\n'
     '          <code>data/bound_churn.json</code>.\n'
     '        </p>\n'
     '        <table class="rank" style="margin:14px 0;">\n'
     '          <thead>\n'
     '            <tr>\n'
     '              <th>Entrant</th>\n'
     '              <th class="num">Median score shift</th>\n'
     '              <th class="num">Rows re-scored</th>\n'
     '              <th class="num">Largest score move</th>\n'
     '              <th class="num">Rows moving 3+ places</th>\n'
     '            </tr>\n'
     '          </thead>\n'
     '          <tbody>\n'
     '            <tr><td>$1.0B valuation, $5M ARR</td><td class="num">+2.43</td>'
     '<td class="num">85 of 100</td><td class="num">3.28 pts</td>'
     '<td class="num">17</td></tr>\n'
     '            <tr><td>$1.0B valuation, $1M ARR</td><td class="num">+6.38</td>'
     '<td class="num">88 of 100</td><td class="num">9.37 pts</td>'
     '<td class="num">43</td></tr>\n'
     '            <tr style="background:rgba(74,222,128,0.07);"><td><strong>Same entrants, '
     'anchored bounds (shipped)</strong></td><td class="num"><strong>0.00</strong></td>'
     '<td class="num"><strong>0 of 100</strong></td>'
     '<td class="num"><strong>0.00 pts</strong></td>'
     '<td class="num"><strong>0</strong></td></tr>\n'
     '          </tbody>\n'
     '        </table>\n'
     '        <p>\n'
     '          Under sample-derived bounds, one company joining at $5M of ARR moves\n'
     '          the median score by 2.43 points, re-scores 85 of the other 100 rows,\n'
     '          and reorders 17 of them by three or more places &mdash; churn that has\n'
     '          nothing to do with any company having changed. A $1M-ARR entrant is\n'
     '          worse: +6.38 points on the median, a 9.37-point swing on the worst-hit\n'
     '          row, and 43 rows reordered. Under the shipped anchored bounds the\n'
     '          same two entrants change nothing at all: 0 rows re-scored, 0 rows\n'
     '          reordered.\n'),
]


def main():
    print("making the bound-churn claim reproducible...")
    apply("methodology.html", METHODOLOGY)
    print("done")


if __name__ == "__main__":
    main()
