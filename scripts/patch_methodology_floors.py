"""
patch_methodology_floors.py - document the axis floor clamp and fix two
stale figures the log-min probe exposed.

1. Section 4 cites Reworkd AI as the smallest ARR in the list. Reworkd has
   fallen out of the top 100, so the example points at a company a reader
   cannot find. The smallest ARR in the list is now SandboxAQ at $17.8M.

2. Section 8 quotes OpenAI's z-scores as 0.882 / 0.912, which are from an
   older edition. The current values are 0.983 / 0.925.

3. Sections 5 and 7 now document the axis floor clamp: a value below a floor
   reads 0, the same as a missing value. Without it a company with a little
   revenue scores BELOW a company with none.

Run:
    python scripts/patch_methodology_floors.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "methodology.html"

PAIRS = [
    # --- section 4: the stale Reworkd example ------------------------------
    ("          Valuation and ARR each span 5+ orders of magnitude across the\n"
     "          eligible set. In a linear scale, Anthropic's $100B ARR is\n"
     "          <strong>10,000&times;</strong> Reworkd AI's $10M ARR &mdash; and because\n"
     "          Anthropic is also the most valuable company in the set, it sits at\n"
     "          the top of both axes and owns <strong>100% of each axis's range</strong>.\n"
     "          The histogram becomes unrecoverable below the giants.\n",

     "          Valuation and ARR each span 5+ orders of magnitude across the\n"
     "          eligible set. In a linear scale, Anthropic's $100B ARR is over\n"
     "          <strong>5,600&times;</strong> SandboxAQ's $17.8M ARR &mdash; the smallest\n"
     "          AI-attributed revenue figure in the list &mdash; and because Anthropic is\n"
     "          also the most valuable company in the set, it sits at the top of both\n"
     "          axes and owns <strong>100% of each axis's range</strong>. The histogram\n"
     "          becomes unrecoverable below the giants.\n"),

    ("          Taking <code>log10</code> compresses extremes into a much more\n"
     "          information-dense scale. After log, Anthropic is at 5.00,\n"
     "          Reworkd is at 1.00 &mdash; a 5&times; ratio, not 10,000&times;.\n"
     "          This is the standard treatment for financial\n"
     "          power-law distributions.\n",

     "          Taking <code>log10</code> compresses extremes into a much more\n"
     "          information-dense scale. After log, Anthropic is at 5.00 and\n"
     "          SandboxAQ at 1.25 &mdash; a span of 3.75 of the axis's 4 log decades,\n"
     "          not 5,600&times;. This is the standard treatment for financial\n"
     "          power-law distributions.\n"),

    # --- section 5: document the floor clamp -------------------------------
    ("          <li>ARR: log<sub>10</sub> anchored from 1.00 (~$10M) to 5.00 (~$100B)</li>\n"
     "        </ul>\n",

     "          <li>ARR: log<sub>10</sub> anchored from 1.00 (~$10M) to 5.00 (~$100B)</li>\n"
     "        </ul>\n"
     "        <p>\n"
     "          A value <strong>below</strong> a floor reads 0 &mdash; the same as a\n"
     "          missing value. The top end is <em>not</em> clamped: a score above 100\n"
     "          is the signal that an anchor has gone stale. Without the floor rule,\n"
     "          a company with $5M of ARR would score <em>below</em> a company with no\n"
     "          ARR at all, because &ldquo;no ARR&rdquo; is scored 0 while a sub-floor\n"
     "          figure scores negative. That is a monotonicity break, and on a live\n"
     "          list it would surface the first time a very small company joined.\n"
     "          The valuation floor earns its keep the same way: raise it from $0.1B\n"
     "          to $1B and Otter.ai &mdash; a real company with a $0.5B valuation &mdash;\n"
     "          would drop below companies with no valuation mark at all.\n"
     "        </p>\n"),

    # --- section 7: the third kind of missing data --------------------------
    ("          <li>\n"
     "            <strong>Both missing</strong>. We drop them entirely.\n"
     "          </li>\n"
     "        </ol>\n",

     "          <li>\n"
     "            <strong>Both missing</strong>. We drop them entirely.\n"
     "          </li>\n"
     "          <li>\n"
     "            <strong>Below the axis floor</strong> (e.g. $5M of ARR against a\n"
     "            $10M floor). These read 0 on that axis, exactly like a missing\n"
     "            value &mdash; &ldquo;no usable signal&rdquo; rather than\n"
     "            &ldquo;worse than no signal&rdquo;. See section 5.\n"
     "          </li>\n"
     "        </ol>\n"),

    # --- section 8: the stale OpenAI z-scores -------------------------------
    ("OpenAI is #2 (z_val 0.882, z_arr 0.912 &rarr; 95.37).",
     "OpenAI is #2 (z_val 0.983, z_arr 0.925 &rarr; 95.37)."),
]


def main():
    t = P.read_text(encoding="utf-8")
    for old, new in PAIRS:
        n = t.count(old)
        if n != 1:
            raise SystemExit(f"FAIL: {n} occurrences for:\n{old[:180]!r}")
        t = t.replace(old, new)
    P.write_text(t, encoding="utf-8")
    print(f"methodology.html: {len(PAIRS)} edits applied")


if __name__ == "__main__":
    main()
