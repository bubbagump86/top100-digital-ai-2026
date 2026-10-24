"""patch_final_snowflake_copy.py - last two copy gaps from the Snowflake row.

1. The full-market-cap comparison list after the worked examples omitted
   Snowflake's $114.7B.
2. "Salesforce ... is the starkest example" - Snowflake is starker still
   ($2B implied AI valuation against a $114.7B cap = 1.7%).

Run: python scripts/patch_final_snowflake_copy.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
P = ROOT / "methodology.html"

PAIRS = [
    ("Baidu $27.4B, Salesforce $280B, ServiceNow $200B.",
     "Baidu $27.4B, Salesforce $280B, ServiceNow $200B, Snowflake $114.7B."),

    ("market cap. Salesforce's implied AI valuation of $16B against a\n"
     "          $280B market cap is the starkest example: Agentforce is real, and it\n"
     "          is also ~6% of what the market pays for Salesforce.",
     "market cap. Salesforce's implied AI valuation of $16B against a\n"
     "          $280B market cap is a stark case: Agentforce is real, and it is also\n"
     "          only ~6% of what the market pays for Salesforce. Snowflake is starker\n"
     "          still &mdash; $2B of implied AI valuation against a $114.7B market cap\n"
     "          is 1.7%."),
]


def main():
    t = P.read_text(encoding="utf-8")
    for old, new in PAIRS:
        n = t.count(old)
        if n != 1:
            raise SystemExit(f"FAIL: {n} occurrences for {old[:70]!r}")
        t = t.replace(old, new)
    P.write_text(t, encoding="utf-8")
    print(f"methodology.html: {len(PAIRS)} edits applied")


if __name__ == "__main__":
    main()
