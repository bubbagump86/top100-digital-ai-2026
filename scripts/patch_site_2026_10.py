"""
patch_site_2026_10.py - update the site copy for the coverage-closed 2026-10 edition.

Every figure below comes from the regenerated pipeline outputs
(data/ranked.json, data/sensitivity.json, data/multiple_check.json,
data/coverage.json). The script asserts each replacement fires exactly once,
so a stale edit fails loudly instead of silently drifting.

Run:
    python scripts/patch_site_2026_10.py
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
                f"FAIL {path}: expected 1 occurrence, found {n} for:\n{old[:160]!r}")
        t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    print(f"  {path}: {len(pairs)} edits applied")


# ===========================================================================
# methodology.html
# ===========================================================================

METHODOLOGY = [
    # -- 5b robustness table: new correlations ------------------------------
    ('<tr><td>B &mdash; raw + min-max</td><td class="num">+0.937</td>'
     '<td class="num">+0.831</td>',
     '<tr><td>B &mdash; raw + min-max</td><td class="num">+0.919</td>'
     '<td class="num">+0.806</td>'),

    ('<tr><td>C &mdash; raw + z-score</td><td class="num">+0.854</td>'
     '<td class="num">+0.789</td>',
     '<tr><td>C &mdash; raw + z-score</td><td class="num">+0.850</td>'
     '<td class="num">+0.774</td>'),

    ('<tr><td>D &mdash; raw + percentile</td><td class="num">+0.979</td>'
     '<td class="num">+0.912</td><td class="num" style="color:var(--good);">'
     '2 of 100</td></tr>',
     '<tr><td>D &mdash; raw + percentile</td><td class="num">+0.981</td>'
     '<td class="num">+0.910</td><td class="num" style="color:var(--good);">'
     '0 of 100</td></tr>'),

    ('<strong>+0.937</strong> with the shipped model',
     '<strong>+0.919</strong> with the shipped model'),

    ('Raw + z-score has the lowest correlation (+0.854)',
     'Raw + z-score has the lowest correlation (+0.850)'),

    # -- Finding 3: the raw min-max movers, with this edition's ranks -------
    ('DeepSeek #40&rarr;#16, Thinking Machines Lab #41&rarr;#17, '
     'SSI #48&rarr;#22,\n          Reflection AI #54&rarr;#26, '
     'Moonshot AI #56&rarr;#29.',
     'DeepSeek #41&rarr;#16, Thinking Machines Lab #42&rarr;#17, '
     'SSI #50&rarr;#22,\n          Reflection AI #56&rarr;#26, '
     'Moonshot AI #58&rarr;#29, Luma AI #93&rarr;#58.'),

    # -- Finding 5: percentile variant --------------------------------------
    ('correlates <em>more</em> closely with the shipped model (+0.979\n'
     '          Spearman, +0.912 Kendall) than raw min-max does, matches the '
     'top 12\n          exactly, and is invariant to any monotone change of '
     'units. It\'s also\n          the most discriminative of the four: only '
     '<strong>2 of 100</strong>\n          rows fall below 5/100 (vs 0 for the '
     'shipped log model and 87-90 for\n          the raw variants).',
     'correlates <em>more</em> closely with the shipped model (+0.981\n'
     '          Spearman, +0.910 Kendall) than raw min-max does, matches the '
     'top 12\n          exactly, and is invariant to any monotone change of '
     'units. It\'s also\n          the only variant besides the shipped one '
     'that keeps every row above 5/100:\n          <strong>0 of 100</strong> rows '
     'fall below 5/100 (against 87-90 for\n          the raw variants).'),

    ('proxy rows (Palantir #26&rarr;#43, ByteDance #28&rarr;#47) because a',
     'proxy rows (Palantir #26&rarr;#42, ByteDance #28&rarr;#45) because a'),

    # -- section 6b: the peer pool ------------------------------------------
    ('<li>Pool: <strong>81 pure-play companies</strong> with both a valuation '
     'and an ARR figure</li>',
     '<li>Pool: <strong>85 pure-play companies</strong> with both a valuation '
     'and an ARR figure</li>'),

    ('edition</em> (n=81, IQR 15&ndash;40&times;, mean 33.6&times;, trimmed\n'
     '          mean 25.5&times;).',
     'edition</em> (n=85, IQR 15&ndash;40&times;, mean 37.7&times;, trimmed\n'
     '          mean 27.3&times;).'),

    ('adding one company at 90.9&times; moves it from 20.00&times; to\n'
     '          20.42&times; and shifts every derived megacap row.',
     'adding one company at 90.9&times; moves it from 20.83&times; to\n'
     '          21.08&times; and shifts every derived megacap row.'),

    # -- 6c Test 1: distribution table ---------------------------------------
    ('<tr><td>mean</td><td class="num">33.6&times;</td>',
     '<tr><td>mean</td><td class="num">37.7&times;</td>'),

    ('<tr><td>10% trimmed mean</td><td class="num">25.5&times;</td>',
     '<tr><td>10% trimmed mean</td><td class="num">27.3&times;</td>'),

    ('<tr><td>p90</td><td class="num">62.5&times;</td>',
     '<tr><td>p90</td><td class="num">76.0&times;</td>'),

    ('statistics &mdash; the mean is 68% higher and the trimmed mean 28%',
     'statistics &mdash; the mean is 89% higher and the trimmed mean 37%'),

    # -- 6c Test 2: comparability by scale -----------------------------------
    ('<tr><td>ARR &lt; $100M</td><td class="num">37</td>'
     '<td class="num">20.0&times;</td><td class="num">7.5&ndash;149&times;</td></tr>',
     '<tr><td>ARR &lt; $100M</td><td class="num">36</td>'
     '<td class="num">21.1&times;</td><td class="num">7.5&ndash;314.6&times;</td></tr>'),

    ('<tr><td>$100M &ndash; $1B</td><td class="num">29</td>'
     '<td class="num">30.1&times;</td><td class="num">5.0&ndash;324&times;</td></tr>',
     '<tr><td>$100M &ndash; $1B</td><td class="num">30</td>'
     '<td class="num">29.3&times;</td><td class="num">5.0&ndash;323.5&times;</td></tr>'),

    # -- 6c Test 3: geography -------------------------------------------------
    ('<tr><td>Western pure-plays</td><td class="num">76</td>'
     '<td class="num">20.0&times;</td><td class="num">14.9&ndash;37.2&times;</td></tr>',
     '<tr><td>Western pure-plays</td><td class="num">80</td>'
     '<td class="num">20.0&times;</td><td class="num">14.9&ndash;39.1&times;</td></tr>'),

    # -- worked example --------------------------------------------------------
    ('peer multiple (pinned)    = 20.0x     (pure-play median, 2026-10 edition, n=81)',
     'peer multiple (pinned)    = 20.0x     (pure-play median, 2026-10 edition, n=85)'),

    # -- reproduction console output ------------------------------------------
    ('  peer multiple   : 20.00x  (pinned; computed median 20.00x)',
     '  peer multiple   : 20.00x  (pinned; computed median 20.83x)'),

    ('Peer EV/Revenue multiple (pure-play pool, n=81):',
     'Peer EV/Revenue multiple (pure-play pool, n=85):'),

    ('  median=20.00x  p25=15.00x  p75=40.00x',
     '  median=20.83x  p25=15.00x  p75=40.00x'),

    # -- limitations -----------------------------------------------------------
    ('median across 81 companies spanning $10M to $100B ARR.',
     'median across 85 companies spanning $10M to $100B ARR.'),
]

# ===========================================================================
# index.html
# ===========================================================================

INDEX = [
    ('derived from 81 pure-play companies) to get an implied standalone AI',
     'derived from 85 pure-play companies) to get an implied standalone AI'),

    ('superficially similar (Spearman +0.937) while quietly pushing',
     'superficially similar (Spearman +0.919) while quietly pushing'),
]

# ===========================================================================
# about.html
# ===========================================================================

ABOUT = [
    ('          Two analysis scripts back the robustness sections:\n'
     '          <code>scripts/sensitivity.py</code> (log vs raw normalisation)\n'
     '          and <code>scripts/multiple_check.py</code> (stress-tests the 20&times;\n'
     '          peer multiple). Both write JSON into <code>data/</code>, which the\n'
     '          overview page reads directly.\n',
     '          Two analysis scripts back the robustness sections:\n'
     '          <code>scripts/sensitivity.py</code> (log vs raw normalisation)\n'
     '          and <code>scripts/multiple_check.py</code> (stress-tests the 20&times;\n'
     '          peer multiple). Both write JSON into <code>data/</code>, which the\n'
     '          overview page reads directly.\n'
     '        </p>\n'
     '        <p>\n'
     '          A third script, <code>scripts/coverage.py</code>, audits coverage.\n'
     '          Every name on a watchlist (<code>data/coverage_watchlist.json</code>)\n'
     '          must resolve to exactly one disposition &mdash; ranked, folded into a\n'
     '          roll-up row, or excluded with a published reason. A name with no\n'
     '          disposition is a coverage gap and blocks publication. The audit\n'
     '          currently reports 39 of 39 names resolved and zero gaps.\n'),
]


def main():
    print("patching site copy...")
    apply("methodology.html", METHODOLOGY)
    apply("index.html", INDEX)
    apply("about.html", ABOUT)
    print("done")


if __name__ == "__main__":
    main()
