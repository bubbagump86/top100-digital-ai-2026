"""
scripts/migrate_v3.py
=====================
Adds full-company market-cap reference data to the diversified rows, and
extends the exclusion list with the large caps that fail the AI-revenue
test (Apple) or the digital-AI test (TSM, Broadcom, Tesla).

Market caps: Oct 20, 2026 close (StockTitan / Morningstar / MarketWatch /
wafergraph).
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "companies.json"

with DATA.open(encoding="utf-8") as fh:
    doc = json.load(fh)

by_name = {c["name"]: c for c in doc["companies"]}

MARKET_CAPS = {
    "Microsoft (AI business)":                       (3950.0, "Oct 20, 2026 close (StockTitan)"),
    "Google / Alphabet (AI: Gemini + Cloud AI)":     (4160.0, "Oct 20, 2026 close (StockTitan)"),
    "Amazon (AWS AI)":                               (2830.0, "Oct 20, 2026 close (StockTitan)"),
    "Meta (AI: Advantage+ + Meta AI + Llama)":        (1770.0, "Oct 20, 2026 close (StockTitan)"),
    "Alibaba (AI: Qwen + Alibaba Cloud AI)":          (270.1,  "Oct 20, 2026 (wafergraph)"),
    "Baidu (AI: ERNIE + Baidu AI Cloud)":             (27.4,   "Oct 20, 2026 close (Morningstar / MarketWatch)"),
    "Tencent (AI: Hunyuan + Tencent Cloud AI)":       (470.9,  "Oct 20, 2026 (wafergraph)"),
    "ByteDance (AI: Doubao + Seed + Volcano Engine)": (300.0,  "2024-25 private round; no 2026 mark"),
    "Salesforce (Agentforce / AI)":                  (280.0,  "2025 market cap"),
    "ServiceNow (Now Assist AI)":                    (200.0,  "2025 market cap"),
    "Notion AI":                                     (6.0,    "2024 private round"),
    "Palantir Technologies":                         (350.0,  "2025 market cap"),
    "Samsara":                                       (30.0,   "2025 market cap"),
    "Schrodinger":                                   (3.0,    "2025 market cap"),
    "Cohesity":                                      (4.69,   "2024 secondary"),
    "Talkdesk":                                      (10.0,   "2024 secondary"),
    "SpaceXAI (xAI + Cursor + X)":                   (1950.0, "Oct 20, 2026 close (StockTitan) - parent SpaceX"),
}

for name, (mcap, asof) in MARKET_CAPS.items():
    if name in by_name:
        by_name[name]["market_cap_usd_b"] = mcap
        by_name[name]["market_cap_date"] = asof

# Extend the exclusion list with the large caps that fail our tests.
doc["exclusions"]["examples"].extend([
    {"name": "Apple", "why": "Apple Intelligence is not separately monetized - no AI revenue line exists. Its $4.95T market cap is a consumer-electronics franchise, and including it would make the valuation axis a measure of hardware franchises, not AI."},
    {"name": "TSMC", "why": "Semiconductor foundry"},
    {"name": "Broadcom", "why": "Semiconductor / networking silicon (incl. custom AI ASICs)"},
    {"name": "Tesla", "why": "Autos; AI only via the autonomy stack (excluded as physical)"},
    {"name": "SpaceX (parent)", "why": "Launch + space infrastructure. Only its SpaceXAI division is digital AI, and that division IS ranked separately as 'SpaceXAI (xAI + Cursor + X)'."},
    {"name": "Codeium / Windsurf", "why": "Acquired by Cognition Jul 14, 2025; ARR now rolled into Cognition's consolidated figure. Removed to avoid double counting."},
])

doc["exclusions"]["reason"] = (
    "Excluded from the ranked top 100 because the company is hardware-first, "
    "robotics-first, semiconductor-first, physically-manufactured, or has no "
    "disclosed AI revenue line. They are not 'pure-play digital AI'."
)

with DATA.open("w", encoding="utf-8") as fh:
    json.dump(doc, fh, indent=2, ensure_ascii=False)

print(f"market_cap annotated: {len(MARKET_CAPS)} rows")
print(f"exclusions: {len(doc['exclusions']['examples'])}")
