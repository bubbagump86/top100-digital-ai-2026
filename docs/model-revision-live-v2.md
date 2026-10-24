# Model revision — "live list" edition

**DECISION: Option A adopted** (anchored axis bounds + pinned peer multiple +
the missing-ARR rule left unchanged). Option B — the hybrid missing-ARR rule —
was tested and **deferred**; see §4 for why.

Shipped in the `live-v2` policy (`data/model_config.json`).

**Status: this document is the decision record for the revision.** The live
site runs the revised model. The proposal it describes was reviewed on
2026-10-24; the numbers below are the ones that were measured at review time.

---

## 1. Why revise at all

The list is intended to be **live** — re-scored as valuations and ARR move.
That changes the requirements on the model in three ways the current one does
not meet:

| Requirement | Current model | Problem |
|---|---|---|
| Scores should mean something stable, not "position in today's list" | bounds = the sample's own min/max | one new record-holder re-bases everyone |
| An update should move the list only when a company actually changed | recomputed bounds | a new floor reshuffles ranks for unrelated reasons |
| The list should be auditable across editions | no changelog, no fixed anchors | no way to tell a real move from a re-base |

### The churn, measured

Simulated data events, re-scored with the real engine
(`scripts/compare_live.py`). "Rank churn" = companies moving ≥3 places.

| Data event | Current model: median score shift | rank churn | Anchored: median shift | rank churn |
|---|---:|---:|---:|---:|
| New company enters, $1M ARR (new floor) | **+7.22** | **39** | 0.00 | **0** |
| New company enters, $5M ARR | +2.53 | **13** | 0.00 | **0** |
| New company enters, $300B ARR (new ceiling) | −1.33 | **10** | 0.00 | **0** |
| Reworkd AI ARR slips $10M → $5M | +2.53 | **13** | 0.00 | **0** |
| Anthropic ARR revised $100B → $80B | +0.31 | 2 | 0.00 | **0** |
| Anthropic ARR revised $100B → $150B | −0.52 | 1 | 0.00 | **0** |
| OpenAI ARR $50B → $120B | −0.24 | 0 | 0.00 | 0 |

Two things stand out:

