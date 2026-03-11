import pandas as pd
import mysql.connector
import numpy as np
import os

# ── Load Kaggle Dataset ────────────────────────────────────────────
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "Lead Scoring.csv")

df = pd.read_csv(csv_path)
print(f"✅ Loaded {len(df)} leads from Kaggle dataset")

# ── Map Status ─────────────────────────────────────────────────────
def map_status(converted):
    if converted == 1:
        return "Converted"
    else:
        return "New"

df["status_mapped"] = df["Converted"].apply(map_status)

# ── Connect to MySQL ───────────────────────────────────────────────
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password="197672",
    database="crm_leads"
)
cursor = conn.cursor()

# ── Insert Leads ───────────────────────────────────────────────────
inserted = 0
skipped = 0

for _, row in df.iterrows():
    try:
        # Generate name from dataset (use Lead Number as fallback)
        name = f"Lead {int(row['Lead Number'])}"

        # Generate a realistic email
        email = f"lead{int(row['Lead Number'])}@example.com"

        # Generate a realistic phone
        phone = f"9{np.random.randint(100000000, 999999999)}"

        # Map status
        status = map_status(row["Converted"])

        # Notes from Last Activity
        notes = str(row.get("Last Activity", "")) if pd.notna(row.get("Last Activity")) else ""

        cursor.execute(
            """
            INSERT INTO leads (name, email, phone, status, notes)
            VALUES (%s, %s, %s, %s, %s)
            """,
            (name, email, phone, status, notes)
        )
        inserted += 1

    except Exception as e:
        skipped += 1
        continue

conn.commit()
cursor.close()
conn.close()

print(f"✅ {inserted} leads inserted successfully!")
print(f"⚠️  {skipped} leads skipped due to errors")
print("✅ Database import complete!")