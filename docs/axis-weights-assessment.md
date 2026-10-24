# Axis weights: should ARR be weighted above valuation?

**Date:** 2026-10-24
**Status:** assessed. **Recommendation: keep 50/50.** No change to the shipped
weights; the shipped model is unchanged.
**Supersedes:** nothing.

---

## 1. The question

The composite is `S = 100 * (w_val * z_log(val) + w_arr * z_log(arr))`,
shipped at 50/50. The proposal was 0.40 valuation / 0.60 ARR — "revenue is the
hard number, valuation is a negotiated round price".

Everything below is measured with the real engine, not estimated.

## 2. The finding that reframes the question

For a pure-play, valuation and ARR are **not independent** — valuation *is*
ARR × a multiple. So the composite can be rewritten exactly:

```
z_val = z_arr + (log10(multiple) - 1) / 4

S = 100 * ( z_arr  +  w_val * (log10 m - 1) / 4 )
           \_ ARR _/   \_ multiple premium _/
```

Verified against the live dataset: max error 0.0001 across the sampled
pure-plays (`scripts/decompose_the_composite.py`).

Two consequences:

1. **The ARR level term carries weight 1.0 at every split.** Re-weighting
   towards revenue does not shift the balance towards revenue level.
2. **The valuation axis contributes only the multiple premium**, at
   `w_val / 4` per decade of multiple.

Variance decomposition across the 75 pure-plays, shipped weights:

| Term | Variance | Share of total |
|---|---|---|
| ARR level | 0.03176 | 110% |
| Multiple premium | 0.00208 | **7%** |
| Total | 0.02895 | — |

(The sum exceeds 100% because the two terms are negatively correlated: the
biggest-revenue companies trade at the lowest multiples.)

**So the model is already overwhelmingly an ARR-level model.** "50/50" is not
a 50/50 in substance, and the lever the question pulls moves a term that is
7% of the composite's variance, not 50%.

The pure-play multiple range is 5.0× (Otter.ai) to 323.5× (Zhipu), median
22.0× — 1.81 decades, worth 22.6 score points of premium at the shipped
weights and 18.1 points at 0.40/0.60.

## 3. What 0.40 / 0.60 actually does

`scripts/weight_assessment.py`, `scripts/weight_rule_matrix.py`.

| Split | ρ vs 50/50 | Rows moving 5+ | Rows moving 10+ | Top 13 unchanged | Top 11 stable at 10–40× |
|---|---|---|---|---|---|
| 0.50 / 0.50 (shipped) | 1.000 | 0 | 0 | 13/13 | 11/11 |
| 0.45 / 0.55 | 0.995 | 12 | 0 | 13/13 | 11/11 |
| **0.40 / 0.60** | **0.981** | **28** | **12** | **13/13** | **11/11** |
| 0.35 / 0.65 | 0.953 | 37 | 15 | 13/13 | 11/11 |
| 0.30 / 0.70 | 0.911 | 42 | 21 | 13/13 | 11/11 |

**The head does not move.** The top 13 is identical at every split; the top 11
survives the peer multiple at every multiple from 10× to 40×; the valuation
cap still binds on exactly one row (Baidu) with Notion AI still at the cap.

All movement is mid-table, where scores are densely packed — 28 rows move five
or more places on a score change of at most four points. Midjourney moves 23
places on a 4.25-point score change.

### Who moves

| Company | 50/50 | 40/60 | Why |
|---|---|---|---|
| Midjourney | #82 | #59 | $500M ARR, **no valuation** — pure revenue evidence |
| Otter.ai | #87 | #77 | $100M ARR, $0.5B valuation |
| Manus AI | #36 | #29 | $450M ARR at a below-median 8.9× multiple |
| Palantir | #26 | #36 | proxy row: no AI revenue disclosed, ARR axis reads 0 |
| ByteDance | #28 | #39 | proxy row |
| Samsara | #52 | #66 | proxy row |
| SandboxAQ | #72 | #83 | 315× multiple |
| Sakana AI | #74 | #81 | 90× multiple |
| Baichuan | #81 | #92 | 149× multiple |
| Safe Superintelligence | #50 | #63 | pre-revenue |
| Thinking Machines Lab | #42 | #55 | pre-revenue |
| Moonshot AI | #58 | #74 | pre-revenue |
| DeepSeek | #41 | #54 | pre-revenue |

Two directions are visible and both are legitimate:

- **Small narrative-driven companies fall** (SandboxAQ, Sakana, Baichuan) —
  their valuation marks are 90–315× ARR. This is the bias the proposal
  correctly identifies, and it is real.
- **Every row without disclosed ARR falls** (Palantir, ByteDance, Samsara,
  Schrodinger out of the top 100; SSI, Thinking Machines, Moonshot, DeepSeek,
  Reflection AI, Luma AI, AMI). Under the "missing ARR reads 0" rule a row
  with no revenue is scored `w_val * z_val` only, so raising the ARR weight
  shrinks the only axis it has. That is a **disclosure artefact**, not a
  statement about those companies.

## 4. The weights and the missing-ARR rule are not independent

The rule dominates the weight. `scripts/weight_rule_matrix.py`:

