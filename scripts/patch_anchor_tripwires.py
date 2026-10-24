"""
patch_anchor_tripwires.py - write the binding tripwire into the review policy.

The policy has two tripwires for the fixed bounds, and they disagree at the
top of the ARR axis:

  * the RE-ANCHOR TRIGGER (one third of the axis span past a bound) would
    not fire on the ARR ceiling until $2.15T - 21.5x Anthropic's ARR
  * the STALE-ANCHOR SCORE FLAG (a score above 100) fires as soon as
    Anthropic's ARR passes ~$103.7B - 1.037x its current ARR

So the binding tripwire on the ARR ceiling is the score flag, not the
re-anchor trigger, and it is close. That belongs in the policy, not in
someone's head.

Also adds the margin table to the methodology so a reader can see how much
room each bound has.

Run:
    python scripts/patch_anchor_tripwires.py
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main():
    # ---------------------------------------------------------------- policy
    cfg_path = ROOT / "data" / "model_config.json"
    cfg = json.loads(cfg_path.read_text(encoding="utf-8"))
    rp = cfg["review_policy"]
    rp["score_flag_trigger"] = (
        "A score above 100 is the signal that an anchor is tight, and on the "
        "ARR ceiling it is the BINDING tripwire, firing long before the "
        "re-anchor trigger. With the current bounds and Anthropic's valuation "
        "at $965B, the #1 score crosses 100 when Anthropic's ARR passes about "
        "$103.7B - 1.037x its current run-rate. The re-anchor trigger on the "
        "same bound would not fire until $2.15T. If the score flag fires, "
        "review the bounds; do not wait for the re-anchor trigger. Note that "
        "widening the ARR ceiling is not free: it compresses the ARR axis and "
        "shifts the balance back towards valuation."
    )
    rp["bounds_provenance"] = (
        "All four bounds trace to two companies at the time of the pin: "
        "Reworkd AI set the two floors ($0.1B valuation, $10M ARR) and "
        "Anthropic set the two ceilings ($1,000B valuation, $100,000M ARR). "
        "Reworkd has since fallen out of the Top 100, so the floors now sit "
        "above the bottom of the list - dead space at the bottom, almost no "
        "headroom at the top of ARR. That is the fixed-bounds design working "
        "as intended: the axis does not move when the composition does. "
        "scripts/anchor_headroom.py reports the margins."
    )
    cfg_path.write_text(json.dumps(cfg, indent=2, ensure_ascii=False) + "\n",
                        encoding="utf-8")
    print("data/model_config.json: review_policy updated")

    # ----------------------------------------------------------- methodology
    p = ROOT / "methodology.html"
    t = p.read_text(encoding="utf-8")

    old = ("          figure scores negative. That is a monotonicity break, and on a live\n"
           "          list it would surface the first time a very small company joined.\n"
           "          The valuation floor earns its keep the same way: raise it from $0.1B\n"
           "          to $1B and Otter.ai &mdash; a real company with a $0.5B valuation &mdash;\n"
           "          would drop below companies with no valuation mark at all.\n"
           "        </p>\n")

    new = ("          figure scores negative. That is a monotonicity break, and on a live\n"
           "          list it would surface the first time a very small company joined.\n"
           "          The valuation floor earns its keep the same way: raise it from $0.1B\n"
           "          to $1B and Otter.ai &mdash; a real company with a $0.5B valuation &mdash;\n"
           "          would drop below companies with no valuation mark at all.\n"
           "        </p>\n"
           "        <h3>How much room is left on each bound?</h3>\n"
           "        <p>\n"
           "          All four bounds trace to two companies at the time of the pin:\n"
           "          Reworkd AI set the two floors ($0.1B valuation, $10M ARR) and\n"
           "          Anthropic set the two ceilings ($1,000B valuation, $100,000M ARR).\n"
           "          Reworkd has since fallen out of the Top 100, so the floors now sit\n"
           "          above the bottom of the list. That is the fixed-bounds design\n"
           "          working as intended &mdash; the axis did not move when the composition\n"
           "          did &mdash; but it leaves the headroom asymmetric: dead space at the\n"
           "          bottom, almost none at the top of ARR.\n"
           "        </p>\n"
           "        <table class=\"rank\" style=\"margin:14px 0;\">\n"
           "          <thead>\n"
           "            <tr>\n"
           "              <th>Bound</th>\n"
           "              <th class=\"num\">Bound</th>\n"
           "              <th>Nearest row</th>\n"
           "              <th class=\"num\">Value</th>\n"
           "              <th class=\"num\">Re-anchor trigger</th>\n"
           "              <th class=\"num\">Margin</th>\n"
           "            </tr>\n"
           "          </thead>\n"
           "          <tbody>\n"
           "            <tr><td>Valuation ceiling</td><td class=\"num\">$1,000B</td>"
           "<td>Anthropic</td><td class=\"num\">$965B</td>"
           "<td class=\"num\">$21,544B</td><td class=\"num\">22.3&times;</td></tr>\n"
           "            <tr><td>ARR ceiling</td><td class=\"num\">$100,000M</td>"
           "<td>Anthropic</td><td class=\"num\">$100,000M</td>"
           "<td class=\"num\">$2,154,435M</td><td class=\"num\">21.5&times;</td></tr>\n"
           "            <tr><td>Valuation floor</td><td class=\"num\">$0.1B</td>"
           "<td>Otter.ai</td><td class=\"num\">$0.5B</td>"
           "<td class=\"num\">$0.0046B</td><td class=\"num\">107.7&times;</td></tr>\n"
           "            <tr><td>ARR floor</td><td class=\"num\">$10M</td>"
           "<td>SandboxAQ</td><td class=\"num\">$17.8M</td>"
           "<td class=\"num\">$0.46M</td><td class=\"num\">38.3&times;</td></tr>\n"
           "          </tbody>\n"
           "        </table>\n"
           "        <p>\n"
           "          Every re-anchor margin is enormous. But the policy has a second,\n"
           "          tighter tripwire: scores are not clipped, so a score above 100 is\n"
           "          the signal that an anchor is tight. On the ARR ceiling that flag\n"
           "          is the <em>binding</em> one &mdash; with Anthropic's valuation at\n"
           "          $965B, the #1 score crosses 100 when Anthropic's ARR passes about\n"
           "          <strong>$103.7B</strong>, 1.037&times; its current run-rate, whereas the\n"
           "          re-anchor trigger on the same bound would not fire until $2.15T.\n"
           "          Both numbers are in <code>data/model_config.json</code> under\n"
           "          <code>review_policy</code>. If the score flag fires, review the bounds;\n"
           "          do not wait for the re-anchor trigger. Widening the ARR ceiling is not\n"
           "          free &mdash; it compresses the ARR axis and shifts the balance back\n"
           "          towards valuation.\n"
           "        </p>\n")

    if t.count(old) != 1:
        raise SystemExit(f"FAIL: anchor paragraph found {t.count(old)} times")
    t = t.replace(old, new)
    p.write_text(t, encoding="utf-8")
    print("methodology.html: anchor headroom section added")


if __name__ == "__main__":
    main()
