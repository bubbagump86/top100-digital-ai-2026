# Top 100 Digital AI Companies 2026

A standalone, transparent ranking of the top 100 **digital** AI companies in
2026, scored on a normalised composite of **valuation** and **AI-attributed ARR**.

This is not "AI startups" — it covers pure-play digital AI businesses **and**
the AI businesses of the megacaps, on one like-for-like basis. Hardware (AI
silicon, robotics, autonomous vehicles, physical-world AI) is intentionally
excluded. See the [exclusions page](exclusions.html) for the full cut list.

Live site: https://bubbagump86.github.io/top100-digital-ai-2026/
Repository: https://github.com/bubbagump86/top100-digital-ai-2026

## Methodology in 60 seconds

For each company we collect:

- `valuation_usd_b`: an **AI valuation** — either the company's own
  market/transaction valuation (pure-play AI) or a derived figure (see below).
- `arr_usd_m`: **AI-attributed ARR** — for diversified companies, only the
  AI slice, never total company revenue.

Both axes span 5+ orders of magnitude, so we **log-transform** each value and
**min-max rescale** to `[0, 1]` against **fixed bounds** — valuation $0.1B–$1,000B,
ARR $10M–$100B. The composite is the equal-weighted average:

```
S = 100 * (0.5 * z_log(valuation) + 0.5 * z_log(ARR))
```

where `z_log(x) = (log10(x) - log_min) / (log_max - log_min)`.

### Why the bounds are fixed (this list is live)

The list is re-scored as valuations and ARR move. If the bounds were the
minimum and maximum *observed in the current list*, every data update would
re-base every other company's score — and the result would be rank churn that
has nothing to do with any company having changed. We measured it: a company
joining with $5M ARR shifts the median score by 2.53 points (invisible) and
still reorders 13 companies by 3+ places. A $1M entrant reorders 39.

With fixed bounds none of that happens. This does **not** freeze the list —
OpenAI overtaking Anthropic still happens correctly. Anchoring removes spurious
movement while preserving real movement.

Scores are **not clipped**: a company beyond a bound scores above 100, which is
the signal that the anchor is stale. Bounds are reviewed quarterly and revised
only when a company has breached a bound by more than one third of the axis
span; every revision is logged. The policy lives in
[`data/model_config.json`](data/model_config.json), version-controlled with the
data.

### The three-basis model (how big tech fits in)

| Basis | Who | How the valuation is set |
|---|---|---|
| **Pure-play** | Anthropic, OpenAI, Databricks, SpaceXAI, Mistral, Cursor-era AI labs… | The company's own market/transaction valuation. It already *is* an AI valuation. |
| **AI-attributed** | Microsoft, Alphabet, Amazon, Meta, Alibaba, Baidu, Tencent, Salesforce, ServiceNow, Notion AI | `AI ARR × 20×` — the pure-play median EV/Revenue multiple (n=81, IQR 15–40×), **capped at the company's market cap**. Answers *"what would this AI business be worth standalone?"* |
| **Market-cap proxy** | Palantir, Samsara, Schrodinger, ByteDance, Cohesity, Talkdesk | No AI-revenue disclosure, so no AI valuation can be derived. Full market cap used as a flagged proxy; ARR axis scored 0. |

The peer multiple is **pinned at 20×** — the pure-play median as measured on the
2026-10 edition — rather than recomputed on every run. The median is itself a
sample-dependent number: adding one company at 90.9× moves it from 20.00× to
20.42× and shifts every derived megacap row. The pin is re-reviewed quarterly,
and revised only when the pool median has moved more than one third of the IQR
(about 8×) from the pinned value.

**The valuation cap.** A derived AI valuation is a claim about a *part* of a
company, and a part cannot be worth more than the whole. So the valuation axis
is hard-capped:

```
derived AI valuation = MIN( AI ARR × peer multiple , company market cap )
```

