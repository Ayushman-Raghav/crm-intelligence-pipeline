import pandas as pd
import json
import random
from datetime import datetime, timedelta
import os

random.seed(42)

# ── helpers ──────────────────────────────────────────────────────────────
def random_date(start, end):
    return start + timedelta(days=random.randint(0, (end - start).days))

def date_str(d):
    return d.strftime("%Y-%m-%d")

# ── reference data ───────────────────────────────────────────────────────
INDUSTRIES = ["Technology", "Finance", "Healthcare", "Manufacturing",
              "Retail", "Pharma", "Legal", "Education", "Logistics", "Energy"]

REGIONS = ["North America", "Europe", "APAC", "LATAM", "Middle East"]

OWNERS = ["Sarah Johnson", "Mike Chen", "James Patel", "Emma Davis", "Liam Burke"]

TIERS = ["Enterprise", "Mid-Market", "SMB"]

TIER_MRR = {
    "Enterprise":  (5000, 15000),
    "Mid-Market":  (2000, 5000),
    "SMB":         (500,  2000),
}

TIER_SEATS = {
    "Enterprise":  (40, 120),
    "Mid-Market":  (15, 40),
    "SMB":         (5,  15),
}

HEALTH = ["Green", "Amber", "Red"]
HEALTH_WEIGHTS = [0.4, 0.35, 0.25]

COMPANY_NAMES = [
    "Acme Corp", "Globex Industries", "Initech Solutions", "Umbrella Ltd",
    "Hooli Inc", "Massive Dynamic", "Soylent Corp", "Cyberdyne Systems",
    "Veridian Dynamics", "Monarch Solutions", "Apex Dynamics", "Nexus Corp",
    "Pinnacle Tech", "Quantum Leap", "Horizon Systems", "Zenith Analytics",
    "Catalyst Group", "Vertex Solutions", "Prism Technologies", "Aurora Labs",
    "Cobalt Systems", "Delphi Corp", "Eclipse Ventures", "Fusion Works",
    "Genesis Tech", "Helios Group", "Ironclad Solutions", "Jade Systems",
    "Kinetic Labs", "Luminary Corp", "Matrix Solutions", "Nova Dynamics",
    "Orbit Technologies", "Paragon Systems", "Quartz Analytics", "Radiant Corp",
    "Sapphire Solutions", "Titan Works", "Unity Labs", "Valor Systems",
    "Warp Technologies", "Xenon Corp", "Yield Dynamics", "Zephyr Solutions",
    "Blueshift Labs", "Crestview Systems", "Deltaforce Corp", "Ember Analytics",
    "Frontier Tech", "Granite Solutions"
]

FIRST_NAMES = ["James", "Lisa", "Roberto", "Anna", "David", "Priya", "Tom",
               "Chen", "Karen", "Alex", "Emma", "Liam", "Sofia", "Noah",
               "Olivia", "Ethan", "Ava", "Mason", "Isabella", "Logan"]

LAST_NAMES = ["Wilson", "Park", "Ferretti", "Schmidt", "Moore", "Nair",
              "Bradley", "Wei", "Mills", "Turner", "Johnson", "Chen",
              "Patel", "Davis", "Burke", "Kim", "Singh", "Müller", "Rossi", "Tanaka"]

ROLES = ["CTO", "IT Director", "VP Engineering", "Operations Manager",
         "Head of Technology", "IT Manager", "CEO", "COO", "CFO", "Procurement Lead"]

EMAIL_SUBJECTS_NEGATIVE = [
    "Serious concerns about the platform",
    "We are not happy with the service",
    "Ongoing issues still not resolved",
    "Considering our options",
    "Escalating unresolved tickets",
    "Platform not delivering on promises",
    "Request for urgent call with leadership",
]

EMAIL_SUBJECTS_NEUTRAL = [
    "Following up on feature request",
    "Question about upcoming renewal",
    "Checking in on support ticket",
    "Quick question about billing",
    "Update on team onboarding",
]

