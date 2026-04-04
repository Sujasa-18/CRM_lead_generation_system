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
    def calculate_priority(row):
        lead_score    = row.get("lead_score") or 0
        churn_risk    = row.get("churn_risk") or "Low"
        decision_maker = row.get("decision_maker") or "No"
        annual_budget  = row.get("annual_budget") or "Low"
        company_size   = row.get("company_size") or "Small"

        # Boost score based on new features
        boost = 0

       # Decision maker boost
        if decision_maker == "Yes":
            boost += 20

        # Budget boost
        if annual_budget == "High":
            boost += 15
        elif annual_budget == "Medium":
            boost += 8

        # Company size boost
        if company_size == "Enterprise":
            boost += 12
        elif company_size == "Large":
            boost += 8
        elif company_size == "Medium":
            boost += 4

        # Effective score with boost
        effective_score = min(lead_score + boost, 100)

        # Priority rules using effective score
        if effective_score >= 70 and churn_risk == "High":
            return "Priority 1 - Urgent"

        elif effective_score >= 70 and churn_risk == "Medium":
            return "Priority 2 - Follow Up"

        elif effective_score >= 70 and churn_risk == "Low":
            return "Priority 3 - Nurture"

        elif effective_score >= 40 and churn_risk == "High":
            return "Priority 2 - Follow Up"

        elif effective_score >= 40 and churn_risk == "Medium":
            return "Priority 3 - Nurture"

        elif effective_score >= 40 and churn_risk == "Low":
            return "Priority 4 - Monitor"

        elif effective_score < 40 and churn_risk == "High":
            return "Priority 4 - Monitor"

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
    print(leads_df[["name", "lead_score", "churn_risk", "decision_maker",
                     "annual_budget", "company_size", "priority"]].head(10))


if __name__ == "__main__":
    run_priority_scoring()