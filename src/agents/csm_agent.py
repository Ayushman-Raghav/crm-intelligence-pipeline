"""
csm_agent.py — Customer Success Manager Agent
Fixes applied (v2):
  1. Explicit Green / Amber / Red threshold rubric in prompt
  2. Three calibrated few-shot examples (one per tier)
  3. rule_based_score()  — deterministic score from DA metrics
  4. calibrate_risk()    — overrides LLM when it deviates ≥ 2 tiers from rules
  5. Cleaner analytics formatting that highlights concerning metrics
"""

from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from src.memory.chroma_store import query_context
from config import OLLAMA_BASE_URL, OLLAMA_MODEL

llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.2,          
)

# ── Prompt ────────────────────────────────────────────────────────────────────

PROMPT = PromptTemplate.from_template("""
You are a senior Customer Success Manager scoring account health.
Apply the rubric below methodically, then output your assessment.

SCORING RUBRIC:
Metric                    | GREEN            | AMBER          | RED
--------------------------|------------------|----------------|------------------
login_trend_pct           | >= 0%            | -20% to 0%     | < -20%
seat_utilisation_pct      | >= 60%           | 40-60%         | < 40%
open_tickets              | 0-1              | 2-3            | >= 4
critical_tickets          | 0                | 1              | >= 2
renewal_probability       | >= 70%           | 30-70%         | < 30%
days_to_renewal           | > 60 days        | 30-60 days     | < 30 days
nps_score                 | >= 7.0           | 5.0-7.0        | < 5.0
email_sentiment           | Positive         | Neutral        | Negative
escalation_flag           | False            | -              | True
                                      
DECISION RULE:
1. Count how many RED hits and GREEN hits across all metrics.
2. If 2 or more RED hits -> overall = Red (unless 4+ GREEN hits offset -> Amber)
3. If exactly 1 RED hit -> overall = Amber
4. If 0 RED hits and any AMBER hits -> overall = Amber
5. If 0 RED hits and 0 AMBER hits -> overall = Green
6. Use renewal_probability and nps_score as tiebreakers when counts are equal.
                                      
EXAMPLES:

Example 1 - GREEN:
  login_trend_pct: +15%, seat_utilisation_pct: 82%, open_tickets: 0,
  critical_tickets: 0, renewal_probability: 88, days_to_renewal: 95,
  nps_score: 8.5, email_sentiment: Positive, escalation_flag: False
  -> RISK_LEVEL: Green, CONFIDENCE: High

Example 2 - AMBER:
  login_trend_pct: -8%, seat_utilisation_pct: 52%, open_tickets: 2,
  critical_tickets: 0, renewal_probability: 55, days_to_renewal: 45,
  nps_score: 6.2, email_sentiment: Neutral, escalation_flag: False
  -> RISK_LEVEL: Amber, CONFIDENCE: Medium

Example 3 - RED:
  login_trend_pct: -42%, seat_utilisation_pct: 28%, open_tickets: 6,
  critical_tickets: 3, renewal_probability: 12, days_to_renewal: 18,
  nps_score: 3.1, email_sentiment: Negative, escalation_flag: True
  -> RISK_LEVEL: Red, CONFIDENCE: High
                                      
ACCOUNT TO ASSESS:
{analytics}

Historical context:
{context}

Respond in this EXACT format, no extra text:
RISK_LEVEL: <Red|Amber|Green>
CONFIDENCE: <Low|Medium|High>
CHURN_REASONS:
- <reason citing a specific metric value>
- <reason citing a specific metric value>
- <reason citing a specific metric value>
RISK_SUMMARY: <2-3 sentences referencing actual numbers>
""")


# ── Rule-based scorer (guardrail) ─────────────────────────────────────────────

