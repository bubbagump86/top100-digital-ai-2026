"""
polish_pin_2026_10.py - accuracy fixes after the coverage update.

Three issues, all caused by the peer pool moving under a pinned multiple:

  1. index.html showed the COMPUTED pool median (20.83x) under the label
     "pinned", which is wrong - the pinned multiple is 20.0x. The two used
     to coincide, so the panel looked correct until this edition.
  2. The same panel hardcoded "11 / 11" for the top-11 stability figure.
  3. methodology.html described the pin as "the pure-play median as measured
     on the 2026-10 edition (n=85)" - but the pin was set from the n=81
     pool. The current pool computes to 20.83x, which is inside the retune
     trigger, so the pin stands and the copy has to say so accurately.

Run:
    python scripts/polish_pin_2026_10.py
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


INDEX = [
    # 1. pinned multiple vs computed pool median
    ('              <div style="font-size:22px;font-weight:800;">${d.p50_median}&times;</div>\n'
     '              <div class="sub-note">pinned (pool median ${d.p50_median}&times;, mean ${d.mean}&times;)</div>',
     '              <div style="font-size:22px;font-weight:800;">${mc.peer_multiple.median_ev_revenue}&times;</div>\n'
     '              <div class="sub-note">pinned (pool median ${d.p50_median}&times;, mean ${d.mean}&times;)</div>'),

    # 2. top-11 stability from the data, not hardcoded
    ('              <div style="font-size:22px;font-weight:800;color:var(--good);">11 / 11</div>\n'
     '              <div class="sub-note">top-11 unchanged from 10&times; to 40&times;</div>',
     '              <div style="font-size:22px;font-weight:800;color:var(--good);">'
     '${mc.top11_stability.always_present.length} / ${mc.top11_stability.ever_present.length}</div>\n'
     '              <div class="sub-note">top-${mc.top11_stability.always_present.length} unchanged '
     'from 10&times; to 40&times;</div>'),
]

METHODOLOGY = [
    # 3. describe the pin accurately against the current pool
    ('          The 20&times; is the pure-play median <em>as measured on the 2026-10\n'
     '          edition</em> (n=85, IQR 15&ndash;40&times;, mean 37.7&times;, trimmed\n'
     '          mean 27.3&times;). It is held fixed in\n'
     '          <code>data/model_config.json</code> rather than recomputed on every\n'
     '          run, for the same reason the axis bounds are fixed: a live list cannot\n'
     '          have its derived valuations move because the composition of the peer\n'
     '          pool changed. The median is itself a sample-dependent number &mdash;\n'
     '          adding one company at 90.9&times; moves it from 20.83&times; to\n'
     '          21.08&times; and shifts every derived megacap row.\n',
     '          The 20&times; is the pure-play median <em>as measured when the pin was\n'
     '          set</em>, and it is held fixed in <code>data/model_config.json</code>\n'
     '          rather than recomputed on every run, for the same reason the axis\n'
     '          bounds are fixed: a live list cannot have its derived valuations move\n'
     '          because the composition of the peer pool changed. The median is\n'
     '          itself a sample-dependent number &mdash; adding one company at\n'
     '          90.9&times; moves the current pool from 20.83&times; to 21.08&times; and\n'
     '          shifts every derived megacap row.\n'
     '        </p>\n'
     '        <p>\n'
     '          The <em>current</em> pool (n=85, IQR 15&ndash;40&times;, mean 37.7&times;,\n'
     '          trimmed mean 27.3&times;) computes to a median of 20.83&times; &mdash; a\n'
     '          move of 0.83&times; from the pinned 20.0&times;, and far inside the\n'
     '          one-third-of-an-IQR retune trigger of about 8&times;. The pin therefore\n'
     '          stands, and no derived row moved as a result of this update.\n'),

    # the mean is now dragged up by SandboxAQ as well
    ('<tr><td>mean</td><td class="num">37.7&times;</td><td>dragged up by Zhipu 324&times;, Baichuan 149&times;</td></tr>',
     '<tr><td>mean</td><td class="num">37.7&times;</td><td>dragged up by Zhipu 324&times;, SandboxAQ 315&times;, Baichuan 149&times;</td></tr>'),
]


def main():
    print("polishing pinned-multiple copy...")
    apply("index.html", INDEX)
    apply("methodology.html", METHODOLOGY)
    print("done")


if __name__ == "__main__":
    main()