EMAIL_SUBJECTS_POSITIVE = [
    "Ready to expand our contract",
    "Great experience so far",
    "Interested in additional features",
    "Renewal discussion",
    "Team loves the platform",
]

EMAIL_BODIES_NEGATIVE = [
    "We have been experiencing ongoing issues for weeks now. My team cannot do their jobs properly. We are actively evaluating other solutions.",
    "This is unacceptable. The issues raised have not been resolved and it is causing serious disruption to our operations.",
    "I want to be direct. The platform has not delivered what was promised. We are seriously considering cancelling our subscription.",
    "Our team is frustrated. Multiple tickets remain open with no resolution in sight. We need immediate action.",
    "I will be raising this with your leadership team if not resolved by end of week. This has gone on too long.",
]

EMAIL_BODIES_NEUTRAL = [
    "Just following up on the feature request. Any update on the timeline? Not urgent but would be great to have.",
    "Could you clarify the billing on our last invoice? A couple of items look off.",
    "Wanted to check in on the open ticket. Any progress on the resolution?",
    "We have a few new team members to onboard. Can you share the onboarding guide?",
    "Following up on our renewal discussion. Can we schedule a call next week?",
]

EMAIL_BODIES_POSITIVE = [
    "The platform has been fantastic for our team. We are ready to move forward with the expansion we discussed.",
    "Really happy with how things are going. The team loves the platform and we are seeing great results.",
    "We are ready to discuss expanding our usage to additional departments. Can we schedule a call?",
    "The onboarding went really smoothly. The team is up and running and very happy.",
    "Looking forward to the renewal discussion. We are very satisfied with the service.",
]

# ── accounts ─────────────────────────────────────────────────────────────
def generate_accounts(n=50):
    rows = []
    now = datetime.now()
    for i in range(1, n + 1):
        tier = random.choices(TIERS, weights=[0.3, 0.4, 0.3])[0]
        health = random.choices(HEALTH, weights=HEALTH_WEIGHTS)[0]
        mrr = random.randint(*TIER_MRR[tier])
        # FIX: contract start in the past, end date in the future
        start = now - timedelta(days=random.randint(180, 900))
        end = now + timedelta(days=random.randint(30, 365))
        rows.append({
            "account_id":         f"ACC{i:03d}",
            "account_name":       COMPANY_NAMES[i - 1],
            "industry":           random.choice(INDUSTRIES),
            "account_owner":      random.choice(OWNERS),
            "contract_start_date": date_str(start),
            "contract_end_date":  date_str(end),
            "mrr":                mrr,
            "tier":               tier,
            "region":             random.choice(REGIONS),
            "health_status":      health,
        })
    return pd.DataFrame(rows)

# ── contacts ─────────────────────────────────────────────────────────────
def generate_contacts(accounts):
    rows = []
    cid = 1
    now = datetime.now()
    for _, acc in accounts.iterrows():
        n_contacts = random.randint(1, 3)
        for j in range(n_contacts):
            # FIX: 60% contacted within last 30 days, 40% within 31-90 days
            days_ago = random.randint(1, 30) if random.random() < 0.6 else random.randint(31, 90)
            last_contacted = now - timedelta(days=days_ago)
            rows.append({
                "contact_id":          f"CON{cid:03d}",
                "account_id":          acc["account_id"],
                "first_name":          random.choice(FIRST_NAMES),
                "last_name":           random.choice(LAST_NAMES),
                "email":               f"contact{cid}@{acc['account_name'].lower().replace(' ', '')}.com",
                "role":                random.choice(ROLES),
                "is_primary":          j == 0,
                "last_contacted_date": date_str(last_contacted),
                "nps_score":           random.randint(1, 5) if acc["health_status"] == "Red"
                                       else random.randint(5, 7) if acc["health_status"] == "Amber"
                                       else random.randint(7, 10),
            })
            cid += 1
    return pd.DataFrame(rows)