| Case | w_val/w_arr | Rule | Palantir | ByteDance | Samsara | SSI | Top 12 kept |
|---|---|---|---|---|---|---|---|
| Shipped | 0.50/0.50 | zero | #26 | #28 | #52 | #50 | 12/12 |
| Proposed split, current rule | 0.40/0.60 | zero | #36 | #39 | #66 | #63 | 12/12 |
| Proposed split + Option B | 0.40/0.60 | hybrid | #43 | #46 | #72 | **#14** | 10/12 |
| Proposed split + axis dropped | 0.40/0.60 | alone | **#5** | **#7** | **#17** | **#16** | 10/12 |

Changing the weight without deciding the rule moves you into an arbitrary
point in a two-dimensional policy space. The weight change is also not free of
side effects on the scale choice: correlation with the raw min-max variant
falls from 0.919 to 0.872 (and to 0.808 at 0.30/0.70), because ARR is the
power-law axis and weighting it more makes the raw scale matter more. The log
transform becomes **more** load-bearing, not less.

## 5. The bigger lever is not the weight

If the concern is that valuation is doing too much work, the largest single
valuation-weighting error in the list is not the axis weight — it is a data
defect. `scripts/compare_levers.py`:

| Lever | Cohesity | Talkdesk | Rows moving 3+ |
|---|---|---|---|
| A. re-weight to 0.40/0.60 | #22 → #21 (48.09 → 49.35) | #30 → #28 | 39 |
| B. make the proxy tier policy-compliant | **#22 → #89** (48.09 → 20.89) | **#30 → #69** | 2 |

Cohesity and Talkdesk are `proxy` basis, which the published model says must
score 0 on the ARR axis — but both carry their **total company ARR** ($1.5B
and $250M) on the AI-ARR axis. Cohesity's #22 is bought almost entirely by
that: its market cap is a backup-software franchise, not an AI valuation.

Lever B is worth 67 rank places on that row. Lever A is worth about one.
It is also a targeted correction rather than a policy change, and it leaves
Samsara, Palantir, ByteDance and Schrodinger where they are.

## 6. Provenance: is the ARR axis actually the hard one?

`scripts/arr_provenance.py`. Partly. At the head of the list, yes:

| Company | ARR source |
|---|---|
| Anthropic | New York Times, Sep 2026 |
| OpenAI | Financial Times, confirmed by Reuters |
| SpaceXAI | SpaceX SEC filings |
| Baidu | Q2 2026 results |
| Alibaba | Group results, Aug 20 2026 |
| ServiceNow | Q2 2026 results |
| Databricks | Company announcement |
| Zhipu | IPO prospectus |

But roughly **57 of 100 ARR figures are third-party or press estimates** —
VAST Data, Scale AI, Cohesity, Perplexity, Midjourney, Glean, Notion AI,
Talkdesk, Sierra, Hugging Face, Legora, Together AI, DeepL, Invisible
Technologies, Replit, EvenUp, Decagon and more are all "press estimates". Four
rows (Microsoft, Alphabet, Tencent, Mistral) are our own segment estimates.
Only Snowflake's figure is company-disclosed but stale.

So "revenue is the hard number" is true at the top of the list and largely
false in the middle of it.

## 7. Recommendation

**Keep 50/50.** Reasons, in order of weight:

1. The lever is small. The valuation axis is 7% of the composite's variance
   across pure-plays, not 50%. The premise behind the change is already
   substantially satisfied by the model.
2. The change's main side effect is a disclosure penalty. It cuts every row
   without disclosed ARR by 20% on the axis it has — including Palantir and
   ByteDance dropping out of the top 30, and four of the seven companies that
   only just entered the list (Luma AI, AMI) sinking towards the bottom.
3. It interacts with the missing-ARR rule, which dominates it. Deciding the
   weight without deciding the rule is arbitrary.
4. It deepens the model's dependence on the log transform at exactly the
   point where that dependence has been questioned.

**What to do instead, in priority order:**

1. **Fix the proxy tier** (Cohesity, Talkdesk). It is a data defect worth 67
   places on one row, against the re-weight's one. This is the real answer to
   "valuation is over-weighted": remove the rows where the valuation axis is
   least meaningful rather than shrinking the axis for everyone.
2. **Settle the missing-ARR rule** as a deliberate, coupled decision. It
   dominates the weight and is currently deferred. The matrix above shows
   what each option does.
3. **If a revenue tilt is still wanted**, 0.45 / 0.55 is nearly free — ρ
   0.995, no row moves ten places, top 13 unchanged. Take it at a quarterly
   policy review, not mid-edition, because it changes every score and breaks
   comparability with previous editions.

**Also done regardless of the decision:** the weights were hardcoded in three
scripts (`score.py`, `sensitivity.py`, `multiple_check.py`). They now live in
`data/model_config.json` as policy, read by all three, with
`--weight-val` / `--weight-arr` overrides for review work. The shipped output
is byte-identical.

## 8. Files

| File | Role |
|---|---|
| `data/model_config.json` | the weights, as policy, alongside the axis bounds and peer multiple |
| `scripts/weight_assessment.py` | re-runs the pipeline across splits and reports churn → `data/weight_assessment.json` |
| `scripts/weight_rule_matrix.py` | weight × missing-ARR-rule matrix |
| `scripts/decompose_the_composite.py` | proves the ARR-level / multiple-premium decomposition and the variance split |
| `scripts/arr_provenance.py` | classifies the provenance of every ARR and valuation figure |
| `scripts/compare_levers.py` | re-weight vs proxy-tier fix, head to head |
| `scripts/inspect_weight_movers.py` | row-level detail on the biggest movers |
