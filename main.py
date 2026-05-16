import json
import os
from datetime import datetime
from src.agents.da_agent import run_da_agent
from src.agents.csm_agent import run_csm_agent
from src.agents.ae_agent import run_ae_agent
from config import OUTPUT_DIR

def run_pipeline():
    start = datetime.now()
    print("=" * 60)
    print("   CRM Intelligence Pipeline")
    print(f"   Started: {start.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # Step 1 — DA Agent
    print("\n[1/3] Running Data Analyst Agent...")
    da_reports = run_da_agent()
    print(f"      Analysed {len(da_reports)} accounts")

    # Split by urgency — process Red accounts first
    red_accounts   = [r for r in da_reports if r.get("email_sentiment") == "Negative"
                      or (r.get("renewal_probability") or 100) < 20
                      or (r.get("open_tickets") or 0) >= 4]
    other_accounts = [r for r in da_reports if r not in red_accounts]
    ordered = red_accounts + other_accounts
    print(f"      Priority accounts (likely Red): {len(red_accounts)}")

    # Step 2 — CSM Agent
    print("\n[2/3] Running Customer Success Manager Agent...")
    csm_results = run_csm_agent(ordered)

    # Step 3 — AE Agent
    print("\n[3/3] Running Account Executive Agent...")
    outputs = run_ae_agent(csm_results)

    # Summary
    end = datetime.now()
    duration = (end - start).seconds

    red   = [o for o in outputs if o["health_score"] == "Red"]
    amber = [o for o in outputs if o["health_score"] == "Amber"]
    green = [o for o in outputs if o["health_score"] == "Green"]

    print("\n" + "=" * 60)
    print("   Pipeline Complete")
    print(f"   Duration: {duration}s")
    print(f"   Accounts processed: {len(outputs)}")
    print(f"   🔴 Red:   {len(red)}")
    print(f"   🟡 Amber: {len(amber)}")
    print(f"   🟢 Green: {len(green)}")
    print("=" * 60)

    print("\n   Accounts requiring immediate action:")
    for o in red:
        print(f"   → {o['account_name']} ({o['tier']}) — {o['recommended_action']}")

    print(f"\n   Full report saved to: {OUTPUT_DIR}/full_report.json")

if __name__ == "__main__":
    run_pipeline()