# ── opportunities ────────────────────────────────────────────────────────
def generate_opportunities(accounts):
    rows = []
    now = datetime.now()
    stages = {
        "Red":   ("At Risk",       lambda mrr: (int(mrr * 10 * 0.5),  int(mrr * 10 * 0.8)),  10, 30),
        "Amber": ("Negotiation",   lambda mrr: (int(mrr * 10 * 0.8),  int(mrr * 10 * 1.2)),  50, 20),
        "Green": ("Closed Won",    lambda mrr: (int(mrr * 10 * 1.0),  int(mrr * 10 * 1.5)), 90,  5),
    }
    for _, acc in accounts.iterrows():
        stage, amt_fn, prob, last_act = stages[acc["health_status"]]
        lo, hi = amt_fn(acc["mrr"])
        close = now + timedelta(days=random.randint(30, 90))
        rows.append({
            "opportunity_id":           f"OPP{acc['account_id'][3:]}",
            "account_id":               acc["account_id"],
            "opportunity_name":         f"{acc['account_name']} Renewal 2026",
            "stage":                    stage,
            "amount":                   random.randint(lo, hi),
            "close_date":               date_str(close),
            "renewal_date":             acc["contract_end_date"],
            "probability":              prob + random.randint(-5, 5),
            "days_since_last_activity": last_act + random.randint(0, 15),
        })
    return pd.DataFrame(rows)

# ── support tickets ──────────────────────────────────────────────────────
def generate_support_tickets(accounts):
    categories = ["Technical", "Billing", "Performance", "How-To",
                  "Feature Request", "Outage", "Product Gap", "Churn Risk"]
    priorities = ["Low", "Medium", "High", "Critical"]
    rows = []
    tid = 1
    now = datetime.now()

    ticket_counts = {"Red": (4, 7), "Amber": (2, 4), "Green": (0, 2)}

    for _, acc in accounts.iterrows():
        lo, hi = ticket_counts[acc["health_status"]]
        for _ in range(random.randint(lo, hi)):
            created = now - timedelta(days=random.randint(5, 75))
            is_open = acc["health_status"] in ("Red", "Amber") and random.random() > 0.3
            resolved = None if is_open else date_str(created + timedelta(days=random.randint(1, 5)))
            days_open = (now - created).days if is_open else 0
            priority = random.choices(priorities, weights=[0.1, 0.3, 0.4, 0.2])[0] \
                       if acc["health_status"] == "Red" else \
                       random.choices(priorities, weights=[0.3, 0.4, 0.2, 0.1])[0]
            rows.append({
                "ticket_id":          f"TKT{tid:03d}",
                "account_id":         acc["account_id"],
                "subject":            f"Issue #{tid} - {random.choice(categories)} problem",
                "status":             "Open" if is_open else "Resolved",
                "priority":           priority,
                "created_date":       date_str(created),
                "resolved_date":      resolved,
                "days_open":          days_open,
                "category":           random.choice(categories),
                "satisfaction_score": None if is_open else
                                      random.randint(1, 5) if acc["health_status"] == "Red"
                                      else random.randint(6, 10),
            })
            tid += 1
    return pd.DataFrame(rows)

