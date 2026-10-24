"""
add_coverage_sections_2026_10.py - add the coverage-audit content to the site.

Three insertions:
  1. methodology.html  - new section 2b: the admission rule, the coverage
     audit, and how third-party estimates are treated.
  2. index.html        - a new "Is the coverage complete?" card, rendered
     from data/coverage.json so the numbers can never drift from the audit.
  3. exclusions.html   - a pointer to the audit from the exclusions page.

Run:
    python scripts/add_coverage_sections_2026_10.py
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
    print(f"  {path}: {len(pairs)} insertion(s)")


METHODOLOGY_2B = '''      <div class="card">
        <h2>2b. The admission rule, and the coverage audit</h2>
        <p>
          Eligibility is not a matter of taste. A company is admitted if it is:
        </p>
        <ul>
          <li>
            <strong>Pure-play digital AI</strong> &mdash; the AI business <em>is</em>
            the company, so its market or transaction valuation is already an AI
            valuation. Its multiple also joins the peer pool.
          </li>
          <li>
            <strong>AI-attributed</strong> &mdash; a diversified company that
            <em>discloses</em> AI-attributed revenue. That revenue is valued at
            the peer multiple (section 6b).
          </li>
          <li>
            <strong>Market-cap proxy</strong> &mdash; a company with a material
            AI business that discloses no AI revenue line, where a market-cap
            proxy is defensible. Flagged as the weakest evidence in the list.
          </li>
        </ul>
        <p>
          A software company is <strong>excluded</strong> when AI is neither
          disclosed nor material &mdash; the Apple test in section 2. Scoring
          <em>Datadog</em>, <em>AvePoint</em> or <em>Workato</em> on their full
          market caps would make the valuation axis a measure of observability
          and backup franchises rather than AI: Datadog's management explicitly
          declines to size AI revenue at all, and AvePoint's Q2 2026 release
          discloses SaaS revenue, total revenue and total ARR but no AI line.
          All three are excluded with reasons on the
          <a href="exclusions.html">exclusions page</a>.
        </p>
        <h3>The coverage audit &mdash; no name may be silently absent</h3>
        <p>
          A ranking that only publishes what it included has an invisible hole:
          a company can be missing simply because nobody checked. The 2026-10
          edition was audited against a 39-name third-party AI company list,
          and the audit is now a repeatable step in the pipeline
          (<code>scripts/coverage.py</code>, against
          <code>data/coverage_watchlist.json</code>).
        </p>
        <p>
          The rule the audit enforces: <strong>every watchlist name must resolve
          to exactly one disposition</strong> &mdash; ranked, folded into a
          roll-up row, or excluded with a published reason. A name that resolves
          to nothing is a <strong>coverage gap</strong>, and a gap blocks
          publication.
        </p>
        <p>
          The audit found <strong>19 names with no disposition at all</strong>,
          plus two roll-ups that had never been written down (Google DeepMind
          inside Alphabet, Microsoft Research Asia inside Microsoft). All 21 now
          resolve: 7 were added to the ranking with sourced valuation and
          AI-attributed ARR, 2 are folded into roll-up rows, and 12 are excluded
          with a stated reason. The audit now reports
          <strong>39 of 39 names resolved, zero gaps</strong>.
        </p>
        <h3>How we treat third-party estimates</h3>
        <p>
          A third-party revenue estimate is used as an input only when it is
          (a) above this list's $10M ARR anchor and (b) the best available
          figure. It is then published with its source and an explicit
          confidence flag. Below the anchor it is not used at all &mdash; Luma
          AI's ~$8M Sacra estimate is 22 months old and under the anchor, so
          that row's ARR axis reads 0 under the missing-ARR rule instead. Where
          two sources conflict we publish the conservative figure and name the
          conflict; where a figure is single-sourced we say so.
        </p>
      </div>

'''

INDEX_CARD = '''    <div class="card">
      <h2>Is the coverage complete?</h2>
      <p>
        A ranking that only publishes what it included has an invisible hole: a
        company can be missing simply because nobody checked. This edition was
        audited against a 39-name third-party AI company list, and every name
        must resolve to exactly one disposition &mdash; ranked, folded into a
        roll-up row, or excluded with a published reason.
      </p>
      <div id="coverage" class="chart-wrap" style="margin:16px 0 0;"></div>
      <p style="margin-top:14px;">
        <strong>Result: 39 of 39 names resolved, zero gaps.</strong> 25 are
        ranked, 2 are folded into roll-up rows (Google DeepMind inside Alphabet,
        Microsoft Research Asia inside Microsoft), and 12 are excluded with a
        stated reason &mdash; hardware-first, physical AI, no disclosed AI
        revenue line, or too small to evidence. The audit that enforces this is
        a repeatable step in the pipeline:
        <code>python scripts/coverage.py</code>.
      </p>
    </div>

'''

INDEX_RENDER = '''
      // Coverage audit - read from data/coverage.json so the published
      // numbers can never drift from the audit that produced them.
      try {
        const cres = await fetch("data/coverage.json", { cache: "no-store" });
        const cov = await cres.json();
        const cc = cov.counts || {};
        const box = document.getElementById("coverage");
        if (!box) throw new Error("no #coverage element");
        const gapColor = cov.coverage_complete ? "var(--good)" : "var(--bad)";
        box.innerHTML = `
          <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(140px,1fr));gap:14px;">
            <div>
              <div style="font-size:22px;font-weight:800;">${cov.watchlist_size}</div>
              <div style="font-size:13px;color:var(--text-dim);">names audited</div>
            </div>
            <div>
              <div style="font-size:22px;font-weight:800;color:var(--accent);">${cc.RANKED || 0}</div>
              <div style="font-size:13px;color:var(--text-dim);">ranked</div>
            </div>
            <div>
              <div style="font-size:22px;font-weight:800;color:var(--accent-2);">${cc.FOLDED || 0}</div>
              <div style="font-size:13px;color:var(--text-dim);">folded into a roll-up</div>
            </div>
            <div>
              <div style="font-size:22px;font-weight:800;color:var(--warn);">${cc.EXCLUDED || 0}</div>
              <div style="font-size:13px;color:var(--text-dim);">excluded with a reason</div>
            </div>
            <div>
              <div style="font-size:22px;font-weight:800;color:${gapColor};">${(cov.gaps || []).length}</div>
              <div style="font-size:13px;color:var(--text-dim);">coverage gaps</div>
            </div>
          </div>`;
      } catch (e) {
        const box = document.getElementById("coverage");
        if (box) {
          box.innerHTML = '<p class="sub-note">Coverage data unavailable.</p>';
        }
      }
'''

EXCLUSIONS_NOTE = '''    <div class="card prose">
      <p>
        Every exclusion below carries a stated reason, and the whole set is
        audited against a third-party watchlist by
        <code>scripts/coverage.py</code>: a name can be ranked, folded into a
        roll-up row, or excluded here &mdash; but it can never be silently
        absent. The current audit reports 39 of 39 watchlist names resolved and
        zero gaps.
      </p>
    </div>

'''


def main():
    print("adding coverage-audit content...")
    apply("methodology.html", [
        ('      <div class="card">\n        <h2>3. The two input axes</h2>',
         METHODOLOGY_2B + '      <div class="card">\n        <h2>3. The two input axes</h2>'),
    ])
    apply("index.html", [
        ('    <div class="card">\n      <h2>Is the 20&times; peer multiple load-bearing?</h2>',
         INDEX_CARD + '    <div class="card">\n      <h2>Is the 20&times; peer multiple load-bearing?</h2>'),
        ('      } catch (e) {\n'
         '        document.getElementById("multiple-check").innerHTML =\n'
         '          \'<p class="sub-note">Multiple-check data unavailable.</p>\';\n'
         '      }\n'
         '    });',
         '      } catch (e) {\n'
         '        document.getElementById("multiple-check").innerHTML =\n'
         '          \'<p class="sub-note">Multiple-check data unavailable.</p>\';\n'
         '      }\n' + INDEX_RENDER + '    });'),
    ])
    apply("exclusions.html", [
        ('    <div class="card prose" id="ex-list">',
         EXCLUSIONS_NOTE + '    <div class="card prose" id="ex-list">'),
    ])
    print("done")


if __name__ == "__main__":
    main()
