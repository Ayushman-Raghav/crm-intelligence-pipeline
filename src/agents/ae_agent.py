import json
import os
from datetime import datetime
from langchain_ollama import ChatOllama
from langchain_core.prompts import PromptTemplate
from config import OLLAMA_BASE_URL, OLLAMA_MODEL, OUTPUT_DIR

llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0.4,
)

EMAIL_PROMPT = PromptTemplate.from_template("""
You are an experienced Account Executive writing a professional email to a customer.

## Account Information:
- Account Name: {account_name}
- Tier: {tier}
- Risk Level: {risk_level}
- Account Owner: {account_owner}

## Churn Risk Reasons:
{churn_reasons}

## Risk Summary:
{risk_summary}

## Your Task:
Write a short, professional, and empathetic outreach email from the account owner to the primary contact.

Rules:
- Do NOT mention "churn", "risk score", or internal metrics
- Be human and conversational, not corporate
- Acknowledge any issues indirectly without admitting fault
- Propose a specific next step (call, check-in, review meeting)
- Keep it under 150 words
- Sign off with the account owner's name

Respond with just the email body, no subject line.
""")

def format_churn_reasons(reasons: list[str]) -> str:
    return "\n".join([f"- {r}" for r in reasons])

def generate_email(csm_result: dict) -> str:
    prompt = EMAIL_PROMPT.format(
        account_name=csm_result["account_name"],
        tier=csm_result["tier"],
        risk_level=csm_result["risk_level"],
        account_owner=csm_result["account_owner"],
        churn_reasons=format_churn_reasons(csm_result["churn_reasons"]),
        risk_summary=csm_result["risk_summary"],
    )
    response = llm.invoke(prompt)
    return response.content.strip()

def build_output(csm_result: dict, draft_email: str) -> dict:
    return {
        "account_id":    csm_result["account_id"],
        "account_name":  csm_result["account_name"],
        "tier":          csm_result["tier"],
        "mrr":           csm_result["mrr"],
        "account_owner": csm_result["account_owner"],
        "health_score":  csm_result["risk_level"],
        "confidence":    csm_result["confidence"],
        "risk_factors":  csm_result["churn_reasons"],
        "risk_summary":  csm_result["risk_summary"],
        "recommended_action": (
            "Immediate executive escalation call"
            if csm_result["risk_level"] == "Red"
            else "Schedule proactive check-in"
            if csm_result["risk_level"] == "Amber"
            else "Nurture for expansion opportunity"
        ),
        "draft_email":   draft_email,
        "generated_at":  datetime.now().isoformat(),
    }

def run_ae_agent(csm_results: list[dict]) -> list[dict]:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    all_outputs = []

    for result in csm_results:
        account_name = result["account_name"]
        print(f"  Generating output for {account_name}...")

        draft_email = generate_email(result)
        output = build_output(result, draft_email)
        all_outputs.append(output)

        # Save individual account file
        filename = f"{result['account_id']}_{account_name.replace(' ', '_')}.json"
        filepath = os.path.join(OUTPUT_DIR, filename)
        with open(filepath, "w") as f:
            json.dump(output, f, indent=2)

    # Save full summary report
    summary_path = os.path.join(OUTPUT_DIR, "full_report.json")
    with open(summary_path, "w") as f:
        json.dump(all_outputs, f, indent=2)

    print(f"\n  Saved {len(all_outputs)} account reports to {OUTPUT_DIR}/")
    return all_outputs

if __name__ == "__main__":
    from src.agents.da_agent import run_da_agent
    from src.agents.csm_agent import run_csm_agent

    print("Running DA Agent...")
    da_reports = run_da_agent()

    print("\nRunning CSM Agent...")
    csm_results = run_csm_agent(da_reports[:5])

    print("\nRunning AE Agent...")
    outputs = run_ae_agent(csm_results)

    print("\n── Sample Output ─────────────────────────────")
    for o in outputs:
        print(f"\nAccount:    {o['account_name']}")
        print(f"Health:     {o['health_score']} ({o['confidence']} confidence)")
        print(f"Action:     {o['recommended_action']}")
        print(f"Risk Factors:")
        for rf in o["risk_factors"]:
            print(f"  - {rf}")
        print(f"\nDraft Email:\n{o['draft_email']}")
        print("\n" + "─" * 50)