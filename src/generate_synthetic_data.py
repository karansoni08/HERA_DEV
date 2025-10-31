from pathlib import Path
import pandas as pd
from faker import Faker
import random

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)
fake = Faker()

def generate_users(n=50):
    roles = ["Analyst","Manager","Engineer","Finance Officer","HR Specialist"]
    depts = ["Finance","HR","Engineering","Marketing","Operations"]
    privs = ["normal","elevated","admin"]
    rows = []
    for i in range(n):
        rows.append({
            "user_id": f"USR{i+1:04d}",
            "department": random.choice(depts),
            "role": random.choice(roles),
            "privilege_level": random.choice(privs),
            "critical_asset_access": random.choice([0,1])
        })
    return pd.DataFrame(rows)

if __name__ == "__main__":
    users = generate_users()
    users.to_csv(DATA_DIR / "user_directory.csv", index=False)
    print("✅ data/user_directory.csv created")