1. **The current model reshuffles the mid-field for invisible reasons.** A
   company joining with $5M ARR moves the median score by 2.53 points — nobody
   would report that — and still reorders 13 companies by 3+ places. The list
   is dense near the bottom (#91 17.52, #92 17.52, #93 17.51), so any
   perturbation at all reorders it.
2. **The floor is the fragile end; the ceiling is safe.** The log transform
   already compresses the top, so a leader's ARR revision moves almost
   nothing (0.31 points). It is a new *minimum* that re-bases everyone.

Anchoring does **not** freeze the list: OpenAI overtaking Anthropic still
happens correctly. It removes spurious movement while preserving real
movement — which is exactly what a live ranking needs.

---

## 2. The three changes, and which combination to take

### (a) Anchored axis bounds

```
z_val = (log10(valuation) - log10(0.1))  / (log10(1000)  - log10(0.1))
z_arr = (log10(ARR)      - log10(10))   / (log10(100000) - log10(10))
```

Fixed bounds: valuation **$0.1B – $1,000B**, ARR **$10M – $100,000M**.
Published as policy, not derived from the sample.

### (b) Pinned peer multiple

The peer EV/Revenue multiple is currently the **median of the pure-play pool
recomputed on every run** — itself a sample-dependent number. Adding one
company at 90.9× moves the median from 20.00× to 20.42× and shifts every
derived megacap row. Pinning it at **20×** (with periodic review) removes
that second source of drift. *The ranking is already proven stable from 10× to
40×, so pinning costs nothing.*

Note: pinning changes nothing today — the computed median is exactly 20.00×.
It is insurance for future pool changes.

### (c) The missing-ARR rule

Currently: a company with no ARR gets the ARR axis at 0 **and keeps its 50%
weight**, so its composite is `0.5 × z_val`. That penalises the same fact
twice — once by the axis reading 0, once by the weight.

The alternative — drop the axis, let the remaining axis carry full weight
(`z_val`) — is better for a pre-revenue AI lab, but **wrong for a
market-cap proxy**: a proxy's valuation *is* the whole company, so giving it
full weight on that number rewards size with zero AI content. Under the naive
rule, Palantir ($350B market cap, no disclosed AI revenue) enters at **#6**.

**Proposed hybrid:**

| Row type | valuation is… | missing ARR is scored |
|---|---|---|
| Pure-play AI, no ARR disclosed | an **AI** valuation | full weight → `z_val` |
| Market-cap proxy, no AI revenue | a **whole-company** number | keep 50% → `0.5 × z_val` |

---

## 3. The two options on the table

### Option A — stability only (recommended default)

`--anchored --fixed-multiple 20 --missing-rule zero`

| | |
|---|---|
| Rank movement | **88 of 100 unchanged**, 4 up, 8 down |
| Spearman ρ vs current | **+0.9997** |
| Biggest mover | Midjourney #83 → #77 (a tie broken differently) |
| Score range | max 100.00 → 99.81; median 30.92 → 30.83 |
| Churn under all 7 data events | **0** |
| Top 11 across multiples 10×–40× | **stable** |

This is essentially a no-op on the ranking today, and it removes 100% of the
spurious churn. The only visible change is Anthropic 100.00 → 99.81, because
the valuation ceiling is now $1T rather than "the largest valuation in the
list".

### Option B — stability + the missing-ARR fix

`--anchored --fixed-multiple 20 --missing-rule hybrid`

| | |
|---|---|
| Rank movement | 12 unchanged, 8 up, 80 down (the 8 up push the rest) |
| Spearman ρ vs current | +0.9374 |
| New entrants to the top 15 | **DeepSeek #11, Thinking Machines Lab #12, SSI #14, Reflection AI #15** |
| Pushed down | Baidu #11 → #13, Cognition #16 → #21, Inflection #95 → #50, Magic AI #98 → #57 |
| Churn under all 7 data events | **0** |
| Top 11 across multiples 10×–40× | **stable** (11/11 names present at every multiple) |

Pre-revenue frontier labs gain a fairer position: DeepSeek's valuation *is* an
AI valuation and the market has priced it at $50B, so scoring it on the ARR
axis it has not got yet (and halving the credit for not having it) counts the
same fact twice.

**The trade Option B accepts, stated plainly:** a pre-revenue lab outranks a
revenue-generating peer of similar valuation. DeepSeek ($50B, no revenue)
scores 67.47 and sits above Cognition ($48B, $492M ARR) at 54.67. That is
defensible — the $50B *is* the market's forward view — but it is a real change
in what the list rewards.

---

## 4. A caveat on Option B: the hybrid rule increases scale sensitivity

The two changes interact, and this did not show up until the variant was run
through the existing sensitivity harness.

| Scale variant | Current model ρ | Option A ρ | Option B ρ |
|---|---:|---:|---:|
| B — raw + min-max | +0.967 | +0.884 | **+0.811** |
| C — raw + z-score | +0.799 | +0.854 | **+0.698** |
| D — raw + percentile | +0.980 | +0.979 | +0.982 |

Under Option B the log transform is doing much more work. DeepSeek is #11
under log-min-max and **#51** under raw min-max, because the hybrid rule
gives a pre-revenue lab full weight on the valuation axis — and how much that
is worth depends entirely on how the valuation axis is scaled. Option A keeps
the log transform's role where it was.

(These ρ figures are not directly comparable to the published ones: the
published sensitivity analysis runs on the top-100 slice with sample bounds,
whereas these run the variants with the same bounds as the model they are
being compared against.)

---

## 5. Re-anchor policy (required if (a) is adopted)

Anchored bounds will eventually be breached. Proposed policy:

1. **Bounds are fixed policy**: valuation $0.1B – $1,000B, ARR $10M – $100,000M.
2. **Bounds are reviewed quarterly**, and revised only if a company has
   breached a bound by more than one third of the axis span — i.e. an anchor
   that is about to be crossed rather than one that has been crossed.
3. **Scores are not clipped.** If a company exceeds a bound, its z-score
   exceeds 1 and its composite may exceed 100. Clipping would peg Anthropic
   and OpenAI at the same value once OpenAI passes $100B ARR and destroy the
   discrimination the axis exists to provide. A score above 100 is a signal
   that the anchor is stale.
4. **Every revision is logged** with the date, the old bounds, the new
   bounds, and the reason. Scores are otherwise comparable across editions.

---

## 6. Peer multiple policy (required if (b) is adopted)

1. The peer multiple is **pinned at 20×** — the pure-play median as measured
   on the 2026-10 edition (n=81, IQR 15–40×).
2. It is **re-reviewed quarterly** against the current pure-play pool. The
   trigger for a revision is the same as for the axis bounds: the pool median
   must have moved more than one third of the IQR (≈8×) from the pinned
   value, not merely because one company joined.
3. The published methodology keeps showing the *current* pool distribution
   alongside the pinned value, so the pinned multiple can never silently drift
   away from what the data says.
4. The stress test (10×–40×) is re-run on every re-review and published, as
   it is today.

---

## 7. What was decided

1. **Option A adopted.** Anchored axis bounds ($0.1B–$1,000B valuation,
   $10M–$100,000M ARR) and the peer multiple pinned at 20×. The missing-ARR
   rule is unchanged (`zero`).
2. **Option B deferred.** The hybrid missing-ARR rule is not shipped. It was
   a genuine improvement in fairness to pre-revenue labs, but it makes the
   ranking materially more dependent on the log transform (§4) and it is a
   separable decision from the stability work. It can be revisited on its own
   — the machinery is in `scripts/score.py --missing-rule hybrid`.
3. **Bounds** as proposed above.
4. **Multiple** pinned at 20×, re-reviewed quarterly.

### What changed in the published list

| | Before | After |
|---|---|---|
| Anthropic | 100.00 | **99.81** |
| OpenAI | 95.56 | 95.37 |
| Microsoft | 93.16 | 92.97 |
| Alphabet | 90.87 | 90.69 |
| Amazon | 88.89 | 88.71 |
| Meta | 86.46 | 86.29 |
| SpaceXAI | 83.22 | 83.05 |
| Alibaba | 78.13 | 77.97 |
| Databricks | 76.71 | 76.55 |
| Tencent | 75.04 | 74.89 |
| Baidu | 66.48 | 66.37 |

**88 of 100 ranks unchanged**, 4 up, 8 down — the movers are ties being broken
differently (Midjourney #83 → #77 is the largest, a tie at 21.24/21.29). The
top 11 membership is unchanged, and still stable across every multiple from
10× to 40×.

The only visible change a reader will notice is Anthropic's score: 99.81
rather than 100.00, because the valuation anchor is $1,000B and Anthropic is at
$965B. That is the intended behaviour of an anchored scale — a score of 100
would mean "at the top of the scale", and a score above 100 would mean "past
the anchor".

---

## 8. How to reproduce

```bash
# the shipped model (reads data/model_config.json)
python scripts/score.py
python scripts/sensitivity.py
python scripts/multiple_check.py

# the deferred Option B, for reference
python scripts/score.py --variant live-v2 --axis anchored --peer-multiple 20 --missing-rule hybrid
python scripts/sensitivity.py   --input data/variants/live-v2/ranked.json --out data/variants/live-v2/sensitivity.json
python scripts/multiple_check.py --input data/variants/live-v2/ranked.json --out data/variants/live-v2/multiple_check.json

# comparison + churn simulation
python scripts/compare_live.py --variant data/variants/live-v2/ranked.json \
    --variant-flags "--axis anchored --peer-multiple 20 --missing-rule hybrid" \
    --out data/variants/live-v2/comparison.json
```

A `--variant` run writes to `data/variants/<name>/` and **cannot** touch
`data/ranked.json`, `data/ranked.csv` or the site's `ranked.json`. Variant
outputs are git-ignored — they are review artifacts, not site content.
