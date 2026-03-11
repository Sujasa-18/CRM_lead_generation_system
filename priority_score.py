import mysql.connector
import pandas as pd
import os


def run_priority_scoring():

    # ── Connect to MySQL ───────────────────────────────────────────
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="197672",
        database="crm_leads"
    )

    leads_df = pd.read_sql("SELECT * FROM leads", conn, index_col=None)

    # ── Priority Logic ─────────────────────────────────────────────
    # Combines lead_score and churn_risk into one priority ranking
    def calculate_priority(row):
        lead_score = row.get("lead_score") or 0
        churn_risk = row.get("churn_risk") or "Low"

        # High lead score + High churn risk = Act immediately
        if lead_score >= 70 and churn_risk == "High":
            return "Priority 1 - Urgent"

        # High lead score + Medium churn risk = Close the deal
        elif lead_score >= 70 and churn_risk == "Medium":
            return "Priority 2 - Follow Up"

        # High lead score + Low churn risk = Nurture
        elif lead_score >= 70 and churn_risk == "Low":
            return "Priority 3 - Nurture"

        # Medium lead score + High churn risk = Act soon
        elif lead_score >= 40 and churn_risk == "High":
            return "Priority 2 - Follow Up"

        # Medium lead score + Medium churn risk = Monitor
        elif lead_score >= 40 and churn_risk == "Medium":
            return "Priority 3 - Nurture"

        # Medium lead score + Low churn risk = Low priority
        elif lead_score >= 40 and churn_risk == "Low":
            return "Priority 4 - Monitor"

        # Low lead score + High churn risk = Likely lost
        elif lead_score < 40 and churn_risk == "High":
            return "Priority 4 - Monitor"

        # Low lead score = No action needed
        else:
            return "Priority 5 - No Action"

    leads_df["priority"] = leads_df.apply(calculate_priority, axis=1)

    # ── Save to MySQL ──────────────────────────────────────────────
    cursor = conn.cursor()
    for _, row in leads_df.iterrows():
        cursor.execute(
            "UPDATE leads SET priority = %s WHERE id = %s",
            (str(row["priority"]), int(row["id"]))
        )

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✅ Priority scores saved to database!")
    print(leads_df[["name", "lead_score", "churn_risk", "priority"]].head(10))


if __name__ == "__main__":
    run_priority_scoring()