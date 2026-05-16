from src.memory.chroma_store import add_documents
from src.ingestion.loader import load_accounts

def seed():
    accounts = load_accounts()
    documents = []
    ids = []
    metadatas = []

    notes = {
        "ACC001": "Onboarded smoothly in Jan 2023. Initial champion was the CTO. Strong adoption in engineering team. Minor API issues raised in Q4 2023 still pending resolution.",
        "ACC002": "Difficult onboarding in Q1 2023. Operations team resistant to change. CEO escalated twice in Q3. Platform stability has been a recurring concern. Renewal at serious risk.",
        "ACC003": "Excellent onboarding. Product adopted across 3 departments. Expansion discussions started in Q4 2023. Strong internal champion in VP Engineering.",
        "ACC004": "Healthcare compliance requirements caused delays during onboarding. Data migration has been a persistent issue. IT Director frustrated with pace of resolution. Renewal in jeopardy.",
        "ACC005": "Mid-market account with steady usage. No major escalations. Feature requests submitted but not yet prioritised. Renewal likely but not guaranteed.",
        "ACC006": "Enterprise account with strong executive sponsorship. Rolled out across APAC in Q2 2023. Expansion into two additional regions planned for 2024.",
        "ACC007": "SMB account that has struggled with product fit since onboarding. Sales promised features not yet on roadmap. Multiple complaints about platform speed. High churn risk.",
        "ACC008": "Steady Mid-Market account. SSO setup caused initial friction but resolved quickly. Growing user base month on month. Renewal conversation expected in Q1 2024.",
    }

    for _, acc in accounts.iterrows():
        aid = acc["account_id"]
        note = notes.get(aid, f"{acc['account_name']} is a {acc['tier']} account in {acc['industry']}. Onboarded in {acc['contract_start_date']}. Region: {acc['region']}.")
        documents.append(note)
        ids.append(aid)
        metadatas.append({
            "account_name": acc["account_name"],
            "tier": acc["tier"],
            "industry": acc["industry"],
        })

    add_documents(documents, ids, metadatas)
    print(f"Seeded {len(documents)} account context documents into ChromaDB")

if __name__ == "__main__":
    seed()