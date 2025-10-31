from pathlib import Path
import pandas as pd
from faker import Faker
import random

fake = Faker()
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# ---------- 1. USER DIRECTORY ----------
def generate_users(n=200):
    roles = ["Analyst", "Manager", "Engineer", "Finance Officer", "HR Specialist"]
    departments = ["Finance", "HR", "Engineering", "Marketing", "Operations"]
    privilege_levels = ["normal", "elevated", "admin"]

    rows = []
    for i in range(n):
        rows.append({
            "user_id": f"USR{i+1:04d}",
            "name": fake.name(),
            "department": random.choice(departments),
            "role": random.choice(roles),
            "privilege_level": random.choice(privilege_levels),
            "critical_asset_access": random.choice([0, 1])
        })
    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / "user_directory.csv", index=False)
    return df


# ---------- 2. PHISHING SIMULATION ----------
def generate_phishing(users):
    rows = []
    for _, u in users.iterrows():
        attempts = random.randint(1, 3)
        for _ in range(attempts):
            rows.append({
                "user_id": u["user_id"],
                "opened": random.choice([0, 1]),
                "clicked": random.choice([0, 1]),
                "reported": random.choice([0, 1]),
                "creds_submitted": random.choice([0, 1])
            })
    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / "phishing_simulation.csv", index=False)
    return df


# ---------- 3. ACCESS LOGS ----------
def generate_access_logs(users):
    actions = ["read", "write", "delete", "escalate", "download"]
    rows = []
    for _, u in users.iterrows():
        for _ in range(random.randint(5, 15)):
            rows.append({
                "user_id": u["user_id"],
                "action": random.choice(actions),
                "data_gb": round(random.uniform(0.1, 3.0), 2),
                "after_hours": random.choice([0, 1]),
                "anomalous_geo": random.choice([0, 1])
            })
    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / "access_logs.csv", index=False)
    return df


# ---------- 4. POLICY VIOLATIONS ----------
def generate_policy_violations(users):
    violations = ["Access Violation", "Data Transfer", "Policy Breach", "Phishing Response"]
    rows = []
    for _, u in users.iterrows():
        for _ in range(random.randint(0, 3)):
            rows.append({
                "user_id": u["user_id"],
                "violation_type": random.choice(violations),
                "severity": random.choice(["low", "medium", "high"]),
                "repeat_count": random.randint(0, 3)
            })
    df = pd.DataFrame(rows)
    df.to_csv(DATA_DIR / "policy_violations.csv", index=False)
    return df


if __name__ == "__main__":
    users = generate_users()
    generate_phishing(users)
    generate_access_logs(users)
    generate_policy_violations(users)
    print("✅ Synthetic data created in /data/")

