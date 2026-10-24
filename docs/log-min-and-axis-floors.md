# The log_min question: does a negative valuation floor distort the measure?

**Date:** 2026-10-24
**Status:** answered. One change adopted (the axis floor clamp), one stale
figure fixed. **No shipped score changed.**
**Supersedes:** nothing.

---

## The question

The valuation axis is anchored `log10` from **−1.00** ($0.1B) to 3.00
($1,000B); the ARR axis from **+1.00** ($10M) to 5.00 ($100B). Does the
negative `log_min` on the valuation axis distort the measure?

Answer: **the sign does not. The origin does — and the question exposed a
real monotonicity break on the ARR axis, which is now fixed.**

All measurements below come from `scripts/log_min_probe.py`, which re-runs
the real engine.

---

## 1. The sign is inert — but the origin is not

A z-score is invariant to affine shifts of its axis. Shifting the valuation
axis from log [−1, 3] to log [0, 4] — same 4-decade span, same data,
different origin — changes every `z_val` by exactly 0.25.

Measured: every row with a valuation loses 12.5 points (0.25 × the 0.5
weight × 100). Every row **without** one loses nothing, because a missing
valuation reads 0 and keeps its weight. So the no-valuation cohort rises
relative to the rest:

| | shipped | axis origin shifted to 0 |
|---|---|---|
| rows whose rank changed | — | **55 of 97** |
| Midjourney | #82 | **#43** |
| Otter.ai | #87 | #74 |
| Schrodinger | #95 | #100 |

**So the valuation axis's origin is a de facto, undocumented lever over where
the no-valuation cohort sits.** That is worth knowing and worth stating; it
is not a distortion, because the treatment of a missing axis (read 0, keep the
weight) is applied consistently to both axes.

## 2. The two axes are not anchored symmetrically

| Axis | Bounds | z range the data uses | Spread of z |
|---|---|---|---|
| Valuation | $0.1B – $1,000B (log −1 → 3) | [0.175, 0.996] | **0.821** of the range |
| ARR | $10M – $100,000M (log 1 → 5) | [0.063, 1.000] | **0.937** of the range |

Across the 88 rows carrying both axes: σ(z_val) = 0.2059, σ(z_arr) = 0.2178,
**ratio 0.945**. Valuation is **5.5% less dispersed than ARR**.

That is a real, mild tilt towards revenue — and it comes from the *anchoring*,
not the weights. It is roughly a quarter of the size of the 0.40/0.60 weight
change discussed in `docs/axis-weights-assessment.md`, and it exists
independently of it. It is the price of fixed bounds: anchoring to the
sample's own extremes removes the compression but re-bases every score on
every data update (methodology §5).

## 3. The floor is protective, not distorting — and the ARR axis lacked it

Here is the real finding. Under the "missing ARR reads 0" rule, a company with
**no** ARR is scored `z_arr = 0`. A company with a **small** ARR was scored
`z_arr < 0` — meaning "some revenue" ranked *below* "no revenue".

Measured, with probe rows that score inside the top 100:

| Probe row | z_val | z_arr | score |
|---|---|---|---|
| $10B valuation, **$5M ARR** (below the $10M floor) | +0.5000 | **−0.0753** | **21.24** |
| $10B valuation, **no ARR** | +0.5000 | — | **25.00** |
| $0.05B valuation (below the $0.1B floor), $1B ARR | **−0.0753** | +0.5000 | **21.24** |
| No valuation, $1B ARR | — | +0.5000 | **25.00** |

**Both inversions were live in the model.** A company with $5M of ARR scored
3.76 points *below* a company with no ARR at all, and a company with a $50M
valuation scored below one with no valuation.

No current row is affected — the smallest ARR in the list is $17.8M
(SandboxAQ), the smallest valuation is $0.5B (Otter.ai) — but on a live list
the first very small company to join would trip it.

### The fix (adopted)

`data/model_config.json` → `"axis_floor_clamp": true`. A value **below** an
axis floor reads **0**, exactly like a missing value. The top end is not
clamped: a score above 100 remains the signal that an anchor is stale.

With the clamp, the same probe rows give:

| Probe row | z_arr | score |
|---|---|---|
| $10B valuation, $5M ARR | **+0.0000** | **25.00** |
| $10B valuation, no ARR | — | **25.00** |

Tied, not inverted. "No signal" and "signal below the usable range" now score
the same, which is the intended reading.

