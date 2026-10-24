"""
apply_coverage_2026_10.py - close the coverage gap found in the 2026-10 edition.

CONTEXT
-------
The 2026-10 edition was compared against a 39-name third-party AI company
list. 18 names were in the Top 100, 2 were folded into roll-up rows
(Google DeepMind -> Alphabet, Microsoft Research Asia -> Microsoft), and
19 had NO disposition at all - they were simply missing from the dataset,
not even on the exclusions page. That silence was the coverage bug.

This script closes it. Every one of those 21 names now gets exactly one
disposition:

  * added as a ranked row (7)
  * folded into an existing roll-up row (2)
  * excluded with a published reason (12)

ADMISSION RULE APPLIED (and why each call went the way it did)
-------------------------------------------------------------
A company is admitted if it is:

  1. pure-play digital AI - the AI business IS the company, so its market
     or transaction valuation is already an AI valuation        -> 'actual'
  2. a diversified company that DISCLOSES AI-attributed revenue  -> 'derived'
  3. a company with a material AI business that discloses no AI
     revenue line, where a market-cap proxy is defensible        -> 'proxy'

A software company is excluded when AI is neither disclosed nor material
(the Apple test), because scoring it on its full market cap would make
the valuation axis a measure of non-AI software franchises.

THIRD-PARTY ESTIMATE RULE
-------------------------
A third-party revenue estimate is used as an input only when it is
(a) above this list's $10M ARR anchor and (b) the best available figure.
It is then published with its source and an explicit confidence flag.
Below the anchor (Luma AI at ~$8M) it is not used, and the row's ARR axis
reads 0 under the missing-ARR rule.

Idempotent: re-running replaces the same rows rather than duplicating them.

Run:
    python scripts/apply_coverage_2026_10.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "companies.json"

GENERATED_AT = "2026-10-24"

# ---------------------------------------------------------------------------
# 1. RANKED ROWS
# ---------------------------------------------------------------------------

NEW_ROWS = [
    # ---------------- Snowflake: disclosed AI revenue -> derived -----------
    {
        "rank_seed": 15,
        "name": "Snowflake (Cortex AI / Snowflake Intelligence)",
        "category": "AI Data Platform (public)",
        "hq": "Bozeman, Montana, USA",
        "founded": 2012,
        "valuation_usd_b": 2.0,
        "valuation_date": "Derived: AI ARR x peer multiple",
        "valuation_source": (
            "DERIVED. Snowflake publishes an AI revenue line, so its AI "
            "business is valued like a standalone AI segment: $100M AI "
            "run-rate x the pinned 20x peer multiple = $2.0B implied AI "
            "valuation. The full market cap of $114.70B (Oct 23, 2026 close) "
            "is used only as the cap ceiling - it binds nowhere here."
        ),
        "arr_usd_m": 100,
        "arr_date": "Dec 2025 (announced with Q3 FY2026 results)",
        "arr_source": (
            "Company-stated $100M annualised AI revenue run-rate, announced a "
            "quarter ahead of schedule with Q3 FY2026 results (Dec 2025). "
            "STALE: Snowflake published NO updated AI dollar figure with Q2 "
            "FY2027 results (Sep 2, 2026) - the CFO gave only a qualitative "
            "'meaningful step-up in AI revenue'. Figure confirmed via "
            "aggregators rather than from the primary release, so it carries "
            "medium confidence."
        ),
        "arr_total_usd_m": 5430,
        "arr_attribution_note": (
            "AI-attributed only: the $100M annualised AI revenue run-rate "
            "Snowflake itself published. Total TTM revenue $5.43B; Q2 FY2027 "
            "revenue $1.55B (+35% YoY), product revenue $1.49B (+37%), NRR "
            "126%. The AI run-rate is roughly 2% of the product base - AI is "
            "the narrative and a growth driver, not the revenue engine. "
            "Because the disclosed figure is 10 months stale we under-credit "
            "Snowflake rather than guess upward."
        ),
        "summary": (
            "Cloud data platform ('AI Data Cloud') with Cortex AI, Snowflake "
            "Intelligence and Cortex Code. One of very few large-cap "
            "software companies that publishes a dollar AI revenue figure - "
            "but it has not updated that figure since Dec 2025."
        ),
        "is_digital_only": True,
        "is_pure_play_ai": False,
        "valuation_basis": "derived",
        "market_cap_usd_b": 114.7,
        "market_cap_date": (
            "Oct 23, 2026 close ($325.43/share), stockanalysis.com - "
            "single-source; a second tracker showed $101.65B for the same "
            "date, so treat as +/-12%"
        ),
    },
    # ---------------- Manus AI ---------------------------------------------
    {
        "rank_seed": 20,
        "name": "Manus AI",
        "category": "AI Agent / Consumer + Enterprise",
        "hq": "Singapore",
        "founded": 2022,
        "valuation_usd_b": 4.0,
        "valuation_date": "Oct 8, 2026 round",
        "valuation_source": (
            "Press figure, NOT company-disclosed: Bloomberg reported a ~$4B "
            "valuation on a >$500M round led by Boyu Capital and IDG (with "
            "Tencent, HSG and ZhenFund participating). Total funding ~$585M. "
            "Single-source valuation - flagged accordingly."
        ),
        "arr_usd_m": 450,
        "arr_date": "Jun 2026 (run-rate)",
        "arr_source": (
            "Reported run-rate of $400M-$500M (Jun 2026), up from $100M ARR "
            "in Dec 2025. Midpoint used. Press-reported, not "
            "company-confirmed - flagged."
        ),
        "arr_total_usd_m": 450,
        "arr_attribution_note": (
            "The whole company is the AI product, so the run-rate is "
            "AI-attributed by construction."
        ),
        "summary": (
            "General-purpose AI agent that carries out multi-step tasks end "
            "to end. Independent again since Sep 1, 2026 after Beijing "
            "unwound the Meta acquisition agreed in Dec 2025."
        ),
        "is_digital_only": True,
        "is_pure_play_ai": True,
        "valuation_basis": "actual",
    },
    # ---------------- Wonderful AI ----------------------------------------
    {
        "rank_seed": 30,
        "name": "Wonderful AI",
        "category": "AI Customer Support",
        "hq": "Tel Aviv, Israel",
        "founded": 2023,
        "valuation_usd_b": 5.0,
        "valuation_date": "Sep 2, 2026 Series C",
        "valuation_source": (
            "Company-confirmed and independently reported (Reuters, "
            "TechCrunch): $550M Series C led by Insight Partners at a $5.0B "
            "post-money valuation. Total funding raised >$800M."
        ),
        "arr_usd_m": 70,
        "arr_date": "Sep 7, 2026 (revenue run-rate)",
        "arr_source": (
            "Company-stated revenue run-rate of ~$70M (Ynet, Sep 7, 2026). A "
            "revenue run-rate is used as the ARR proxy under this list's "
            "published rule."
        ),
        "arr_total_usd_m": 70,
        "arr_attribution_note": (
            "The whole company is the AI product, so the run-rate is "
            "AI-attributed by construction. Service-led model: gross margin "
            "~52% because delivery mixes human agents with the AI."
        ),
        "summary": (
            "AI customer-service agents in Hebrew, Arabic and English for "
            "enterprise contact centres. The fastest-growing newly independent "
            "AI company in this list by revenue run-rate."
        ),
        "is_digital_only": True,
        "is_pure_play_ai": True,
        "valuation_basis": "actual",
    },
    # ---------------- SandboxAQ -------------------------------------------
    {
        "rank_seed": 55,
        "name": "SandboxAQ",
        "category": "AI for Science + Quantum Security",
        "hq": "New York, USA",
        "founded": 2022,
        "valuation_usd_b": 5.6,
        "valuation_date": "Dec 2024 round",
        "valuation_source": (
            "Company-confirmed $5.6B mark. Later figures are higher but "
            "single-source (~$9.84B per DefiLlama, May 2026; $13.89B per "
            "Forge Global), so the last CONFIRMED mark is published."
        ),
        "arr_usd_m": 17.8,
        "arr_date": "2024 estimate (latest available)",
        "arr_source": (
            "Third-party estimate ($17.8M). Revenue is not disclosed and "
            "published estimates span $8.4M-$128.2M - a 15x range - so this "
            "is a LOW-CONFIDENCE single-source input. The Information (Jul "
            "2025) reported 'lavish spending, weak growth'."
        ),
        "arr_total_usd_m": 17.8,
        "arr_attribution_note": (
            "LOW CONFIDENCE. The published estimate range is 15x wide, so "
            "this row's score should be read as indicative. Its valuation "
            "figure is much better evidenced than its revenue figure."
        ),
        "summary": (
            "Large language models for chemistry and materials science, "
            "post-quantum cryptography, and an AI-for-science platform. Also "
            "runs a quantum-sensing navigation programme (AQNav) - a hardware "
            "side-line, not the core business."
        ),
        "is_digital_only": True,
        "is_pure_play_ai": True,
        "valuation_basis": "actual",
    },
    # ---------------- Sakana AI -------------------------------------------
    {
        "rank_seed": 60,
        "name": "Sakana AI",
        "category": "Foundation Models / Research Lab",
        "hq": "Tokyo, Japan",
        "founded": 2024,
        "valuation_usd_b": 2.7,
        "valuation_date": "Nov 17, 2025 Series B",
        "valuation_source": (
            "Company-confirmed: JPY 432B (~$2.7B) post-money, per Sakana "
            "AI's own investor page (updated Apr 9, 2026). Total funding "
            "~JPY 66B (~$412M)."
        ),
        "arr_usd_m": 30,
        "arr_date": "2025-2026 estimate",
        "arr_source": (
            "Third-party estimate (~$30M). Not company-disclosed. LOW "
            "CONFIDENCE - single-source paid-database estimate."
        ),
        "arr_total_usd_m": 30,
        "arr_attribution_note": (
            "LOW CONFIDENCE. Sakana does not publish revenue; this is a "
            "single-source estimate."
        ),
        "summary": (
            "Japan's model-merging and evolutionary-AI lab (David Ha, Llion "
            "Jones). Merges and fine-tunes open models rather than "
            "pretraining from scratch, and sells subscription access to the "
            "resulting models."
        ),
        "is_digital_only": True,
        "is_pure_play_ai": True,
        "valuation_basis": "actual",
    },
    # ---------------- Luma AI ---------------------------------------------
    {
        "rank_seed": 70,
        "name": "Luma AI",
        "category": "AI Video Generation / World Models",
        "hq": "Palo Alto, USA",
        "founded": 2021,
        "valuation_usd_b": 4.0,
        "valuation_date": "Nov 19, 2025 Series C",
        "valuation_source": (
            "CNBC-confirmed: $900M Series C led by HUMAIN at a $4.0B+ "
            "post-money valuation. A Mar 2026 round at $9B was reported by "
            "Forbes but never confirmed, so the Nov 2025 mark is published. "
            "Total raised ~$1.06B."
        ),
        "arr_usd_m": None,
        "arr_date": None,
        "arr_source": (
            "Not disclosed. Sacra estimated ~$8M annualised revenue as of "
            "Dec 2024 - below this list's $10M ARR anchor and now 22 months "
            "stale, so it is not used as an input. The ARR axis therefore "
            "scores 0 under the missing-ARR rule."
        ),
        "arr_total_usd_m": None,
        "arr_attribution_note": (
            "No AI-attributed ARR at or above the $10M anchor could be "
            "evidenced, so this row is scored on valuation alone."
        ),
        "summary": (
            "3D and world-generation models (Dream Machine), neural radiance "
            "fields and Gaussian-splatting research, plus a consumer video "
            "product. Pure-play digital AI."
        ),
        "is_digital_only": True,
        "is_pure_play_ai": True,
        "valuation_basis": "actual",
    },
    # ---------------- AMI (LeCun) -----------------------------------------
    {
        "rank_seed": 75,
        "name": "Advanced Machine Intelligence (AMI)",
        "category": "Foundation Models / Research Lab",
        "hq": "New York, USA",
        "founded": 2025,
        "valuation_usd_b": 4.53,
        "valuation_date": "Mar 10, 2026 seed",
        "valuation_source": (
            "Reuters: $1.03B seed at a $3.5B pre-money mark (~$4.53B "
            "post-money), led by Lux Capital - with only ~$150M committed at "
            "signing. Single-source round report."
        ),
        "arr_usd_m": None,
        "arr_date": None,
        "arr_source": (
            "Pre-revenue. No revenue or ARR is disclosed, so the ARR axis "
            "scores 0 under the missing-ARR rule."
        ),
        "arr_total_usd_m": None,
        "arr_attribution_note": (
            "Pre-revenue frontier lab. Its research direction (JEPA world "
            "models) is oriented toward physical AI, but the company itself "
            "sells software and models, not hardware."
        ),
        "summary": (
            "Frontier research lab founded by Yann LeCun, building "
            "general-purpose AI through JEPA world models. IDENTITY NOTE: "
            "this is the lab whose name is literally 'Advanced Machine "
            "Intelligence'; a separate manufacturing-AI company also trades "
            "on the AMI acronym."
        ),
        "is_digital_only": True,
        "is_pure_play_ai": True,
        "valuation_basis": "actual",
    },
]

# ---------------------------------------------------------------------------
# 2. ROLL-UP ROWS (not ranked separately; disclosed as folded)
# ---------------------------------------------------------------------------

ROLLUPS = [
    {
        "rank_seed": 4,
        "name": "Google DeepMind",
        "category": "Roll-up (not ranked separately)",
        "hq": "London, UK",
        "founded": 2010,
        "valuation_usd_b": None,
        "arr_usd_m": None,
        "summary": (
            "Alphabet's AI research division: the Gemini model family, "
            "DeepMind Science, and robotics research. Not ranked on its own "
            "because its products ship inside Alphabet - its revenue is "
            "already inside the Alphabet AI row."
        ),
        "is_digital_only": True,
        "is_pure_play_ai": False,
        "valuation_basis": "proxy",
        "duplicate_in_ranking_with": "Google / Alphabet (AI: Gemini + Cloud AI)",
    },
    {
        "rank_seed": 3,
        "name": "Microsoft Research Asia (MSRA)",
        "category": "Roll-up (not ranked separately)",
        "hq": "Beijing, China",
        "founded": 1998,
        "valuation_usd_b": None,
        "arr_usd_m": None,
        "summary": (
            "Microsoft's Asia research lab: multimodal and speech models, "
            "and the Phi line's early research lineage. Not ranked on its "
            "own because its output ships inside Microsoft - its revenue is "
            "already inside the Microsoft AI row."
        ),
        "is_digital_only": True,
        "is_pure_play_ai": False,
        "valuation_basis": "proxy",
        "duplicate_in_ranking_with": "Microsoft (AI business)",
    },
]

# ---------------------------------------------------------------------------
# 3. EXCLUSIONS (published on the exclusions page)
# ---------------------------------------------------------------------------

NEW_EXCLUSIONS = [
    {
        "name": "Datadog",
        "why": (
            "Observability platform with an AI surface (Bits AI, Datadog for "
            "AI). Management explicitly declines to size AI revenue - Q2 "
            "2026 disclosed AI customer counts ('over 750 AI customers', all "
            "top-10 AI leaders) but no AI dollar figure - so there is no AI "
            "revenue line and AI is not the material driver. Same test as "
            "Apple. Market cap $96.8B (Oct 23, 2026)."
        ),
    },
    {
        "name": "Workato",
        "why": (
            "Enterprise automation / iPaaS repositioned around agentic AI "
            "(Agent Studio, AIRO, Enterprise MCP, AI Gateway). No AI revenue "
            "is disclosed and absolute ARR is not disclosed either. The last "
            "confirmed valuation is $5.7B (Nov 2021) - too stale to publish "
            "in a 2026 edition - and estimated revenue of roughly $200M is "
            "far below list scale."
        ),
    },
    {
        "name": "AvePoint",
        "why": (
            "Microsoft-365 data protection and governance, rebranded as a "
            "'Trust Layer for AI'. Public (Nasdaq: AVPT since Jul 2021; SGX: "
            "AVP since Sep 2025). Q2 2026 discloses SaaS revenue, total "
            "revenue and total ARR ($465.1M) but no AI revenue line, and AI "
            "is a positioning layer on a SaaS-backup core. Same test as "
            "Apple. Market cap $3.49B."
        ),
    },
    {
        "name": "Prometheus (prometheus.ai)",
        "why": (
            "Physical-AI company founded in Nov 2025 by Jeff Bezos and Vik "
            "Bajaj - an 'artificial general engineer for the physical world'. "
            "$12B Series B at a $41B post-money valuation (Jun 2026). "
            "Genuinely AI-native, but its output modality is hardware and "
            "industrial systems, which fails this list's digital-only test. "
            "NOT the open-source Prometheus monitoring project."
        ),
    },
    {
        "name": "Preferred Networks (PFN)",
        "why": (
            "AI accelerator silicon (PES / MN-P) - semiconductor-first, with "
            "no AI-attributed ARR. Also note: PFN is NOT listed on the Tokyo "
            "Stock Exchange, contrary to some third-party lists - it is "
            "unlisted."
        ),
    },
    {
        "name": "Periodic Labs",
        "why": (
            "AI-for-science lab whose delivery mechanism is autonomous "
            "robotic wet labs - physical AI, not digital. Pre-revenue since "
            "founding. Valuation $1.3B post (Sep 2025 seed); a reported "
            "~$7B round is talks only and unclosed."
        ),
    },
    {
        "name": "Enigma",
        "why": (
            "Robotics foundation models (embodied AI) - excluded as physical. "
            "The name is also ambiguous: it matches several entities, and no "
            "AI-attributed ARR or verifiable valuation is published for any "
            "of them."
        ),
    },
    {
        "name": "BeyondMath",
        "why": (
            "Generative physics AI for engineering simulation (London). $18.5M "
            "seed (Feb 2026). No valuation disclosed and no revenue - below "
            "the list's evidence threshold."
        ),
    },
    {
        "name": "Cantina Labs",
        "why": (
            "Agentic smart-contract security, incubated by Spearbit. $16.5M "
            "raised in total, including an $8M round led by Framework "
            "Ventures at a stealth exit (Jul 2026). No valuation disclosed "
            "and no revenue - below the list's evidence threshold."
        ),
    },
    {
        "name": "Openmind Research Institute",
        "why": (
            "Research institute, not a company: a non-profit AI research "
            "institute in Edmonton (Richard Sutton, Michael Bowling and "
            "colleagues), funded by $4.8M from Huawei Canada. No equity, no "
            "revenue, no valuation."
        ),
    },
    {
        "name": "BottleCap AI",
        "why": (
            "Efficient foundation models (CAP1), Prague, founded by Tomas "
            "Mikolov. $7.5M seed. No valuation disclosed and no revenue - "
            "below the list's evidence threshold."
        ),
    },
    {
        "name": "Causal Labs",
        "why": (
            "Causal-inference / general causal intelligence research (Large "
            "Physics foundation model). $6M seed (Mar 2025). No valuation "
            "disclosed and no revenue - below the list's evidence threshold."
        ),
    },
]

EXCLUSION_REASON = (
    "Excluded from the ranked top 100 because the company is hardware-first, "
    "robotics-first, semiconductor-first, physically-manufactured, is not a "
    "company at all, has no disclosed AI revenue line, or is below the list's "
    "evidence threshold (no disclosed valuation and no revenue). They are not "
    "'pure-play digital AI'."
)


def main():
    data = json.loads(DATA.read_text(encoding="utf-8"))
    companies = data["companies"]
    existing = {c["name"] for c in companies}

    added, replaced, skipped = [], [], []

    for row in NEW_ROWS + ROLLUPS:
        if row["name"] in existing:
            replaced.append(row["name"])
            companies[:] = [row if c["name"] == row["name"] else c
                            for c in companies]
        else:
            added.append(row["name"])
            companies.append(row)

    # --- exclusions -------------------------------------------------------
    ex = data["exclusions"]
    ex["reason"] = EXCLUSION_REASON
    examples = ex["examples"]
    have = {e["name"] for e in examples}
    new_ex = []
    for e in NEW_EXCLUSIONS:
        if e["name"] in have:
            examples[:] = [e if x["name"] == e["name"] else x for x in examples]
            replaced.append(e["name"])
        else:
            examples.append(e)
            new_ex.append(e["name"])

    # --- metadata ---------------------------------------------------------
    data["metadata"]["generated_at"] = GENERATED_AT
    data["metadata"]["coverage_audit"] = {
        "watchlist": "data/coverage_watchlist.json",
        "script": "scripts/coverage.py",
        "policy": (
            "Every name on an external watchlist must resolve to exactly one "
            "disposition: ranked, folded into a roll-up row, or excluded with "
            "a published reason. A name with no disposition is a coverage gap "
            "and blocks publication."
        ),
        "closed_on": GENERATED_AT,
    }

    DATA.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                    encoding="utf-8")

    print(f"companies in dataset : {len(companies)}")
    print(f"rows added           : {len(added)}")
    for n in added:
        print(f"    + {n}")
    print(f"rows replaced         : {len(replaced)}")
    print(f"exclusions added     : {len(new_ex)}")
    for n in new_ex:
        print(f"    - {n}")
    print(f"total exclusions     : {len(examples)}")


if __name__ == "__main__":
    main()
