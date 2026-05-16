import pandas as pd
import json
import os
from config import DATA_DIR

def load_accounts():
    path = os.path.join(DATA_DIR, "accounts.csv")
    return pd.read_csv(path)

def load_contacts():
    path = os.path.join(DATA_DIR, "contacts.csv")
    return pd.read_csv(path)

def load_opportunities():
    path = os.path.join(DATA_DIR, "opportunities.csv")
    return pd.read_csv(path)

def load_support_tickets():
    path = os.path.join(DATA_DIR, "support_tickets.csv")
    return pd.read_csv(path)

def load_usage_data():
    path = os.path.join(DATA_DIR, "usage_data.csv")
    return pd.read_csv(path)

def load_email_threads():
    path = os.path.join(DATA_DIR, "email_threads.json")
    with open(path, "r") as f:
        return json.load(f)

def load_all():
    return {
        "accounts": load_accounts(),
        "contacts": load_contacts(),
        "opportunities": load_opportunities(),
        "support_tickets": load_support_tickets(),
        "usage_data": load_usage_data(),
        "email_threads": load_email_threads()
    }