# ── usage data ───────────────────────────────────────────────────────────
def generate_usage_data(accounts):
    rows = []
    now = datetime.now()
    # Generate last 3 months dynamically
    months = [
        (now - timedelta(days=60)).strftime("%Y-%m"),
        (now - timedelta(days=30)).strftime("%Y-%m"),
        now.strftime("%Y-%m"),
    ]
    last_login_days = {"Green": 2, "Amber": 10, "Red": 35}

    for _, acc in accounts.iterrows():
        seats = random.randint(*TIER_SEATS[acc["tier"]])
        base_users = int(seats * (0.85 if acc["health_status"] == "Green"
                                  else 0.65 if acc["health_status"] == "Amber"
                                  else 0.45))
        for i, month in enumerate(months):
            if acc["health_status"] == "Red":
                factor = 1.0 - (i * random.uniform(0.15, 0.25))
            elif acc["health_status"] == "Amber":
                factor = 1.0 - (i * random.uniform(0.05, 0.10))
            else:
                factor = 1.0 + (i * random.uniform(0.02, 0.06))

            active = max(1, int(base_users * factor))
            logins = active * random.randint(6, 12)
            features = max(1, int(12 * factor))
            days_since_login = last_login_days[acc["health_status"]] + random.randint(0, 5)
            last_login = now - timedelta(days=days_since_login)
            rows.append({
                "account_id":            acc["account_id"],
                "month":                 month,
                "active_users":          active,
                "total_logins":          logins,
                "features_used":         features,
                "avg_session_minutes":   max(2, int(30 * factor)),
                "last_login_date":       date_str(last_login),
                "licensed_seats":        seats,
                "seat_utilisation_pct":  round((active / seats) * 100, 1),
            })
    return pd.DataFrame(rows)

# ── email threads ────────────────────────────────────────────────────────
def generate_email_threads(accounts, contacts):
    threads = []
    eid = 1
    now = datetime.now()
    for _, acc in accounts.iterrows():
        primary = contacts[
            (contacts["account_id"] == acc["account_id"]) &
            (contacts["is_primary"] == True)
        ]
        if primary.empty:
            continue
        contact = primary.iloc[0]
        health = acc["health_status"]

        if health == "Red":
            sentiment = "Negative"
            subject = random.choice(EMAIL_SUBJECTS_NEGATIVE)
            body = random.choice(EMAIL_BODIES_NEGATIVE)
            escalation = True
        elif health == "Amber":
            sentiment = "Neutral"
            subject = random.choice(EMAIL_SUBJECTS_NEUTRAL)
            body = random.choice(EMAIL_BODIES_NEUTRAL)
            escalation = False
        else:
            sentiment = "Positive"
            subject = random.choice(EMAIL_SUBJECTS_POSITIVE)
            body = random.choice(EMAIL_BODIES_POSITIVE)
            escalation = False

        date = now - timedelta(days=random.randint(1, 45))
        threads.append({
            "thread_id":      f"EMAIL{eid:03d}",
            "account_id":     acc["account_id"],
            "contact_email":  contact["email"],
            "date":           date_str(date),
            "direction":      "inbound",
            "subject":        subject,
            "body":           body,
            "sentiment":      sentiment,
            "escalation_flag": escalation,
        })
        eid += 1
    return threads

# ── main ─────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    os.makedirs("data/sample", exist_ok=True)

    print("Generating accounts...")
    accounts = generate_accounts(50)

    print("Generating contacts...")
    contacts = generate_contacts(accounts)

    print("Generating opportunities...")
    opportunities = generate_opportunities(accounts)

    print("Generating support tickets...")
    tickets = generate_support_tickets(accounts)

    print("Generating usage data...")
    usage = generate_usage_data(accounts)

    print("Generating email threads...")
    emails = generate_email_threads(accounts, contacts)

    accounts.to_csv("data/sample/accounts.csv", index=False)
    contacts.to_csv("data/sample/contacts.csv", index=False)
    opportunities.to_csv("data/sample/opportunities.csv", index=False)
    tickets.to_csv("data/sample/support_tickets.csv", index=False)
    usage.to_csv("data/sample/usage_data.csv", index=False)
    with open("data/sample/email_threads.json", "w") as f:
        json.dump(emails, f, indent=2)

    print("\nDone. Summary:")
    print(f"  Accounts:        {len(accounts)}")
    print(f"  Contacts:        {len(contacts)}")
    print(f"  Opportunities:   {len(opportunities)}")
    print(f"  Support Tickets: {len(tickets)}")
    print(f"  Usage Records:   {len(usage)}")
    print(f"  Email Threads:   {len(emails)}")