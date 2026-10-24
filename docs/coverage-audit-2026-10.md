# Coverage audit and admission-rule decision — 2026-10 edition

**Date:** 2026-10-24
**Status:** applied, published
**Supersedes:** nothing. Adds to `docs/model-revision-live-v2.md` (the model policy),
which is unchanged by this work.

---

## 1. What the problem was

The 2026-10 edition was compared against a 39-name third-party AI company list
(`data/coverage_watchlist.json`). The result:

| Disposition | Count |
|---|---|
| Ranked in the Top 100 | 18 |
| Folded into an existing roll-up row, but never written down | 2 |
| **No disposition at all** | **19** |

The 19 were the real defect. They were not excluded, not folded, not ranked —
they were simply **absent**. A ranking that only publishes what it included has
an invisible hole: a company can be missing because nobody checked, and nothing
in the pipeline can detect that.

Two further names (Google DeepMind, Microsoft Research Asia) were genuinely
rolled into Alphabet and Microsoft, but that roll-up existed only in prose on the
site. The dataset did not record it, so no audit could ever confirm it.

## 2. The fix: the coverage audit is now a pipeline step

New script `scripts/coverage.py`, new data file `data/coverage_watchlist.json`.

The rule the audit enforces:

> Every name on a watchlist must resolve to **exactly one** disposition —
> `RANKED`, `FOLDED` (into a roll-up row), or `EXCLUDED` (with a published
> reason). A name that resolves to nothing is a **coverage gap**, and a gap
> blocks publication.

The audit is deterministic and re-runnable:

```
$ python scripts/coverage.py
  watchlist      : 39 names
  RANKED         : 25
  FOLDED         : 2
  EXCLUDED       : 12
  GAP            : 0
  COVERAGE COMPLETE: YES
```

`data/coverage.json` is the machine-readable output and is rendered on the
overview page, so the published numbers can never drift from the audit that
produced them.

## 3. The admission rule

Eligibility stopped being a judgement call and became a stated rule. A company
is admitted if it is:

1. **Pure-play digital AI** — the AI business *is* the company, so its market or
   transaction valuation is already an AI valuation. → `actual`
2. **AI-attributed** — a diversified company that *discloses* AI-attributed
   revenue. → `derived`
3. **Market-cap proxy** — a company with a material AI business that discloses
   no AI revenue line, where a market-cap proxy is defensible. → `proxy`
   (flagged as the weakest evidence in the list)

A software company is **excluded** when AI is neither disclosed nor material —
the same test that excludes Apple. Scoring Datadog, AvePoint or Workato on their
full market caps would make the valuation axis a measure of observability and
backup franchises rather than AI.

### The 21 resolved names

**Added to the ranking (7)**

| Company | Basis | Valuation | AI ARR | Rank |
|---|---|---|---|---|
| Snowflake (Cortex AI / Snowflake Intelligence) | derived | $2.0B implied (from $100M AI ARR × 20×) | $100M (company-stated, Dec 2025, stale) | #59 |
| Manus AI | actual | ~$4.0B (Bloomberg, Oct 2026) | $450M (reported range $400–500M, Jun 2026) | #36 |
| Wonderful AI | actual | $5.0B (Sep 2026 Series C) | ~$70M run-rate (Sep 2026) | #49 |
| SandboxAQ | actual | $5.6B (company-confirmed, Dec 2024) | $17.8M (single-source estimate) | #72 |
| Sakana AI | actual | $2.7B (company-confirmed, Nov 2025) | ~$30M (single-source estimate) | #74 |
| Luma AI | actual | $4.0B (CNBC, Nov 2025) | not usable → ARR axis 0 | #93 |
| Advanced Machine Intelligence (AMI) | actual | ~$4.53B (Reuters, Mar 2026) | pre-revenue → ARR axis 0 | #91 |

**Folded into roll-up rows (2)**

| Company | Folded into | Host rank |
|---|---|---|
| Google DeepMind | Alphabet (Gemini + Cloud AI) | #4 |
| Microsoft Research Asia (MSRA) | Microsoft (AI business) | #3 |

**Excluded with a published reason (12)**

