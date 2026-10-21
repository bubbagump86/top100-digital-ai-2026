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
**min-max rescale** to `[0, 1]`. The composite is the equal-weighted average:

```
S = 100 * (0.5 * z_log(valuation) + 0.5 * z_log(ARR))
```

where `z_log(x) = (log10(x) - log_min) / (log_max - log_min)`.

### The three-basis model (how big tech fits in)

| Basis | Who | How the valuation is set |
|---|---|---|
| **Pure-play** | Anthropic, OpenAI, Databricks, SpaceXAI, Mistral, Cursor-era AI labs… | The company's own market/transaction valuation. It already *is* an AI valuation. |
| **AI-attributed** | Microsoft, Google, Amazon, Meta, Alibaba, Baidu, Tencent, Salesforce, ServiceNow, Notion AI | `AI-attributed ARR × 20×` — the pure-play median EV/Revenue multiple (n=81, IQR 15–40×). Answers *"what would this AI business be worth standalone?"* |
| **Market-cap proxy** | Palantir, Samsara, Schrodinger, ByteDance, Cohesity, Talkdesk | No AI-revenue disclosure, so no AI valuation can be derived. Full market cap used as a flagged proxy; ARR axis scored 0. |

The peer multiple is derived from the pure-play pool only, so the imputation
never feeds back into its own input.

Missing data: if one axis is undisclosed it scores 0 (worst observed). If
both are missing the company is dropped.

Full treatment, worked examples, and sensitivity analysis — see
[`methodology.html`](methodology.html), section 6b.

## What's in the box

```
top100-ai-2026/                # repo root - served as the static site
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
│   └── ranked.csv             # flat CSV
├── scripts/
│   ├── score.py               # scoring engine (Python, stdlib only)
│   ├── migrate_v2.py          # Oct-2026 dataset migration (M&A, big tech)
│   └── migrate_v3.py          # market-cap annotations, extra exclusions
├── README.md
└── LICENSE
```

## Methodology in 60 seconds

For each pure-play digital AI company we collect:

- `valuation_usd_b`: most recent primary/tender round, public-market cap, or
  transaction valuation (USD billions).
- `arr_usd_m`: disclosed ARR or annualised run-rate (USD millions).

Both axes span 5+ orders of magnitude, so we **log-transform** each value and
**min-max rescale** to `[0, 1]` across the surviving set. The composite score
is the equal-weighted average:

```
S = 100 * (0.5 * z_log(val) + 0.5 * z_log(arr))
```

Where `z_log(x) = (log10(x) - log_min) / (log_max - log_min)`.

If one of the two axes is undisclosed, the missing axis is scored at 0
(worst observed). If both are missing, the company is dropped from the
ranking.

For the worked example with Anthropic, the reasoning, the missing-data
policy, and the sensitivity analysis — see
[`site/methodology.html`](site/methodology.html).

## Reproducing the ranking

```bash
git clone https://github.com/bubbagump86/top100-digital-ai-2026.git
cd top100-digital-ai-2026
python scripts/score.py
```

This regenerates `data/ranked.json`, `data/ranked.csv`, and the
site-level `ranked.json` (used by the live site). Open `index.html` in a
browser to view the site (no build step).

To tweak the scoring, change the weights at the top of `scripts/score.py`:

```python
W_VAL = 0.5
W_ARR = 0.5
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
| 1    | Anthropic                          | $965B             | $100,000M            | 100.00 |
| 2    | OpenAI                             | $852B             | $50,000M             | 95.56 |
| 3    | Microsoft (AI business)            | $740B *derived*   | $37,000M             | 93.16 |
| 4    | Google / Alphabet (AI)             | $600B *derived*   | $30,000M             | 90.87 |
| 5    | Amazon (AWS AI)                    | $500B *derived*   | $25,000M             | 88.89 |
| 6    | Meta (AI)                          | $400B *derived*   | $20,000M             | 86.46 |
| 7    | SpaceXAI (xAI + Cursor + X)        | $310B             | $14,200M             | 83.22 |
| 8    | Alibaba (AI)                       | $186B *derived*   | $9,300M              | 78.13 |
| 9    | Databricks                         | $190B             | $7,000M              | 76.71 |
| 10   | Baidu (AI)                         | $149B *derived*   | $7,440M              | 75.71 |

\* derived = AI-attributed ARR × the 20× pure-play median EV/Revenue multiple.

The full ranking is in [`ranking.html`](ranking.html), and you can filter it
by valuation basis there.

The full ranking is in [`site/ranking.html`](site/ranking.html).

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
