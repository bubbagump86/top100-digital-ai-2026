# Top 100 Pure-Play Digital AI Companies 2026

A standalone, transparent ranking of the top 100 **digital** AI companies in
2026, scored on a normalised composite of **valuation** and **ARR**.

This is *not* "AI startups" — it is exclusively digital-AI businesses.
Hardware (AI silicon, robotics, autonomous vehicles, physical-world AI) is
intentionally excluded. See the [exclusions page](site/exclusions.html) for
the full cut list and rationale.

Live site: https://bubbagump86.github.io/top100-digital-ai-2026/
Repository: https://github.com/bubbagump86/top100-digital-ai-2026

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
│   ├── companies.json         # raw input data (101 entries)
│   ├── ranked.json            # top 100 with scores (mirror)
│   └── ranked.csv             # flat CSV
├── scripts/
│   └── score.py               # scoring engine (Python, stdlib only)
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

## Top 10 (2026 edition)

| Rank | Company                          | Valuation | ARR      | Score |
|------|----------------------------------|-----------|----------|-------|
| 1    | Anthropic                        | $965B     | $30,000M | 98.57 |
| 2    | OpenAI                           | $852B     | $25,000M | 96.78 |
| 3    | Salesforce (Agentforce / AI)     | $280B     | $38,000M | 93.26 |
| 4    | ServiceNow (Now Assist AI)        | $200B     | $12,000M | 84.43 |
| 5    | Databricks                       | $190B     | $7,000M  | 80.88 |
| 6    | Palantir Technologies            | $350B     | $3,700M  | 80.34 |
| 7    | xAI                              | $230B     | $1,500M  | 72.58 |
| 8    | Anysphere (Cursor)               | $60B      | $4,000M  | 71.21 |
| 9    | VAST Data                        | $30B      | $2,000M  | 63.22 |
| 10   | Scale AI                         | $29B      | $2,000M  | 63.04 |

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