| Company | Reason |
|---|---|
| Datadog | No AI revenue line (management explicitly declines to size it) and AI is not material — the Apple test |
| Workato | No AI revenue disclosed; last confirmed valuation is $5.7B from Nov 2021, too stale to publish; ~$200M revenue is below list scale |
| AvePoint | No AI revenue line in Q2 2026; AI is a positioning layer on a SaaS-backup core |
| Prometheus (prometheus.ai) | Physical AI / hardware-industrial output modality. Not the open-source monitoring project |
| Preferred Networks (PFN) | AI accelerator silicon (PES / MN-P) — semiconductor-first. Also *not* TSE-listed, contrary to some third-party lists |
| Periodic Labs | Autonomous robotic wet labs — physical-AI delivery; pre-revenue |
| Enigma | Robotics foundation models (embodied AI); name ambiguous, no disclosed valuation or ARR |
| BeyondMath | $18.5M seed; no valuation, no revenue — below the evidence threshold |
| Cantina Labs | $16.5M raised; no valuation, no revenue — below the evidence threshold |
| Openmind Research Institute | Not a company — a non-profit research institute (Sutton, Bowling) funded by Huawei Canada |
| BottleCap AI | $7.5M seed; no valuation, no revenue — below the evidence threshold |
| Causal Labs | $6M seed; no valuation, no revenue — below the evidence threshold |

## 4. How third-party estimates are treated

A third-party revenue estimate is used as an input **only** when it is
(a) above this list's $10M ARR anchor and (b) the best available figure. It is
then published with its source and an explicit confidence flag.

Below the anchor it is not used at all — Luma AI's ~$8M Sacra estimate is
22 months old and under the anchor, so that row's ARR axis reads 0 under the
missing-ARR rule instead. Where two sources conflict we publish the
conservative figure and name the conflict; where a figure is single-sourced we
say so (Manus AI's ~$4B valuation, SandboxAQ's revenue estimate, Sakana AI's
revenue estimate).

## 5. Effect on the model — none, by design

The pinned peer multiple and the anchored axis bounds did their job. Adding
seven rows to a 107-row input:

- **No existing row's score changed at all.** Every rank change is pure
  displacement: the seven lowest-scoring rows fell out of the top 100.
- The peer pool grew from n=81 to n=85 and its computed median moved from
  20.00× to 20.83×. The retune trigger is a move of more than one third of the
  IQR (~8×), so the pin at 20.0× stands and no derived row moved.

### Rows that left the Top 100

| Was | Company | Score |
|---|---|---|
| #94 | Augment Code | 16.90 |
| #95 | Suno | 16.26 |
| #96 | Inflection AI | 16.26 |
| #97 | Roboflow | 15.69 |
| #98 | Magic AI | 14.70 |
| #99 | Inworld AI | 14.70 |
| #100 | Pika | 14.37 |

This is what a Top 100 does. The seventh-lowest new entrant (AMI, 20.70) sits
above all seven.

## 6. Robustness after the update

| Variant | Spearman | Kendall | Rows < 5/100 |
|---|---|---|---|
| A — log + min-max (shipped) | +1.000 | +1.000 | 0 |
| B — raw + min-max | +0.919 | +0.806 | 87 |
| C — raw + z-score | +0.850 | +0.774 | 90 |
| D — raw + percentile | +0.981 | +0.910 | 0 |

The top 12 are identical under the shipped model and variant D. The top 11
names are unchanged at every multiple from 10× to 40×.

## 7. Files

| File | Role |
|---|---|
| `data/coverage_watchlist.json` | the external watchlist, version-controlled |
| `scripts/coverage.py` | the audit — every name must resolve to one disposition |
| `data/coverage.json` | machine-readable audit output, rendered on the overview page |
| `scripts/apply_coverage_2026_10.py` | the data patch (idempotent) that adds the 7 rows, 2 roll-ups and 12 exclusions |
| `scripts/patch_watchlist.py` | explicit name mappings between the watchlist and our rows |
| `scripts/patch_site_2026_10.py` | site copy updates for the new figures (asserts each edit fires once) |
| `scripts/add_coverage_sections_2026_10.py` | methodology §2b, the overview coverage card, the exclusions note |
| `scripts/polish_pin_2026_10.py` | fixes the pinned-vs-computed median distinction in the overview panel |
| `scripts/diff_ranking.py` | compares two `ranked.json` files — membership and rank moves |
| `scripts/scan_numbers.py` | finds hardcoded figures in the site HTML that a data change may have invalidated |

## 8. Open item, not changed here

Two existing rows score their **total** company ARR on the AI-ARR axis despite
being `proxy` basis, which the published model says should read 0:
Cohesity ($1.5B total ARR, rank #22) and Talkdesk ($250M total ARR, rank #30).
Every other proxy row (Palantir, Samsara, Schrodinger, ByteDance) has a null
ARR and therefore reads 0. This is a genuine inconsistency in the existing data,
not a consequence of the coverage work, so it was left alone rather than changed
silently. Correcting it would move Cohesity from #22 to roughly #70 and Talkdesk
from #30 to roughly #75.
