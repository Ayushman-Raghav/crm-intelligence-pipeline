import pandas as pd
from datetime import datetime
from src.ingestion.loader import load_all

TODAY = datetime.now()

def compute_login_trend(usage: pd.DataFrame, account_id: str) -> dict:
    acct = usage[usage["account_id"] == account_id].sort_values("month")
    if len(acct) < 2:
        return {"login_trend_pct": 0.0, "latest_logins": 0}
    first = acct.iloc[0]["total_logins"]
    last  = acct.iloc[-1]["total_logins"]
    trend = round(((last - first) / first) * 100, 1) if first > 0 else 0.0
    return {
        "login_trend_pct":    trend,
        "latest_logins":      int(last),
        "latest_active_users": int(acct.iloc[-1]["active_users"]),
        "seat_utilisation_pct": float(acct.iloc[-1]["seat_utilisation_pct"]),
        "last_login_date":    acct.iloc[-1]["last_login_date"],
    }

def compute_ticket_signals(tickets: pd.DataFrame, account_id: str) -> dict:
    acct = tickets[tickets["account_id"] == account_id]
    open_tickets = acct[acct["status"] == "Open"]
    return {
        "total_tickets":       len(acct),
        "open_tickets":        len(open_tickets),
        "critical_tickets":    len(open_tickets[open_tickets["priority"] == "Critical"]),
        "avg_days_open":       round(open_tickets["days_open"].mean(), 1) if not open_tickets.empty else 0.0,
        "max_days_open":       int(open_tickets["days_open"].max()) if not open_tickets.empty else 0,
    }

def compute_renewal_signals(opportunities: pd.DataFrame, account_id: str) -> dict:
    acct = opportunities[opportunities["account_id"] == account_id]
    if acct.empty:
        return {"days_to_renewal": None, "renewal_probability": None, "opportunity_stage": None}
    opp = acct.iloc[0]
    renewal_date = datetime.strptime(opp["renewal_date"], "%Y-%m-%d")
    days_to_renewal = (renewal_date - TODAY).days
    return {
        "days_to_renewal":       days_to_renewal,
        "renewal_probability":   int(opp["probability"]),
        "opportunity_stage":     opp["stage"],
        "days_since_last_activity": int(opp["days_since_last_activity"]),
        "opportunity_amount":    int(opp["amount"]),
    }

def compute_contact_signals(contacts: pd.DataFrame, account_id: str) -> dict:
    acct = contacts[contacts["account_id"] == account_id]
    primary = acct[acct["is_primary"] == True]
    nps = float(primary.iloc[0]["nps_score"]) if not primary.empty else None
    last_contacted = primary.iloc[0]["last_contacted_date"] if not primary.empty else None
    if last_contacted:
        days_since = (TODAY - datetime.strptime(last_contacted, "%Y-%m-%d")).days
    else:
        days_since = None
    return {
        "nps_score":                nps,
        "days_since_last_contact":  days_since,
    }

def compute_email_signals(emails: list, account_id: str) -> dict:
    acct = [e for e in emails if e["account_id"] == account_id]
    if not acct:
        return {"email_sentiment": "Unknown", "escalation_flag": False}
    latest = sorted(acct, key=lambda x: x["date"], reverse=True)[0]
    return {
        "email_sentiment":  latest["sentiment"],
        "escalation_flag":  latest["escalation_flag"],
        "latest_email_subject": latest["subject"],
    }

def run_da_agent() -> list[dict]:
    data = load_all()
    accounts    = data["accounts"]
    contacts    = data["contacts"]
    opportunities = data["opportunities"]
    tickets     = data["support_tickets"]
    usage       = data["usage_data"]
    emails      = data["email_threads"]

    results = []
    for _, acc in accounts.iterrows():
        aid = acc["account_id"]
        report = {
            "account_id":   aid,
            "account_name": acc["account_name"],
            "tier":         acc["tier"],
            "mrr":          int(acc["mrr"]),
            "industry":     acc["industry"],
            "account_owner": acc["account_owner"],
            "region":       acc["region"],
        }
        report.update(compute_login_trend(usage, aid))
        report.update(compute_ticket_signals(tickets, aid))
        report.update(compute_renewal_signals(opportunities, aid))
        report.update(compute_contact_signals(contacts, aid))
        report.update(compute_email_signals(emails, aid))
        results.append(report)

    return results

if __name__ == "__main__":
    results = run_da_agent()
    for r in results[:3]:
        print("\n── Account ──────────────────────────────")
        for k, v in r.items():
            print(f"  {k:<30} {v}")