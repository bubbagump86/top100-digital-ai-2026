"""
scripts/migrate_v2.py
=====================
One-shot dataset migration for the October-2026 refresh:

  1. Update Anthropic / OpenAI ARR to the latest reported figures.
  2. Merge xAI + Cursor into a single SpaceXAI entity.
  3. Add 8 big-tech rows (Microsoft, Amazon, Google, Meta, Alibaba,
     Baidu, Tencent, ByteDance) with AI-attributed revenue.
  4. Tag every row with a valuation basis:
       pure_play  -> valuation is a market-set AI valuation (feeds the
                     peer-multiple pool)
       derived    -> valuation = AI-attributed ARR x peer median multiple
       proxy      -> no AI-revenue disclosure; full market cap used as a
                     flagged proxy, ARR axis scored at 0
  5. Drop rows that are no longer distinct businesses.

Run:  python scripts/migrate_v2.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "companies.json"

with DATA.open(encoding="utf-8") as fh:
    doc = json.load(fh)

companies = doc["companies"]
by_name = {c["name"]: c for c in companies}

# ---------------------------------------------------------------- 1. ARR refresh
by_name["Anthropic"].update({
    "arr_usd_m": 100000,
    "arr_date": "mid-September 2026 (run-rate)",
    "arr_source": ("New York Times (Sep 2026), via stateofclaude.com: >$100B annualised "
                   "run-rate. Prior prints: $65B end-Jul 2026 (Reuters), $47B mid-May "
                   "2026 (company-confirmed at Series H close), $30B Apr 2026, $14B Feb 2026, "
                   "$9B end-2025. Q3-2026 recognised revenue $16.8B (CNBC)."),
    "arr_total_usd_m": 100000,
    "arr_attribution_note": "100% AI. Anthropic is a pure-play AI company.",
})
by_name["Anthropic"]["valuation_date"] = "May 28, 2026 (Series H close, $65B raise)"
by_name["Anthropic"]["valuation_source"] = (
    "Series H at $965B post-money (second-largest private round on record). "
    "Confidentially filed for IPO Jun 1, 2026; targeting Nasdaq listing Nov 2026 "
    "at ~$1.5-2T (Reuters, Oct 14 2026 investor day)."
)

by_name["OpenAI"].update({
    "arr_usd_m": 50000,
    "arr_date": "end-September 2026 (run-rate)",
    "arr_source": ("Financial Times, confirmed by Reuters (Oct 9, 2026): ~$50B annualised "
                   "run-rate. NOTE: an earlier ~$70B figure (Axios, Sep 29) was revised DOWN "
                   "because it counted gross cloud-partner sales; OpenAI books only its net "
                   "share. Q3-2026 revenue growth: +77% overall, +107% enterprise. "
                   "ChatGPT ads $1B annualised; 1.2B WAU."),
    "arr_total_usd_m": 50000,
    "arr_attribution_note": "100% AI. OpenAI is a pure-play AI company.",
})
by_name["OpenAI"]["valuation_date"] = "March 2026 ($122B round, $852B post-money)"
by_name["OpenAI"]["valuation_source"] = (
    "$852B held flat through a self-funded $7B employee tender completed Aug 10, 2026 "
    "(CNBC). A ~$1.4T / $30B bridge round is in EARLY, UNSIGNED talks (Bloomberg, "
    "Sep 29 2026) - not used, since $852B is the last confirmed mark."
)

# --------------------------------------------------- 2. Merge xAI + Cursor -> SpaceXAI
xai = by_name["xAI (now SpaceXAI)"]
cursor = by_name["Anysphere / Cursor (now SpaceXAI division)"]

spacexai = {
    "rank_seed": 4,
    "name": "SpaceXAI (xAI + Cursor + X)",
    "category": "Foundation Models / AI Coding / Consumer AI",
    "hq": "Palo Alto & San Francisco, USA (SpaceXAI division of SpaceX)",
    "founded": 2023,
    "valuation_usd_b": 310.0,
    "valuation_date": "Feb 2, 2026 (xAI) & Aug 14, 2026 (Cursor) - both SpaceX acquisitions closed",
    "valuation_source": ("Sum of disclosed all-stock acquisition prices: xAI $250B "
                         "(SpaceX, closed Feb 2 2026, 0.1433 SpaceX shares per xAI share) + "
                         "Anysphere/Cursor $60B (SpaceX, signed Jun 16 2026, closed Aug 14 2026, "
                         "~391M SpaceX Class A shares). SpaceX itself IPO'd on Nasdaq Jun 12, "
                         "2026 at ~$1.77T market cap."),
    "arr_usd_m": 14200,
    "arr_date": "Q2 2026 segment actual ($2.561B) + Cursor $4B ARR consolidated from Aug 14, 2026",
    "arr_source": ("SpaceX SEC filings: AI segment revenue $2.561B in Q2 2026 (+247% YoY), "
                   "$818M in Q1 2026, $3.2B FY2025; AI segment operating loss $6.4B FY2025. "
                   "Cursor contributed a $4B ARR run-rate at close (SpaceX announcement). "
                   "Grok's own product ARR was last pegged at ~$500M (Bloomberg, mid-2026). "
                   "Grok: 117M MAU, 1.9M paying SuperGrok subscribers (S-1, Mar 2026)."),
    "arr_total_usd_m": 14200,
    "arr_attribution_note": (
        "Single consolidated entity: xAI (Grok) + Cursor (Anysphere) + X. ARR = Q2 2026 AI "
        "segment revenue $2.561B annualised ($10.2B) + Cursor's $4B ARR (consolidated from "
        "Aug 14 2026). The segment also carries four compute-rental contracts worth ~$41B "
        "annualised at their stated rates by Dec 2026 (Anthropic $1.25B/mo to May 2029, "
        "Google $920M/mo from Oct 2026, Reflection AI $150M/mo, plus a new $1.11B/mo deal) - "
        "that ramp is the single biggest forward swing factor and is NOT in the $14.2B above. "
        "Grok, Cursor, Grok Bot and X Premium were unified into a single 'X Subscription' "
        "on Oct 12-13, 2026."),
    "summary": ("Consolidated AI business of SpaceX: Grok foundation models + Cursor AI coding "
                "($4B ARR) + the X platform. Acquired by SpaceX in two all-stock deals "
                "($250B for xAI in Feb 2026, $60B for Cursor in Aug 2026). Now also runs a "
                "large GPU-compute-rental business leasing Colossus capacity to Anthropic, "
                "Google and others."),
    "is_digital_only": True,
    "is_pure_play_ai": False,
    "valuation_basis": "actual",
    "corporate_status": "division_of_spacex_since_2026-02-02",
}
companies[companies.index(xai)] = spacexai
companies.remove(cursor)

# ------------------------------------------------------------ 3. Big tech additions
BIG_TECH = [
    {
        "rank_seed": 70,
        "name": "Microsoft (AI business)",
        "category": "Big Tech AI - Enterprise AI & Cloud",
        "hq": "Redmond, USA",
        "founded": 1975,
        "valuation_usd_b": None,
        "valuation_date": "Derived: AI ARR x peer multiple",
        "valuation_source": ("DERIVED. Microsoft does not publish an AI-segment market cap. "
                             "We impute one using the peer EV/Revenue multiple derived from "
                             "the pure-play set (see methodology sec. 6b). Full-company market "
                             "cap is not used because ~85% of Microsoft revenue is non-AI "
                             "(Windows, Office, Gaming, LinkedIn, search)."),
        "arr_usd_m": 37000,
        "arr_date": "Q3 FY2026 (quarter ended Mar 31, 2026) - not restated at Q4",
        "arr_source": ("Microsoft FY26 Q3 earnings call, Apr 29 2026 (Nadella): 'Our AI business "
                       "surpassed $37 billion ARR, up 123%.' Q4 FY26 (Jul 29 2026) did NOT restate "
                       "a consolidated AI-ARR figure; it gave proxies instead: M365 Copilot >30M "
                       "paid seats, Copilot revenue +60% QoQ, Azure revenue >$100B for the first "
                       "time, Azure growth +43%, commercial RPO $678B (+84%). FY26 total revenue "
                       "$331.8B."),
        "arr_total_usd_m": 331800,
        "arr_attribution_note": ("AI business ARR as disclosed by Microsoft ($37B, +123% YoY). "
                                  "Most transparently disclosed AI revenue figure of any "
                                  "diversified company in this list."),
        "summary": ("Copilot family (M365 Copilot, GitHub Copilot, Security Copilot, consumer "
                    "Copilot) + Azure AI services + first-party models. The largest disclosed "
                    "AI business ARR of any diversified tech company."),
        "is_digital_only": True,
        "is_pure_play_ai": False,
        "valuation_basis": "derived",
    },
    {
        "rank_seed": 71,
        "name": "Google / Alphabet (AI: Gemini + Cloud AI)",
        "category": "Big Tech AI - Foundation Models & Cloud AI",
        "hq": "Mountain View, USA",
        "founded": 1998,
        "valuation_usd_b": None,
        "valuation_date": "Derived: AI ARR x peer multiple",
        "valuation_source": ("DERIVED from AI-attributed revenue x peer EV/Revenue multiple. "
                             "Alphabet's full market cap is not used: search, YouTube, Android "
                             "and Play remain the majority of revenue."),
        "arr_usd_m": 30000,
        "arr_date": "2026 run-rate (estimate from Q1-Q2 2026 disclosures)",
        "arr_source": ("ESTIMATE. Alphabet does not disclose standalone Gemini revenue. Anchors: "
                       "Google Cloud Q2 2026 revenue $24.768B (+82% YoY, run-rate ~$99B) with "
                       "management attributing the acceleration to 'enterprise AI Solutions and "
                       "enterprise AI Infrastructure'; revenue from products built on gen-AI "
                       "models grew ~800% YoY (Q1 2026); Gemini app 950M MAU; Gemini Enterprise in "
                       "~90% of the Fortune 100; Gemini API 22B tokens/min; Vertex AI usage 25x "
                       "YoY; Google One AI subscriptions. Estimate = AI-attributable share of "
                       "Cloud run-rate + Gemini API + consumer AI subscriptions."),
        "arr_total_usd_m": 479000,
        "arr_attribution_note": ("AI-attributable ARR is an ESTIMATE, not a disclosure - flagged "
                                 "as such. Google Cloud total run-rate ~$99B; we attribute a "
                                 "minority share to AI products plus Gemini API and consumer AI "
                                 "plans."),
        "summary": ("Gemini model family, Gemini app (950M MAU), Gemini Enterprise agent "
                    "platform, Vertex AI, TPUs, and Google One AI subscriptions. 3.0+ has been "
                    "revenue driver of Google Cloud for the first time."),
        "is_digital_only": True,
        "is_pure_play_ai": False,
        "valuation_basis": "derived",
    },
    {
        "rank_seed": 72,
        "name": "Amazon (AWS AI)",
        "category": "Big Tech AI - AI Cloud & Model Platform",
        "hq": "Seattle, USA",
        "founded": 1994,
        "valuation_usd_b": None,
        "valuation_date": "Derived: AI ARR x peer multiple",
        "valuation_source": ("DERIVED from AI-attributed revenue x peer EV/Revenue multiple. "
                             "Amazon's full market cap is not used: e-commerce is the majority "
                             "of revenue."),
        "arr_usd_m": 25000,
        "arr_date": "Q2 2026 (annualised run-rate)",
        "arr_source": ("Amazon Q2 2026 earnings (Jassy): AWS's AI business 'exceeded a $25 billion "
                       "annual revenue run rate, growing triple-digit percentages year-over-year'; "
                       "the chips business also passed $25B run-rate. AWS total $42.2B in the "
                       "quarter (+37%), a $169B annualised run-rate. Bedrock has hundreds of "
                       "thousands of customers; Q2 Bedrock spend exceeded all prior quarters "
                       "combined; 10+ models added in the quarter."),
        "arr_total_usd_m": 740000,
        "arr_attribution_note": ("AWS AI business run-rate as disclosed by Amazon ($25B+). "
                                  "This is AI services revenue, excluding the separate "
                                  "chips/ silicon business."),
        "summary": ("Amazon Bedrock (frontier-model marketplace, now hosting GPT-5.6, Claude "
                    "Opus 5, Gemma 4 and SpaceXAI's Grok 4.3), Bedrock AgentCore, SageMaker, "
                    "and AWS AI infrastructure. Fastest AWS growth in 18 quarters."),
        "is_digital_only": True,
        "is_pure_play_ai": False,
        "valuation_basis": "derived",
    },
    {
        "rank_seed": 73,
        "name": "Meta (AI: Advantage+ + Meta AI + Llama)",
        "category": "Big Tech AI - Advertising AI & Foundation Models",
        "hq": "Menlo Park, USA",
        "founded": 2004,
        "valuation_usd_b": None,
        "valuation_date": "Derived: AI ARR x peer multiple",
        "valuation_source": ("DERIVED from AI-attributed revenue x peer EV/Revenue multiple. "
                             "Meta's full market cap is not used: ~97.7% of Q2 2026 revenue "
                             "was advertising."),
        "arr_usd_m": 20000,
        "arr_date": "2026 run-rate (Advantage+ AI campaigns, last disclosed figure)",
        "arr_source": ("Meta disclosed that AI-driven Advantage+ campaigns 'surpassed $20 billion "
                       "in annual run rate' (Q2 2025 earnings). Context: Q2 2026 revenue $60.8B "
                       "(+28%), of which $59.36B advertising; 4M+ advertisers using Meta's "
                       "generative AI tools; Gen Ads Recommendation Model delivering +5% Instagram "
                       "ad conversion; AI lifted ad pricing 6% and impressions 18%. 2026 capex "
                       "guidance $130-145B."),
        "arr_total_usd_m": 243200,
        "arr_attribution_note": ("Meta's AI chatbot (Meta AI / Muse Spark) generates $0 direct "
                                  "revenue; the AI money is in advertising optimisation. We use "
                                  "the disclosed Advantage+ $20B run-rate. The Meta AI app and "
                                  "Llama/Muse API revenue are additive but undisclosed."),
        "summary": ("Meta Superintelligence Labs: Muse model family (frontier weights closed), "
                    "Llama open-weight family (1B+ cumulative downloads), Meta AI assistant "
                    "across WhatsApp/Instagram/Facebook (1B+ MAU), and Advantage+ AI ad "
                    "campaigns - the single largest AI-monetised product at Meta."),
        "is_digital_only": True,
        "is_pure_play_ai": False,
        "valuation_basis": "derived",
    },
    {
        "rank_seed": 74,
        "name": "Alibaba (AI: Qwen + Alibaba Cloud AI)",
        "category": "Big Tech AI - Foundation Models & AI Cloud",
        "hq": "Hangzhou, China",
        "founded": 1999,
        "valuation_usd_b": None,
        "valuation_date": "Derived: AI ARR x peer multiple",
        "valuation_source": ("DERIVED from AI-attributed revenue x peer EV/Revenue multiple. "
                             "Alibaba's full market cap is not used: e-commerce, local "
                             "services and quick commerce dominate group revenue."),
        "arr_usd_m": 9300,
        "arr_date": "Q2 FY2027 (quarter ended Jun 30, 2026), annualised",
        "arr_source": ("Alibaba Group results, Aug 20 2026: AI-related product revenue US$1.824B "
                       "in the June 2026 quarter (12th consecutive quarter of triple-digit YoY "
                       "growth) -> $7.30B annualised; AI Labs and Applications segment US$492M in "
                       "the quarter -> $1.97B annualised. Combined AI-attributed ARR ~$9.3B. "
                       "Context: AI Cloud and Compute Services revenue US$7.139B (+45%); Cloud "
                       "external revenue +45%; Qwen App 300M+ MAU; Qwen 3B+ downloads; "
                       "management guides AI model/application ARR to RMB 30B (~$4.3B) by "
                       "year-end and >50% of cloud external revenue within a year."),
        "arr_total_usd_m": 158000,
        "arr_attribution_note": ("AI-related product revenue + AI Labs and Applications "
                                  "segment, both disclosed by Alibaba."),
        "summary": ("Qwen model family (most-downloaded open-source model family globally), "
                    "Alibaba Cloud / Model Studio (MaaS) with the Token Hub business group, "
                    "QwenWork workforce agent, Qwen App and Taobao shopping agent. China's "
                    "largest AI cloud by share (38.1%, Omdia)."),
        "is_digital_only": True,
        "is_pure_play_ai": False,
        "valuation_basis": "derived",
    },
    {
        "rank_seed": 75,
        "name": "Baidu (AI: ERNIE + Baidu AI Cloud)",
        "category": "Big Tech AI - Foundation Models & AI Cloud",
        "hq": "Beijing, China",
        "founded": 2000,
        "valuation_usd_b": None,
        "valuation_date": "Derived: AI ARR x peer multiple",
        "valuation_source": ("DERIVED from AI-attributed revenue x peer EV/Revenue multiple. "
                             "Baidu's full market cap is not used: online marketing is still "
                             "roughly half of core revenue and is declining."),
        "arr_usd_m": 7440,
        "arr_date": "Q2 2026 (quarter ended Jun 30, 2026), annualised",
        "arr_source": ("Baidu Q2 2026 results (Aug 18 2026): Core AI-powered Business RMB 12.5B "
                       "(~$1.86B) in the quarter -> $7.44B annualised, now >50% of core revenue "
                       "for a second consecutive quarter. AI Cloud Infrastructure RMB 7.3B (+50%); "
                       "GPU Cloud +283% YoY; AI Applications RMB 2.5B (+3%); Qianfan external "
                       "token usage 9x YoY. Total Q2 revenue RMB 31.3B (-4.4% YoY), net profit "
                       "RMB 2.32B (-68%)."),
        "arr_total_usd_m": 125000,
        "arr_attribution_note": ("Baidu's own 'Core AI-powered Business' segment - the most "
                                  "AI-concentrated disclosure of any company in this list "
                                  "(>52% of core revenue)."),
        "summary": ("ERNIE 5.x model family, Baidu AI Cloud (China's #1 AI cloud by LLM share), "
                    "Qianfan model-as-a-service, and Apollo Go robotaxis. Also the most "
                    "AI-concentrated large-cap by revenue mix - and the one where AI is "
                    "displacing, not adding to, the legacy business."),
        "is_digital_only": True,
        "is_pure_play_ai": False,
        "valuation_basis": "derived",
    },
    {
        "rank_seed": 76,
        "name": "Tencent (AI: Hunyuan + Tencent Cloud AI)",
        "category": "Big Tech AI - Foundation Models & AI Cloud",
        "hq": "Shenzhen, China",
        "founded": 1998,
        "valuation_usd_b": None,
        "valuation_date": "Derived: AI ARR x peer multiple",
        "valuation_source": ("DERIVED from AI-attributed revenue x peer EV/Revenue multiple. "
                             "Tencent's full market cap is not used: gaming, advertising and "
                             "fintech dominate."),
        "arr_usd_m": 7000,
        "arr_date": "Q2 2026 run-rate (estimate)",
        "arr_source": ("ESTIMATE. Tencent does not disclose AI revenue. Anchors: Q2 2026 cloud "
                       "revenue growth accelerated to 'low 20s percent' explicitly attributed to "
                       "AI-related demand (GPU rental, Model-as-a-Service, WorkBuddy and "
                       "CodeBuddy token usage); operating capex RMB 51.8B (+190% YoY); new AI "
                       "product drag RMB 10.5B in the quarter; Hunyuan 3 in production, Hunyuan 4 "
                       "in training; Yuanbao and Xiaowei consumer agents. Estimate assumes roughly "
                       "40% of Tencent Cloud revenue is AI-related."),
        "arr_total_usd_m": 820000,
        "arr_attribution_note": ("ESTIMATE, flagged as such. Tencent Cloud revenue is not broken "
                                  "out either, so this is the weakest of the big-tech AI "
                                  "figures in this list."),
        "summary": ("Hunyuan model family (Hunyuan 3 in production, Hunyuan 4 training), "
                    "WorkBuddy and CodeBuddy productivity agents, Yuanbao and Xiaowei consumer "
                    "agents, and Tencent Cloud MaaS/GPU rental. Distribution to 1B+ WeChat users."),
        "is_digital_only": True,
        "is_pure_play_ai": False,
        "valuation_basis": "derived",
    },
    {
        "rank_seed": 77,
        "name": "ByteDance (AI: Doubao + Seed + Volcano Engine)",
        "category": "Big Tech AI - Consumer AI & Foundation Models",
        "hq": "Beijing, China",
        "founded": 2012,
        "valuation_usd_b": 300.0,
        "valuation_date": "2024-25 private round (stale - no new mark disclosed)",
        "valuation_source": ("Private company; no 2026 primary mark disclosed. Last known "
                             "valuation ~$300B. Used as a market-cap proxy because ByteDance "
                             "discloses no AI-attributed revenue."),
        "arr_usd_m": None,
        "arr_date": None,
        "arr_source": ("Not disclosed. Doubao assistant 260M+ MAU in Q1 2026 (overtaking ERNIE "
                       "Bot for the first time) and 345M+ MAU by mid-2026; Volcano Engine AI "
                       "cloud; Seedance video models; 2026 capex estimates $23-70B depending on "
                       "source (all third-party, none company-confirmed)."),
        "arr_total_usd_m": 186000,
        "arr_attribution_note": ("No AI-revenue disclosure. This row scores on valuation alone "
                                  "(market-cap proxy) and is one of the weakest evidence bases in "
                                  "the list."),
        "summary": ("China's largest AI consumer platform by users: Doubao assistant (345M+ "
                    "MAU), Seed model family, Seedance video, and Volcano Engine AI cloud. "
                    "Occupies ~1/5 of China's delivered datacenter capacity."),
        "is_digital_only": True,
        "is_pure_play_ai": False,
        "valuation_basis": "proxy",
    },
]

# Insert big-tech rows right after the pure-play core, keeping rank_seed order later.
companies.extend(BIG_TECH)

# --------------------------------------- 4. Re-tag existing rows with a valuation basis
# Default: pure-play AI company -> its own valuation IS an AI valuation.
for c in companies:
    c.setdefault("is_pure_play_ai", True)
    c.setdefault("valuation_basis", "actual")

# Rows whose valuation is a FULL-COMPANY market cap and whose ARR is AI-attributed.
# -> valuation must be derived from the AI revenue at peer multiples.
DERIVED = {
    "Salesforce (Agentforce / AI)": {
        "arr_usd_m": 800,
        "arr_date": "Q4 FY2026 (Feb 2026 earnings)",
        "arr_source": ("Salesforce Q4 FY26 press release; SEC 8-K (Agentforce ARR $800M, "
                       "+169% YoY). Total company revenue $41.5B - we use the AI slice only."),
        "valuation_basis": "derived",
        "is_pure_play_ai": False,
    },
    "ServiceNow (Now Assist AI)": {
        "arr_usd_m": 1500,
        "arr_date": "FY2026 forecast (Q2 2026 actual: $1B ACV)",
        "arr_source": ("ServiceNow Q2 2026 financial results; management earnings call. "
                       "Now Assist + AI portfolio = $1.5B FY26 forecast against $15.8B total "
                       "subscription revenue - only ~10% of subscription revenue is classified "
                       "as AI."),
        "valuation_basis": "derived",
        "is_pure_play_ai": False,
    },
    "Notion AI": {
        "arr_usd_m": 300,
        "arr_date": "2025 (AI-attributed est.)",
        "arr_source": "Press estimates (Notion AI revenue slice).",
        "valuation_basis": "derived",
        "is_pure_play_ai": False,
    },
}

PROXY = {
    "Palantir Technologies": {
        "valuation_basis": "proxy",
        "is_pure_play_ai": False,
        "valuation_source": ("PROXY. Palantir's AIP revenue is not disclosed separately, so an "
                             "AI-attributed valuation cannot be derived. Full market cap used "
                             "as a flagged proxy - this OVERSTATES Palantir's AI valuation and "
                             "simultaneously UNDERSTATES its AI revenue (both axes penalised "
                             "in opposite directions)."),
    },
    "Samsara": {
        "valuation_basis": "proxy",
        "is_pure_play_ai": False,
        "valuation_source": ("PROXY. Samsara sells sensor hardware; AI-layer revenue is not "
                             "separately disclosed, so no AI-attributed valuation can be "
                             "derived. Full market cap used as a flagged proxy."),
    },
    "Schrodinger": {
        "valuation_basis": "proxy",
        "is_pure_play_ai": False,
        "valuation_source": ("PROXY. Bunsen (agentic AI) is pre-revenue; the core $200M+ ACV is "
                             "physics simulation, not AI. Full market cap used as a flagged "
                             "proxy."),
    },
    "Cohesity": {
        "valuation_basis": "proxy",
        "is_pure_play_ai": False,
        "valuation_source": ("PROXY. Enterprise data security, not an AI company. AI search is "
                             "a feature. Full market cap used as a flagged proxy."),
    },
    "Talkdesk": {
        "valuation_basis": "proxy",
        "is_pure_play_ai": False,
        "valuation_source": ("PROXY. CCaaS platform with AI features; AI revenue is not "
                             "separately disclosed. Full market cap used as a flagged proxy."),
    },
}

for name, patch in DERIVED.items():
    by_name[name].update(patch)
for name, patch in PROXY.items():
    by_name[name].update(patch)

# ------------------------------------------------------------- 5. Drop merged / stale rows
DROP = ["Codeium (Windsurf) — now part of Cognition", "Roblox (AI in Gaming Platform)"]
for name in DROP:
    if name in by_name:
        companies.remove(by_name[name])

# ---------------------------------------------------------------------- write it out
doc["companies"] = companies
doc["metadata"]["scoring"]["valuation_bases"] = {
    "pure_play": ("Company is fundamentally an AI business. Its market or transaction "
                  "valuation IS an AI valuation and is used as-is. These companies also form "
                  "the peer pool used to derive the multiple below."),
    "derived": ("Company is diversified. We take its AI-attributed ARR and multiply by the "
                "pure-play median EV/Revenue multiple to obtain an implied 'what would this AI "
                "business be worth standalone' valuation."),
    "proxy": ("Company discloses no AI-attributed revenue, so no AI valuation can be derived. "
              "Full market cap is used as a flagged proxy and the ARR axis is scored at 0. "
              "These are the weakest-evidence rows in the list."),
}
doc["metadata"]["scoring"]["missing_data_policy"] = (
    "If ARR is undisclosed but a recent revenue or run-rate exists, we substitute it. "
    "If both metrics are missing the company is dropped from the ranked list. Companies "
    "with no disclosed AI revenue are kept only where a market-cap proxy is defensible, "
    "and are flagged 'proxy'."
)
doc["metadata"]["generated_at"] = "2026-10-21"

DATA.write_text(json.dumps(doc, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"companies: {len(companies)}")
print("pure_play:", sum(1 for c in companies if c.get("is_pure_play_ai", True)))
print("derived  :", sum(1 for c in companies if c.get("valuation_basis") == "derived"))
print("proxy    :", sum(1 for c in companies if c.get("valuation_basis") == "proxy"))
print("actual   :", sum(1 for c in companies if c.get("valuation_basis") == "actual"))
