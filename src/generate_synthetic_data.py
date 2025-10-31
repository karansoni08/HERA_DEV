"""
Generate synthetic datasets for HERA (100 employees by default).

Outputs (in ./data):
 - user_directory.csv
 - phishing_simulation.csv
 - access_logs.csv
 - policy_violations.csv

Run from project root:
  python src/generate_synthetic_data.py
"""

from pathlib import Path
import pandas as pd
from faker import Faker
import random
from datetime import datetime, timedelta

# --- CONFIG ---
SEED = 42
NUM_USERS = 100
DAYS_HISTORY = 90  # generate events across last N days
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

fake = Faker()
random.seed(SEED)
Faker.seed(SEED)


def _random_times(n, days_back=DAYS_HISTORY):
    """Return n ISO timestamps randomly distributed in the last `days_back` days."""
    now = datetime.now()
    start = now - timedelta(days=days_back)
    return [
        (start + timedelta(seconds=random.randint(0, int((now - start).total_seconds())))).isoformat()
        for _ in range(n)
    ]


def generate_users(n=NUM_USERS):
    roles = ["Analyst", "Manager", "Engineer", "Finance Officer", "HR Specialist", "Contractor"]
    departments = ["Finance", "HR", "Engineering", "Marketing", "Operations"]
    privilege_levels = ["normal", "elevated", "admin"]

    rows = []
    for i in range(n):
        role = random.choice(roles)
        # Mark some users as contractors (origin_type helpful)
        employment_type = "contractor" if role == "Contractor" else "employee"
        rows.append({
            "user_id": f"USR{i+1:04d}",
            "name": fake.name(),
            "email": fake.company_email(),
            "department": random.choice(departments),
            "role": role,
            "employment_type": employment_type,
            "privilege_level": random.choices(privilege_levels, weights=[0.7, 0.25, 0.05])[0],
            "critical_asset_access": int(random.random() < 0.12),  # ~12% have critical access
            "hire_date": fake.date_between(start_date='-5y', end_date='today').isoformat()
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / "user_directory.csv", index=False)
    return df


def generate_phishing(users_df):
    rows = []
    # base probabilities by role to simulate different human risk profiles
    base_click_rate_by_role = {
        "Analyst": 0.10,
        "Manager": 0.12,
        "Engineer": 0.08,
        "Finance Officer": 0.18,
        "HR Specialist": 0.14,
        "Contractor": 0.20
    }

    for _, u in users_df.iterrows():
        attempts = random.randint(2, 4)  # number of simulated phishing tests per user
        times = _random_times(attempts)
        role = u["role"]
        base_click = base_click_rate_by_role.get(role, 0.10)
        for ts in times:
            opened = int(random.random() < min(0.9, base_click + 0.15))  # many open
            clicked = int(opened and (random.random() < base_click))
            reported = int(opened and (random.random() < 0.25))  # some report
            creds_submitted = int(clicked and (random.random() < 0.02))  # rare
            # origin_type: if creds_submitted and anomalous, label as external attacker for downstream analysis
            origin_type = "employee" if random.random() < 0.98 else "external_attacker"
            rows.append({
                "user_id": u["user_id"],
                "timestamp": ts,
                "opened": opened,
                "clicked": clicked,
                "reported": reported,
                "creds_submitted": creds_submitted,
                "origin_type": origin_type,
            })
    df = pd.DataFrame(rows).sort_values("timestamp")
    df.to_csv(DATA_DIR / "phishing_simulation.csv", index=False)
    return df


def generate_access_logs(users_df):
    rows = []
    actions = ["read", "write", "delete", "escalate", "download", "modify"]
    for _, u in users_df.iterrows():
        events_count = random.randint(8, 25)
        times = _random_times(events_count)
        for ts in times:
            action = random.choices(actions, weights=[0.5, 0.15, 0.02, 0.03, 0.2, 0.1])[0]
            data_gb = round(random.uniform(0.01, 5.0) if action in ("download", "write", "modify") else random.uniform(0.0, 0.5), 2)
            # after-hours: more likely for certain roles
            hour = datetime.fromisoformat(ts).hour
            after_hours = int(hour < 7 or hour > 19)
            anomalous_geo = int(random.random() < 0.02)  # small percent
            # origin type: mostly employee; occasionally vendor or external attacker
            r = random.random()
            if r < 0.96:
                origin_type = "employee" if u["employment_type"] == "employee" else "contractor"
            elif r < 0.99:
                origin_type = "vendor"
            else:
                origin_type = "external_attacker"

            rows.append({
                "user_id": u["user_id"],
                "timestamp": ts,
                "action": action,
                "data_gb": data_gb,
                "after_hours": after_hours,
                "anomalous_geo": anomalous_geo,
                "origin_type": origin_type,
            })
    df = pd.DataFrame(rows).sort_values("timestamp")
    df.to_csv(DATA_DIR / "access_logs.csv", index=False)
    return df


def generate_policy_violations(users_df):
    rows = []
    violation_types = ["Access Violation", "Data Transfer Without Approval", "Policy Breach", "Phishing Response"]
    for _, u in users_df.iterrows():
        # Most users have 0-1 violations, a few have more
        count = random.choices([0,1,2,3], weights=[0.7,0.2,0.08,0.02])[0]
        times = _random_times(count)
        for ts in times:
            v = random.choice(violation_types)
            severity = random.choices(["low","medium","high"], weights=[0.6,0.3,0.1])[0]
            origin_type = "employee" if random.random() < 0.98 else "contractor"
            rows.append({
                "user_id": u["user_id"],
                "timestamp": ts,
                "violation_type": v,
                "severity": severity,
                "repeat_count": random.randint(0, 3),
                "origin_type": origin_type
            })
    df = pd.DataFrame(rows).sort_values("timestamp")
    df.to_csv(DATA_DIR / "policy_violations.csv", index=False)
    return df


if __name__ == "__main__":
    print(f"Generating synthetic datasets for {NUM_USERS} users (seed={SEED})...")
    users = generate_users(NUM_USERS)
    print(" - user_directory.csv written:", DATA_DIR / "user_directory.csv")
    phishing = generate_phishing(users)
    print(" - phishing_simulation.csv written:", DATA_DIR / "phishing_simulation.csv")
    access = generate_access_logs(users)
    print(" - access_logs.csv written:", DATA_DIR / "access_logs.csv")
    violations = generate_policy_violations(users)
    print(" - policy_violations.csv written:", DATA_DIR / "policy_violations.csv")
    print("✅ All synthetic data created in ./data/")

