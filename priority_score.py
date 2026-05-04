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
        lead_score     = row.get("lead_score") or 0
        churn_risk     = row.get("churn_risk") or "Low"
        decision_maker = row.get("decision_maker") or "No"
        annual_budget  = row.get("annual_budget") or "Low"
        company_size   = row.get("company_size") or "Small"

        # Determine base category from lead score
        if lead_score >= 70:
            category = "Hot"
        elif lead_score >= 40:
            category = "Warm"
        else:
            category = "Cold"

        # Boost points (only affects within-category ranking)
        boost = 0
        if decision_maker == "Yes":
            boost += 2
        if annual_budget == "High":
            boost += 2
        elif annual_budget == "Medium":
            boost += 1
        if company_size == "Enterprise":
            boost += 2
        elif company_size == "Large":
            boost += 1

        # ── Hot leads (score >= 70) ────────────────────────────────
        if category == "Hot":
            if churn_risk == "High":
                return "Priority 1 - Urgent"
            elif churn_risk == "Medium":
                if boost >= 3:
                    return "Priority 1 - Urgent"
                return "Priority 2 - Follow Up"
            else:
                if boost >= 4:
                    return "Priority 2 - Follow Up"
                return "Priority 3 - Nurture"

        # ── Warm leads (score 40-69) ───────────────────────────────
        elif category == "Warm":
            if churn_risk == "High":
                if boost >= 4:
                    return "Priority 2 - Follow Up"
                return "Priority 3 - Nurture"
            elif churn_risk == "Medium":
                return "Priority 3 - Nurture"
            else:
                return "Priority 4 - Monitor"

        # ── Cold leads (score < 40) ────────────────────────────────
        else:
            if churn_risk == "High":
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
    print(leads_df[["name", "lead_score", "lead_category",
                     "churn_risk", "decision_maker", "priority"]].head(10))
    print("\nPriority Distribution:")
    print(leads_df["priority"].value_counts())


if __name__ == "__main__":
    run_priority_scoring()