Exactly one row binds in the 2026 set — **Baidu**, where the uncapped
derivation ($148.8B) is 543% of its $27.4B market cap. Baidu's valuation axis
is set to $27.4B, the uncapped figure is published alongside it, and the row
is badged as indicative. Notion AI sits exactly at its $6.0B cap (100.0%)
without the cap binding; every other derived row lands between 5.7% and 68.9%
of its market cap. The cap costs Baidu one place (#10 → #11).

Missing data: if one axis is undisclosed it scores 0 (worst observed). If
both are missing the company is dropped.

Full treatment, worked examples, and sensitivity analysis — see
[`methodology.html`](methodology.html), sections 6b and 5b.

## Robustness: what if we didn't log-transform?

The log transform is the most consequential choice in the model, so it's
tested rather than assumed. `scripts/sensitivity.py` re-runs the full
ranking four ways:

| Variant | Spearman ρ vs shipped | Kendall τ | Rows scoring < 5/100 |
|---|---:|---:|---:|
| **A — log + min-max (shipped)** | +1.000 | +1.000 | **0 of 100** |
| B — raw + min-max | +0.937 | +0.831 | **87 of 100** |
| C — raw + z-score | +0.854 | +0.789 | **90 of 100** |
| D — raw + percentile | +0.979 | +0.912 | **2 of 100** |

**The headline is robust**: the top 7 are identical under all four variants,
and the top 12 are identical under the scale-free percentile variant (D).

**But raw min-max would quietly wreck the list.** It correlates +0.937 with
the shipped model, so it looks fine at a glance — yet 87 of 100 rows collapse
below 5/100 (vs 0 under A). Anthropic's $100B ARR owns 100% of the raw axis
range, so every company under ~$1B ARR is crushed to ~0 and becomes
indistinguishable. It also promotes pre-revenue labs (DeepSeek #40→#16,
Thinking Machines #41→#17, SSI #48→#22) purely because "no revenue" wins by
default once everything else is zero.

Percentile (D) is the strongest alternative and agrees even more closely with
the shipped model. We ship log+min-max because it preserves *how much bigger*
one company is than another, which percentile deliberately flattens.

Full write-up: [`methodology.html`](methodology.html) section 5b.
Machine-readable: [`data/sensitivity.json`](data/sensitivity.json).

## Stress-testing the 20× peer multiple

The second-most-consequential number in the model. `scripts/multiple_check.py`
runs five checks.

The multiple is **pinned at 20×** — the pure-play median as measured on the
2026-10 edition — rather than recomputed each run, for the same reason the
axis bounds are fixed: a live list cannot have its derived valuations move
because the composition of the peer pool changed. It is re-reviewed quarterly
and revised only when the pool median has moved more than one third of the
IQR (about 8×) from the pinned value. The distribution below is always the
*current* pool, so the pin cannot drift away from the data unnoticed.

**1. Is the median the right statistic?** The pool is a power law:
min 5×, p25 15×, **median 20×**, mean 33.6×, trimmed mean 25.5×, p75 40×,
max 324×. The median is the *most conservative* of the central statistics.

**2. Is the pool comparable?** No — the multiple is not scale-invariant:

| Peer ARR band | n | Median multiple |
|---|---:|---:|
| < $100M | 37 | 20.0× |
| $100M – $1B | 29 | 30.1× |
| $1B – $5B | 5 | 14.5× |
| $5B – $20B | 2 | 24.5× |
| ≥ $20B | 2 | **13.3×** |

Anthropic and OpenAI — the only pure-plays actually comparable in scale to
Microsoft's $37B AI business — trade at **9.7× and 17.0×**. A size-matched
multiple would be ~13×, making our 20× *generous* for the big-tech rows. We
keep 20× because it's the most defensible summary of a heterogeneous pool and
because the ranking doesn't move.

**3. Does geography hide a split?** Yes. Western pure-plays: median 20× (n=76).
Chinese pure-plays: median **50×** (n=5). Applying a blended 20× to
Alibaba/Baidu/Tencent is conservative relative to their own peers — but with
n=5 that's a weak base, and we say so.

**4. What is the market actually paying?** (market cap ÷ AI ARR)

| Company | Market implies | Uncapped | We use | % of cap |
|---|---:|---:|---:|---:|
| Salesforce | 350× | $16B | $16B | 5.7% |
| Alphabet | 139× | $600B | $600B | 14.4% |
| ServiceNow | 133× | $30B | $30B | 15.0% |
| Amazon | 113× | $500B | $500B | 17.7% |
| Microsoft | 107× | $740B | $740B | 18.7% |
| Meta | 89× | $400B | $400B | 22.6% |
| Tencent | 67× | $140B | $140B | 29.7% |
| Alibaba | 29× | $186B | $186B | 68.9% |
| Notion AI | 20× | $6B | $6B | 100.0% |
| **Baidu** | **3.7×** | $149B | **$27.4B (capped)** | **100.0%** ⚠️ |

Two findings. The market pays 67–139× for megacap AI revenue because it prices
AI *optionality*, not just revenue — our derivation deliberately strips that
out. And **Baidu is the one row where the derivation overruns the company**:
uncapped, it implies 5.4× Baidu's entire market cap. Most likely its "Core
AI-Powered Business" line is largely re-segmented legacy search/ads — the same
relabelling problem we fixed for Salesforce. So the valuation cap binds: Baidu's
axis is set to its $27.4B market cap, the uncapped figure is published
alongside it, and the row is badged as indicative only.

**5. Does the ranking survive the multiple?** We re-ranked at 10×, 12×, 15×,
20×, 25×, 30× and 40×, applying the same cap in every run. **The top 11 is
identical at every one.** The number moves the derived dollar values, not the
ordering.

Full write-up: [`methodology.html`](methodology.html) section 6c.
Machine-readable: [`data/multiple_check.json`](data/multiple_check.json).

## What's in the box

```
top100-digital-ai-2026/           # repo root - served as the static site
├── index.html                 # landing page
├── ranking.html               # sortable, filterable top-100 table
├── methodology.html           # full scoring explanation
├── exclusions.html            # who got cut and why
├── company.html               # per-company deep-dive template
├── about.html                 # sources, license, how to reproduce
├── style.css                  # dark theme
├── app.js                     # sortable/filterable table, CSV export
├── ranked.json                # data file served to the browser
├── data/
│   ├── companies.json         # raw input data (107 entries)
│   ├── ranked.json            # top 100 with scores (mirror)
│   ├── ranked.csv             # flat CSV
│   ├── sensitivity.json       # log-vs-raw robustness results
│   └── multiple_check.json    # peer-multiple stress-test results
├── scripts/
│   ├── score.py               # scoring engine (Python, stdlib only)
│   ├── sensitivity.py         # log-vs-raw robustness analysis
│   ├── multiple_check.py      # peer-multiple stress test
│   ├── migrate_v2.py          # Oct-2026 dataset migration (M&A, big tech)
│   └── migrate_v3.py          # market-cap annotations, extra exclusions
├── README.md
└── LICENSE
```

## Reproducing the ranking

```bash
git clone https://github.com/bubbagump86/top100-digital-ai-2026.git
cd top100-digital-ai-2026
python scripts/score.py
```

This regenerates `data/ranked.json`, `data/ranked.csv`, and the
site-level `ranked.json` (used by the live site). Open `index.html` in a
browser to view the site (no build step).

The model policy — axis bounds, the pinned peer multiple, the missing-ARR rule
and the review triggers — lives in
[`data/model_config.json`](data/model_config.json). To change it, edit that
file; `scripts/score.py` reads it on every run. The weights are at the top of
`scripts/score.py`:

```python
W_VAL = 0.5
W_ARR = 0.5
```

For a dry run that cannot touch the live outputs:

```bash
python scripts/score.py --variant review --axis sample --peer-multiple 0
```

## Recent M&A reflected in the ranking

The 2025-2026 cycle has several high-profile consolidations, and this site
treats them with explicit annotations:

- **SpaceXAI (xAI + Cursor + X)** — presented as **one consolidated entity**.
  xAI acquired by **SpaceX** (all-stock, $250B, closed Feb 2, 2026); Cursor
  acquired (all-stock, $60B, signed Jun 16, 2026, closed Aug 14, 2026).
  Combined valuation **$310B** (the sum of the two disclosed transaction
  prices) and ~$14.2B ARR.
- **Codeium / Windsurf** — acquired by **Cognition** (undisclosed; ~$250M est.),
  closed Jul 14, 2025 with $82M ARR. The standalone Codeium row has been
  **dropped** because its ARR is now rolled into Cognition's consolidated
  figure.
- **Hugging Face** — acquired by NVIDIA in 2025; its $12.93B acquisition price
  remains a valid AI valuation, so it stays.

Full sources are in the per-company entry in
[`data/companies.json`](data/companies.json); the methodology page,
section 10, has the same commentary.

## Top 10 (2026 edition)

| Rank | Company                            | AI Valuation      | AI ARR               | Score |
|------|------------------------------------|-------------------|----------------------|-------|
| 1    | Anthropic                          | $965B             | $100,000M            | 99.81 |
| 2    | OpenAI                             | $852B             | $50,000M             | 95.37 |
| 3    | Microsoft (AI business)            | $740B *derived*   | $37,000M             | 92.97 |
| 4    | Alphabet (AI: Gemini + Cloud AI)   | $600B *derived*   | $30,000M             | 90.69 |
| 5    | Amazon (AWS AI)                    | $500B *derived*   | $25,000M             | 88.71 |
| 6    | Meta (AI)                          | $400B *derived*   | $20,000M             | 86.29 |
| 7    | SpaceXAI (xAI + Cursor + X)        | $310B             | $14,200M             | 83.05 |
| 8    | Alibaba (AI)                       | $186B *derived*   | $9,300M              | 77.97 |
| 9    | Databricks                         | $190B             | $7,000M              | 76.55 |
| 10   | Tencent (AI)                       | $140B *derived*   | $7,000M              | 74.89 |
| 11   | Baidu (AI)                         | $27.4B *derived, capped* | $7,440M      | 66.37 |

\* derived = AI-attributed ARR × the pinned 20× pure-play median EV/Revenue
multiple, capped at the company's market cap (Baidu's uncapped derivation was
$148.8B = 543% of its market cap, so the cap binds). Scores are rescaled
against fixed bounds (valuation $0.1B–$1,000B, ARR $10M–$100B), so Anthropic
tops out at 99.81 rather than 100.

The full ranking is in [`ranking.html`](ranking.html), and you can filter it
by valuation basis there.

## Features

- **Sortable, filterable** ranking table — search by name, category, HQ.
- **CSV export** — one click to take the filtered list with you.
- **Per-company deep-dive** pages with full score breakdowns.
- **Methodology** that anyone can read, attack, or reproduce.
- **Distribution & category breakdowns** on the overview page.
- All-static, no backend, no build step, no JS framework dependency.

## Data sources

The dataset was compiled in October 2026 from a mix of:

- Public-market filings (10-K, 10-Q, S-1).
- Confirmed funding rounds from TechCrunch, Reuters, Bloomberg, The
  Information, FT, WSJ, Forbes, Sifted.
- Company announcements and IPO prospectuses.
- Aggregations: Forbes AI 50, Crunchbase, PitchBook.

Each company entry in `data/companies.json` carries the specific source for
its valuation and ARR figures.

## Limitations

- Private-market round prices change fast. We use the latest figure we could
  verify through October 2026.
- For listed companies (Salesforce, ServiceNow, Palantir, etc.) we use the
  full-company valuation and ARR — we don't subtract pre-AI revenue.
- A few companies run-rate ARR internally (OpenAI, Anthropic, Cursor);
  we accept run-rate and flag it in the source field.

## License

- Code: MIT — see [`LICENSE`](LICENSE).
- Data (`data/companies.json`): CC-BY 4.0 — please attribute "Top 100
  Digital AI Companies 2026" if you reuse it.

## Contributing

Corrections, additions, fresh data? Open an issue or PR. Each entry carries
its sources, so any change should come with a citation.