def rule_based_score(report: dict) -> tuple[str, int, int]:
    """
    Compute a deterministic Green / Amber / Red score from DA metrics.
    Returns (tier, red_count, green_count) for transparency.
    """
    red_hits   = 0
    green_hits = 0

    # Login trend
    trend = report.get("login_trend_pct") or 0.0
    if trend < -20:
        red_hits += 1
    elif trend >= 0:
        green_hits += 1

    # Seat utilisation
    util = report.get("seat_utilisation_pct") or 0.0
    if util < 40:
        red_hits += 1
    elif util >= 60:
        green_hits += 1

    # Open tickets
    open_t = report.get("open_tickets") or 0
    crit_t = report.get("critical_tickets") or 0
    if open_t >= 4 or crit_t >= 2:
        red_hits += 1
    elif open_t <= 1 and crit_t == 0:
        green_hits += 1

    # Renewal probability
    prob = report.get("renewal_probability")
    if prob is not None:
        if prob < 30:
            red_hits += 1
        elif prob >= 70:
            green_hits += 1

    # Days to renewal
    dtr = report.get("days_to_renewal")
    if dtr is not None:
        if dtr < 30:
            red_hits += 1
        elif dtr > 60:
            green_hits += 1

    # NPS score
    nps = report.get("nps_score")
    if nps is not None:
        if nps < 5.0:
            red_hits += 1
        elif nps >= 7.0:
            green_hits += 1

    # Days since last contact
    dlc = report.get("days_since_last_contact")
    if dlc is not None:
        if dlc > 60:
            red_hits += 1
        elif dlc <= 30:
            green_hits += 1

    # Email sentiment / escalation
    sentiment  = (report.get("email_sentiment") or "Unknown").strip()
    escalation = report.get("escalation_flag") or False
    if sentiment == "Negative" or escalation:
        red_hits += 1
    elif sentiment == "Positive":
        green_hits += 1

    # Decision logic (mirrors rubric)
    if red_hits >= 2 and green_hits < 4:
        tier = "Red"
    elif red_hits >= 2 and green_hits >= 4:
        tier = "Amber"          # strong positives offset heavy negatives
    elif red_hits == 1:
        tier = "Amber"
    elif red_hits == 0 and green_hits == 0:
        tier = "Amber"          # no data → cautious default
    else:
        tier = "Green"

    return tier, red_hits, green_hits


def calibrate_risk(llm_result: dict, rule_tier: str, red_hits: int, green_hits: int) -> dict:
    """
    Override the LLM when it deviates significantly from the rule-based score.
    Logs a calibration note for auditability.
    """
    tier_rank = {"Red": 0, "Amber": 1, "Green": 2}
    llm_tier  = llm_result.get("risk_level", "Amber")

    llm_rank  = tier_rank.get(llm_tier,   1)
    rule_rank = tier_rank.get(rule_tier,  1)
    delta     = abs(llm_rank - rule_rank)

    note = None

    if delta >= 2:
        # LLM is 2 full tiers away — hard override
        llm_result["risk_level"] = rule_tier
        llm_result["confidence"] = "Medium"
        note = (
            f"Hard override: LLM said {llm_tier}, "
            f"rules say {rule_tier} "
            f"(red_hits={red_hits}, green_hits={green_hits})"
        )
    if note:
        llm_result["calibration_note"] = note
        print(f"    ⚠ Calibrated: {note}")

    return llm_result


# ── Analytics formatter ───────────────────────────────────────────────────────

def format_analytics(report: dict) -> str:
    """
    Format DA metrics for the prompt, annotating each value with its tier bracket
    so the LLM doesn't have to infer good/bad from raw numbers alone.
    """
    def bracket(value, green_fn, amber_fn):
        if value is None:
            return "N/A"
        if green_fn(value):
            return f"{value}  ✅ GREEN"
        if amber_fn(value):
            return f"{value}  🟡 AMBER"
        return f"{value}  🔴 RED"

    trend = report.get("login_trend_pct")
    util  = report.get("seat_utilisation_pct")
    prob  = report.get("renewal_probability")
    dtr   = report.get("days_to_renewal")
    nps   = report.get("nps_score")
    dlc   = report.get("days_since_last_contact")
    open_t = report.get("open_tickets", 0) or 0
    crit_t = report.get("critical_tickets", 0) or 0

    lines = [
        f"  Account:               {report.get('account_name')} ({report.get('tier')} tier)",
        f"  MRR:                   ${report.get('mrr', 0):,}",
        f"  Industry:              {report.get('industry')}",
        f"  Region:                {report.get('region')}",
        "",
        "  — Usage —",
        f"  login_trend_pct:       {bracket(trend, lambda v: v >= 0, lambda v: -20 <= v < 0)}",
        f"  latest_logins:         {report.get('latest_logins')}",
        f"  latest_active_users:   {report.get('latest_active_users')}",
        f"  seat_utilisation_pct:  {bracket(util, lambda v: v >= 60, lambda v: 40 <= v < 60)}",
        f"  last_login_date:       {report.get('last_login_date')}",
        "",
        "  — Support —",
        f"  total_tickets:         {report.get('total_tickets')}",
        f"  open_tickets:          {bracket(open_t, lambda v: v <= 1, lambda v: v <= 3)}",
        f"  critical_tickets:      {bracket(crit_t, lambda v: v == 0, lambda v: v == 1)}",
        f"  avg_days_open:         {report.get('avg_days_open')}",
        f"  max_days_open:         {report.get('max_days_open')}",
        "",
        "  — Renewal —",
        f"  days_to_renewal:       {bracket(dtr, lambda v: v > 60, lambda v: 30 <= v <= 60)}",
        f"  renewal_probability:   {bracket(prob, lambda v: v >= 70, lambda v: 30 <= v < 70)}%",
        f"  opportunity_stage:     {report.get('opportunity_stage')}",
        f"  days_since_last_activity: {report.get('days_since_last_activity')}",
        f"  opportunity_amount:    ${report.get('opportunity_amount', 0):,}",
        "",
        "  — Relationship —",
        f"  nps_score:             {bracket(nps, lambda v: v >= 7.0, lambda v: 5.0 <= v < 7.0)}",
        f"  days_since_last_contact: {bracket(dlc, lambda v: v <= 30, lambda v: v <= 60)}",
        f"  email_sentiment:       {report.get('email_sentiment')}",
        f"  escalation_flag:       {report.get('escalation_flag')}",
        f"  latest_email_subject:  {report.get('latest_email_subject')}",
    ]
    return "\n".join(lines)


