"""
polish_snowflake_2026_10.py - fold the Snowflake row into the hardcoded
cross-check copy.

Snowflake is a derived row, so it belongs in the market cross-check table
(market implies 1,147x on $100M of disclosed AI revenue), and it changes two
hardcoded claims:

  * "Every other derived row lands between 5.7% and 68.9% of its market cap"
    -> the floor is now Snowflake at 1.7%.
  * "Two findings here" -> three, because Snowflake is the most extreme
    implied multiple in the table.

Also adds Snowflake to the section 3 AI-attribution policy list and to the
section 6b worked examples, so both are complete.

Run:
    python scripts/polish_snowflake_2026_10.py
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
    # -- section 3: AI-attribution policy list ------------------------------
    ('          <li>\n'
     '            <strong>Palantir, Samsara, Schrodinger, ByteDance, Cohesity, Talkdesk</strong>\n'
     '            &mdash; no AI-attributed revenue disclosed. Handled as\n'
     '            <em>market-cap proxies</em> (section 6b).\n'
     '          </li>\n',
     '          <li>\n'
     '            <strong>Snowflake</strong> &mdash; <strong>$100M</strong> annualised\n'
     '            AI revenue run-rate (company-stated, Dec 2025, not updated at Q2\n'
     '            FY2027). A published AI line, so it is derived rather than proxied\n'
     '            &mdash; but stale and small against a $114.7B market cap, so we\n'
     '            under-credit it rather than guess upward.\n'
     '          </li>\n'
     '          <li>\n'
     '            <strong>Palantir, Samsara, Schrodinger, ByteDance, Cohesity, Talkdesk</strong>\n'
     '            &mdash; no AI-attributed revenue disclosed. Handled as\n'
     '            <em>market-cap proxies</em> (section 6b).\n'
     '          </li>\n'),

    # -- section 6b: worked examples ----------------------------------------
    ('ServiceNow   $1,500M AI ARR x 20x =  $30B implied AI valuation\n'
     'Salesforce     $800M AI ARR x 20x =  $16B implied AI valuation</pre>',
     'ServiceNow   $1,500M AI ARR x 20x =  $30B implied AI valuation\n'
     'Salesforce     $800M AI ARR x 20x =  $16B implied AI valuation\n'
     'Snowflake      $100M AI ARR x 20x =   $2B implied AI valuation</pre>'),

    # -- section 6b: the cap paragraph ---------------------------------------
    ('          the cap binding. Every other derived row lands between 5.7% and\n'
     '          68.9% of its market cap.',
     '          the cap binding. Every other derived row lands between 1.7% and\n'
     '          68.9% of its market cap.'),

    # -- 6c Test 4: add the Snowflake row, highest implied multiple ----------
    ('            <tr><td>Salesforce</td><td class="num">$280B</td>',
     '            <tr><td>Snowflake</td><td class="num">$114.7B</td>'
     '<td class="num">$100M</td><td class="num">1,147&times;</td>'
     '<td class="num">$2B</td><td class="num">$2B</td>'
     '<td class="num">1.7%</td></tr>\n'
     '            <tr><td>Salesforce</td><td class="num">$280B</td>'),

    # -- 6c Test 4: the findings --------------------------------------------
    ('        <p>\n'
     '          Two findings here.\n'
     '        </p>\n',
     '        <p>\n'
     '          Three findings here.\n'
     '        </p>\n'),

    ('          <strong>Second: Baidu is the one row where the derivation overruns\n'
     '          the company.</strong>',
     '          <strong>Second: Snowflake is the extreme case at 1,147&times;.</strong>\n'
     '          Its $100M of disclosed AI revenue is 1.7% of a $114.7B market cap,\n'
     '          so the market is paying for the data platform and the AI story, not\n'
     '          for the AI revenue. That is the clearest illustration of why a\n'
     '          disclosed AI line and a full market cap are not interchangeable\n'
     '          &mdash; and why we publish the AI figure on its own.\n'
     '        </p>\n'
     '        <p>\n'
     '          <strong>Third: Baidu is the one row where the derivation overruns\n'
     '          the company.</strong>'),
]


def main():
    print("folding Snowflake into the cross-check copy...")
    apply("methodology.html", METHODOLOGY)
    print("done")


if __name__ == "__main__":
    main()
