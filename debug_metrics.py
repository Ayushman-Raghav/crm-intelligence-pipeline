from src.agents.da_agent import run_da_agent

reports = run_da_agent()

# Count how often each metric hits RED across all accounts
counters = {
    "login_trend":      0,
    "seat_util":        0,
    "tickets":          0,
    "renewal_prob":     0,
    "days_to_renewal":  0,
    "nps":              0,
    "last_contact":     0,
    "sentiment":        0,
}

for r in reports:
    if (r.get("login_trend_pct") or 0) < -20:          counters["login_trend"] += 1
    if (r.get("seat_utilisation_pct") or 0) < 40:       counters["seat_util"] += 1
    if (r.get("open_tickets") or 0) >= 4 or (r.get("critical_tickets") or 0) >= 2:
                                                         counters["tickets"] += 1
    if (r.get("renewal_probability") or 100) < 30:      counters["renewal_prob"] += 1
    if (r.get("days_to_renewal") or 999) < 30:          counters["days_to_renewal"] += 1
    if (r.get("nps_score") or 10) < 5.0:               counters["nps"] += 1
    if (r.get("days_since_last_contact") or 0) > 60:   counters["last_contact"] += 1
    if (r.get("email_sentiment") or "") == "Negative" or r.get("escalation_flag"):
                                                         counters["sentiment"] += 1

print("RED hits per metric across 50 accounts:")
for k, v in sorted(counters.items(), key=lambda x: -x[1]):
    print(f"  {k:<20} {v:>3} / 50  {'⚠ ALWAYS RED' if v == 50 else ''}")