# ── Parser (unchanged logic, slightly more robust) ────────────────────────────

def parse_response(text: str) -> dict:
    lines = text.strip().split("\n")
    result = {
        "risk_level":    "Unknown",
        "confidence":    "Low",
        "churn_reasons": [],
        "risk_summary":  "",
    }
    summary_lines = []
    in_reasons    = False
    in_summary    = False

    for line in lines:
        line = line.strip()
        if line.startswith("RISK_LEVEL:"):
            raw = line.split(":", 1)[1].strip()
            # normalise casing
            result["risk_level"] = raw.capitalize() if raw.lower() in ("red","amber","green") else raw
            in_reasons = in_summary = False
        elif line.startswith("CONFIDENCE:"):
            result["confidence"] = line.split(":", 1)[1].strip().capitalize()
            in_reasons = in_summary = False
        elif line.startswith("CHURN_REASONS:"):
            in_reasons = True
            in_summary = False
        elif line.startswith("RISK_SUMMARY:"):
            in_reasons = False
            in_summary = True
            tail = line.split(":", 1)[1].strip()
            if tail:
                summary_lines.append(tail)
        elif in_reasons and line.startswith("-"):
            result["churn_reasons"].append(line[1:].strip())
        elif in_summary and line:
            summary_lines.append(line)

    result["risk_summary"] = " ".join(summary_lines).strip()
    return result


# ── Main agent ────────────────────────────────────────────────────────────────

def run_csm_agent(da_reports: list[dict]) -> list[dict]:
    results = []

    for report in da_reports:
        account_id   = report["account_id"]
        account_name = report["account_name"]

        # Rule-based score first (used as guardrail)
        rule_tier, red_hits, green_hits = rule_based_score(report)

        # Format analytics with inline bracket annotations
        analytics_text = format_analytics(report)

        # Historical context from ChromaDB
        context_docs = query_context(account_id, n_results=2)
        context_text = "\n".join(context_docs) if context_docs else "No historical context available."

        # LLM assessment
        prompt   = PROMPT.format(analytics=analytics_text, context=context_text)
        response = llm.invoke(prompt)
        parsed   = parse_response(response.content)

        # Calibrate against rule-based score
        parsed = calibrate_risk(parsed, rule_tier, red_hits, green_hits)

        result = {
            "account_id":    account_id,
            "account_name":  account_name,
            "tier":          report.get("tier"),
            "mrr":           report.get("mrr"),
            "account_owner": report.get("account_owner"),
            "rule_tier":     rule_tier,          # keep for dashboard transparency
            "red_hits":      red_hits,
            "green_hits":    green_hits,
            **parsed,
        }
        results.append(result)

        cal = f" [{result.get('calibration_note','').split(':')[0] or 'LLM agreed'}]" if result.get('calibration_note') else ""
        print(f"  [{parsed['risk_level']:5}] {account_name:<35} rules={rule_tier}{cal}")

    return results


# ── Standalone test ───────────────────────────────────────────────────────────

if __name__ == "__main__":
    from src.agents.da_agent import run_da_agent

    print("Running DA Agent...")
    da_reports = run_da_agent()

    print("\nRunning CSM Agent (sample of 5)...")
    csm_results = run_csm_agent(da_reports[:5])

    print("\n── Distribution ───────────────────────────────")
    for tier in ("Green", "Amber", "Red"):
        count = sum(1 for r in csm_results if r["risk_level"] == tier)
        print(f"  {tier}: {count}")

    print("\n── Sample Output ──────────────────────────────")
    for r in csm_results:
        print(f"\nAccount:    {r['account_name']}")
        print(f"LLM Score:  {r['risk_level']} ({r['confidence']} confidence)")
        print(f"Rule Score: {r['rule_tier']}  (red={r['red_hits']}, green={r['green_hits']})")
        if r.get("calibration_note"):
            print(f"Calibrated: {r['calibration_note']}")
        print(f"Reasons:")
        for reason in r["churn_reasons"]:
            print(f"  - {reason}")
        print(f"Summary:    {r['risk_summary']}")