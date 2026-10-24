"""
patch_methodology_weights.py - replace the hand-waved weighting claim with
the measured one.

The old text said: "We tested the ranking with W_VAL = 0.6 / W_ARR = 0.4 ...
The top 10 was stable; reordering happened mostly in the 30-70 range." No
code, no numbers, no way to check it. It also asserted equal weights were
"the simplest justifiable weighting that doesn't privilege private-market
hype over disclosed revenue" without ever examining what the valuation axis
actually contributes.

The replacement publishes the decomposition and the measured splits, and
records where the weights live (data/model_config.json, as policy).

Run:
    python scripts/patch_methodology_weights.py
"""

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "methodology.html"

OLD = '''        <h3>Why equal weights?</h3>
        <p>
          Sensitivity to the weight choice is a real concern. We tested the
          ranking with W_VAL = 0.6 / W_ARR = 0.4 (used in some
          VC-readiness scorecards) and with W_VAL = 0.4 / W_ARR = 0.6
          (used in some growth-investing scorecards). The top 10 was stable;
          reordering happened mostly in the 30-70 range, which is what we'd
          expect from any composite.
        </p>
'''

NEW = '''        <h3>Why equal weights? &mdash; and what the weighting actually does</h3>
        <p>
          The weighting is the most contestable number in the model, so it is
          measured rather than asserted. It is held in
          <code>data/model_config.json</code> as policy, and
          <code>scripts/weight_assessment.py</code> re-runs the whole pipeline
          at any split. There is a subtlety that changes the whole argument.
          For a pure-play, valuation and ARR are <em>not</em> independent:
          valuation <em>is</em> ARR &times; a multiple. So the composite can be
          rewritten exactly:
        </p>
        <pre>z_val = z_arr + (log10(multiple) - 1) / 4

S = 100 * ( z_arr  +  w_val * (log10 m - 1) / 4 )
           \\__ ARR __/    \\__ multiple premium __/</pre>
        <p>
          The ARR <em>level</em> carries weight 1.0 at <em>every</em> split. The
          valuation axis contributes only the <em>multiple premium</em> &mdash;
          how many times ARR the market pays &mdash; at w_val / 4 per decade.
          Across the 75 pure-plays the ARR level term explains
          <strong>110%</strong> of the composite&rsquo;s variance and the
          multiple premium <strong>7%</strong>. The two axes are
          negatively correlated, so the premium partly cancels the level term.
        </p>
        <p>
          The practical consequence: <strong>this model is already
          overwhelmingly an ARR-level model</strong>, and &ldquo;50/50&rdquo;
          is not a 50/50 in substance. Re-weighting towards revenue does not
          shift the balance towards revenue level &mdash; the level term is
          fixed &mdash; it shrinks the multiple premium by 20% and, as a side
          effect, cuts every row with no disclosed ARR by 20% on the axis it
          does have.
        </p>
        <table class="rank" style="margin:14px 0;">
          <thead>
            <tr>
              <th>Split (valuation / ARR)</th>
              <th class="num">&rho; vs shipped</th>
              <th class="num">Rows moving 5+ places</th>
              <th class="num">Rows moving 10+</th>
              <th class="num">Top 13 unchanged</th>
              <th class="num">Top 11 stable at 10&ndash;40&times;</th>
            </tr>
          </thead>
          <tbody>
            <tr><td><strong>0.50 / 0.50 (shipped)</strong></td><td class="num">1.000</td><td class="num">0</td><td class="num">0</td><td class="num">13 / 13</td><td class="num">11 / 11</td></tr>
            <tr><td>0.45 / 0.55</td><td class="num">0.995</td><td class="num">12</td><td class="num">0</td><td class="num">13 / 13</td><td class="num">11 / 11</td></tr>
            <tr><td>0.40 / 0.60</td><td class="num">0.981</td><td class="num">28</td><td class="num">12</td><td class="num">13 / 13</td><td class="num">11 / 11</td></tr>
            <tr><td>0.35 / 0.65</td><td class="num">0.953</td><td class="num">37</td><td class="num">15</td><td class="num">13 / 13</td><td class="num">11 / 11</td></tr>
            <tr><td>0.30 / 0.70</td><td class="num">0.911</td><td class="num">42</td><td class="num">21</td><td class="num">13 / 13</td><td class="num">11 / 11</td></tr>
          </tbody>
        </table>
        <p>
          The head of the list does not care: the top 13 is identical at every
          split, and the top 11 survives the peer multiple at every multiple
          from 10&times; to 40&times;. All the movement is in the mid-table,
          where scores are densely packed &mdash; 28 rows move five or more
          places on a score change of at most four points.
        </p>
        <p>
          What the move <em>does</em> is expose a second effect. Under the
          &ldquo;missing ARR reads 0&rdquo; rule, a row with no AI revenue
          disclosure is scored w_val &times; z_val only. Raising the ARR weight
          therefore does not only reward rows that <em>have</em> revenue &mdash;
          it shrinks the axis that the rows <em>without</em> disclosed revenue
          are scored on. At 0.40 / 0.60, Palantir falls from #26 to #36,
          ByteDance from #28 to #39, Samsara from #52 to #66, Schrodinger leaves
          the top 100 entirely, and Safe Superintelligence moves from #50 to
          #63. That is a disclosure artefact, not a statement about those
          companies. The weighting and the missing-ARR rule have to be decided
          together; the rule dominates.
        </p>
        <p>
          <strong>Our call.</strong> Keep the equal split. It is the only
          setting that does not privilege either axis, the lever it moves is
          small (the valuation axis is 7% of the composite&rsquo;s variance
          across pure-plays, not 50%), and the rows it disturbs most are the
          rows whose ranking already rests on a disclosed weakness rather than
          on their AI business. If a revenue tilt is wanted, 0.45 / 0.55 is
          nearly free &mdash; &rho; 0.995, no row moves ten places &mdash; and
          should be taken at a quarterly policy review, not mid-edition,
          because it changes every score and breaks comparability with
          previous editions.
        </p>
'''


def main():
    t = P.read_text(encoding="utf-8")
    n = t.count(OLD)
    if n != 1:
        raise SystemExit(f"FAIL: expected 1 occurrence, found {n}")
    t = t.replace(OLD, NEW)

    # Point §6 at the policy file, since the weights now live there.
    old2 = ("Composite score is the equal-weighted average of the two rescaled\n"
            "          axes, expressed on a 0-100 scale:")
    new2 = ("Composite score is the equal-weighted average of the two rescaled\n"
            "          axes, expressed on a 0-100 scale. The weights are policy, held\n"
            "          in <code>data/model_config.json</code>:")
    if t.count(old2) != 1:
        raise SystemExit("FAIL: section 6 intro not found")
    t = t.replace(old2, new2)

    P.write_text(t, encoding="utf-8")
    print("methodology.html: weighting section replaced")


if __name__ == "__main__":
    main()