**This changes no shipped score** — verified: `data/ranked.json`,
`data/ranked.csv`, `ranked.json`, `data/sensitivity.json` and
`data/multiple_check.json` are all byte-identical after the change. It removes
a hazard for future editions rather than altering the current list.

## 4. What the negative `log_min` actually buys

Both fixed bounds were originally pinned to a single company: **Reworkd AI sat
at exactly $0.1B valuation and $10M ARR — the two floors at once.** Reworkd
has since fallen out of the top 100, so the floors now sit above the bottom
of the list. That is the fixed-bounds design working exactly as intended: the
axis did not move when the composition did.

The $0.1B–$0.5B band (0.699 unused decades) is where the negative part of
`log_min` lives, and it is load-bearing:

- Raise the floor to $1B and Otter.ai's `z_val` goes negative — a **real**
  company with a $0.5B valuation would rank below companies with no
  valuation mark at all.
- With the $0.1B floor, the smallest real valuation sits at `z_val = 0.175`
  and no real company can go negative on the valuation axis.

So the negative `log_min` is not a distortion. It is the thing that stops the
valuation axis from inverting, and it separates "no valuation disclosed"
(z = 0) from "a small valuation" (z > 0).

## 5. Two stale figures fixed along the way

- **Methodology §4** cited Reworkd AI as the smallest ARR in the list
  (10,000× below Anthropic). Reworkd is no longer in the Top 100, so a reader
  could not find it. The example now uses SandboxAQ ($17.8M), the actual
  smallest ARR in the list — a 5,600× span, not 10,000×.
- **Methodology §8** quoted OpenAI's z-scores as 0.882 / 0.912. Those are
  from an older edition; the current values are 0.983 / 0.925.

## 6. How much room is left — and the one tripwire that is close

`scripts/anchor_headroom.py`.

All four bounds trace to two companies at the time of the pin: **Reworkd AI
set the two floors** ($0.1B valuation, $10M ARR) and **Anthropic set the two
ceilings** ($1,000B valuation, $100,000M ARR). Reworkd has since fallen out
of the Top 100, so the headroom is asymmetric: dead space at the bottom,
almost none at the top of ARR.

| Bound | Bound | Nearest row | Value | Re-anchor trigger | Margin |
|---|---|---|---|---|---|
| Valuation ceiling | $1,000B | Anthropic | $965B | $21,544B | 22.3× |
| ARR ceiling | $100,000M | Anthropic | $100,000M | $2,154,435M | 21.5× |
| Valuation floor | $0.1B | Otter.ai | $0.5B | $0.0046B | 107.7× |
| ARR floor | $10M | SandboxAQ | $17.8M | $0.46M | 38.3× |

Every re-anchor margin is enormous. **But the policy has a second, tighter
tripwire**: scores are not clipped, so a score above 100 is the signal that
an anchor is tight. On the ARR ceiling that flag is the **binding** one:

> With Anthropic's valuation at $965B, the #1 score crosses 100 when
> Anthropic's ARR passes **$103.7B** — **1.037×** its current run-rate —
> whereas the re-anchor trigger on the same bound would not fire until
> $2.15T.

So on a live list, a ~4% move in Anthropic's ARR makes the top score exceed
100 and the two tripwires point in different directions. Both numbers are now
in `data/model_config.json` under `review_policy`, and the methodology
publishes the margin table.

Widening the ARR ceiling is **not** free: it compresses the ARR axis (at
$200B the ARR axis loses ~7% of its dispersion and the 5.5% tilt toward ARR
in section 2 flips), and it changes every score, breaking comparability with
previous editions. That is the argument for leaving the bounds alone and
letting the quarterly review decide — with the tripwire now written down
rather than remembered.

## 7. Verdict

**Leave the bounds as they are.** The sign is inert, the negative valuation
floor is load-bearing (raising it inverts the axis), the floor clamp now
covers sub-floor values, and every re-anchor margin is 20×–108×. The one
thing worth doing was writing the binding tripwire down, which is now done.

## 8. Files

| File | Role |
|---|---|
| `scripts/log_min_probe.py` | the four measurements above |
| `scripts/anchor_headroom.py` | the margin on each bound, and the score-flag threshold |
| `data/model_config.json` | `axis_floor_clamp` as policy; the score-flag and bounds-provenance tripwires |
| `scripts/score.py` | implements the clamp; `--no-axis-floor-clamp` for review |
| `docs/log-min-and-axis-floors.md` | this record |
