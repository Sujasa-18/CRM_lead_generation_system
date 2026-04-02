import pandas as pd
import mysql.connector
import numpy as np
import os

# ── Load Enhanced Dataset ──────────────────────────────────────────
base_dir = os.path.dirname(os.path.abspath(__file__))
csv_path = os.path.join(base_dir, "Lead_Scoring_Enhanced.csv")

df = pd.read_csv(csv_path)
print(f"✅ Loaded {len(df)} leads from enhanced dataset")

# ── Map Status ─────────────────────────────────────────────────────
def map_status(converted):
    return "Converted" if converted == 1 else "New"

df["status_mapped"] = df["Converted"].apply(map_status)

# ── Connect to MySQL ───────────────────────────────────────────────
conn = mysql.connector.connect(
    host="localhost",
    user="root",
    password=os.getenv("DB_PASSWORD", "197672"),
    database="crm_leads"
)
cursor = conn.cursor()

# ── Clear existing leads ───────────────────────────────────────────
cursor.execute("DELETE FROM lead_activity")
cursor.execute("DELETE FROM leads")
conn.commit()
print("✅ Existing leads cleared")

# ── Insert Leads ───────────────────────────────────────────────────
inserted = 0
skipped  = 0

for _, row in df.iterrows():
    try:
        name   = f"Lead {int(row['Lead Number'])}"
        email  = f"lead{int(row['Lead Number'])}@example.com"
        phone  = f"9{np.random.randint(100000000, 999999999)}"
        status = map_status(row["Converted"])
        notes  = str(row.get("Last Activity", "")) if pd.notna(row.get("Last Activity")) else ""

        cursor.execute(
            """
            INSERT INTO leads (
                name, email, phone, status, notes,
                job_role, years_of_experience, industry,
                company_size, annual_budget, decision_maker,
                last_contacted_days, number_of_follow_ups,
                product_demo_taken, response_time_hours,
                previous_purchase, location, age_group,
                lead_source_quality, engagement_trend
            )
            VALUES (
                %s, %s, %s, %s, %s,
                %s, %s, %s,
                %s, %s, %s,
                %s, %s,
                %s, %s,
                %s, %s, %s,
                %s, %s
            )
            """,
            (
                name, email, phone, status, notes,
                str(row.get("job_role", "")),
                int(row.get("years_of_experience", 0)),
                str(row.get("industry", "")),
                str(row.get("company_size", "")),
                str(row.get("annual_budget", "")),
                str(row.get("decision_maker", "No")),
                int(row.get("last_contacted_days", 0)),
                int(row.get("number_of_follow_ups", 0)),
                str(row.get("product_demo_taken", "No")),
                int(row.get("response_time_hours", 0)),
                str(row.get("previous_purchase", "No")),
                str(row.get("location", "")),
                str(row.get("age_group", "")),
                str(row.get("lead_source_quality", "")),
                str(row.get("engagement_trend", "")),
            )
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