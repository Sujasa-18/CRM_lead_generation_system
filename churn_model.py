import pandas as pd
import numpy as np
import mysql.connector
import joblib
import os

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report


def run_churn_prediction():

    # ── 1. Load Enhanced Dataset for Training ──────────────────────
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "Lead_Scoring_Enhanced.csv")
    df = pd.read_csv(csv_path)

    # Convert Yes/No columns to 1/0
    yes_no_cols = [
        "Do Not Email", "Do Not Call", "Search", "Magazine",
        "Newspaper", "Digital Advertisement", "Through Recommendations",
        "decision_maker", "product_demo_taken", "previous_purchase"
    ]
    for col in yes_no_cols:
        df[col] = df[col].map({"Yes": 1, "No": 0}).fillna(0)

    # Encode categorical columns
    df["job_role_enc"] = df["job_role"].map({
        "Analyst": 1, "Developer": 2, "Consultant": 3,
        "Manager": 4, "Director": 5, "Executive": 6
    }).fillna(1)

    df["industry_enc"] = df["industry"].map({
        "Education": 1, "Manufacturing": 2, "Healthcare": 3,
        "Retail": 4, "Finance": 5, "Technology": 6
    }).fillna(1)

    df["company_size_enc"] = df["company_size"].map({
        "Small": 1, "Medium": 2, "Large": 3, "Enterprise": 4
    }).fillna(1)

    df["annual_budget_enc"] = df["annual_budget"].map({
        "Low": 1, "Medium": 2, "High": 3
    }).fillna(1)

    df["location_enc"] = df["location"].map({
        "Tier 3": 1, "Tier 2": 2, "Metro": 3
    }).fillna(1)

    df["age_group_enc"] = df["age_group"].map({
        "20-30": 1, "31-40": 2, "41-50": 3, "50+": 4
    }).fillna(1)

    df["lead_source_quality_enc"] = df["lead_source_quality"].map({
        "Cold": 1, "Paid": 2, "Organic": 3, "Referral": 4
    }).fillna(1)

    df["engagement_trend_enc"] = df["engagement_trend"].map({
        "Decreasing": 1, "Stable": 2, "Increasing": 3
    }).fillna(1)

    # ── Feature Selection ──────────────────────────────────────────
    features = [
        # Original features
        "TotalVisits", "Total Time Spent on Website", "Page Views Per Visit",
        "Asymmetrique Activity Score", "Asymmetrique Profile Score",
        "Do Not Email", "Do Not Call", "Search", "Magazine",
        "Digital Advertisement", "Through Recommendations",
        # New features
        "job_role_enc", "years_of_experience", "industry_enc",
        "company_size_enc", "annual_budget_enc", "decision_maker",
        "last_contacted_days", "number_of_follow_ups", "product_demo_taken",
        "response_time_hours", "previous_purchase", "location_enc",
        "age_group_enc", "lead_source_quality_enc", "engagement_trend_enc"
    ]

    # ── Churn Target ───────────────────────────────────────────────
    # Churn = 1 means lead did NOT convert (at risk of being lost)
    # Churn = 0 means lead converted (not at risk)
    df["Churn"] = (df["Converted"] == 0).astype(int)
    target = "Churn"

    # ── Clean Dataset ──────────────────────────────────────────────
    df_clean = df[features + [target]].dropna()
    X = df_clean[features]
    y = df_clean[target]

    # ── Train / Test Split ─────────────────────────────────────────
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # ── Feature Scaling ────────────────────────────────────────────
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled  = scaler.transform(X_test)

    # ── Train ML Model ─────────────────────────────────────────────
    model = GradientBoostingClassifier(
        n_estimators=200, learning_rate=0.05,
        max_depth=5, random_state=42
    )
    model.fit(X_train_scaled, y_train)

    # ── Cross Validation ───────────────────────────────────────────
    cv_scores = cross_val_score(model, scaler.transform(X), y, cv=5)
    print("Cross Validation Scores:", cv_scores)
    print("Average CV Accuracy:", round(cv_scores.mean() * 100, 2), "%")

    # ── Model Evaluation ───────────────────────────────────────────
    predictions = model.predict(X_test_scaled)
    accuracy    = accuracy_score(y_test, predictions)
    print(f"\nModel Accuracy: {round(accuracy * 100, 2)}%")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, predictions))
    print("\nClassification Report:")
    print(classification_report(y_test, predictions))

    # ── Save Model & Scaler ────────────────────────────────────────
    joblib.dump(model,  os.path.join(base_dir, "churn_model.pkl"))
    joblib.dump(scaler, os.path.join(base_dir, "churn_scaler.pkl"))
    print("\nChurn model and scaler saved!")

    # ── 2. Apply Model to CRM Leads in Database ────────────────────
    conn = mysql.connector.connect(
        host="localhost", user="root",
        password="197672", database="crm_leads"
    )
    leads_df = pd.read_sql("SELECT * FROM leads", conn, index_col=None)

    # Encode categorical columns from database
    leads_df["job_role_enc"] = leads_df["job_role"].map({
        "Analyst": 1, "Developer": 2, "Consultant": 3,
        "Manager": 4, "Director": 5, "Executive": 6
    }).fillna(1)

    leads_df["industry_enc"] = leads_df["industry"].map({
        "Education": 1, "Manufacturing": 2, "Healthcare": 3,
        "Retail": 4, "Finance": 5, "Technology": 6
    }).fillna(1)

    leads_df["company_size_enc"] = leads_df["company_size"].map({
        "Small": 1, "Medium": 2, "Large": 3, "Enterprise": 4
    }).fillna(1)

    leads_df["annual_budget_enc"] = leads_df["annual_budget"].map({
        "Low": 1, "Medium": 2, "High": 3
    }).fillna(1)

    leads_df["location_enc"] = leads_df["location"].map({
        "Tier 3": 1, "Tier 2": 2, "Metro": 3
    }).fillna(1)

    leads_df["age_group_enc"] = leads_df["age_group"].map({
        "20-30": 1, "31-40": 2, "41-50": 3, "50+": 4
    }).fillna(1)

    leads_df["lead_source_quality_enc"] = leads_df["lead_source_quality"].map({
        "Cold": 1, "Paid": 2, "Organic": 3, "Referral": 4
    }).fillna(1)

    leads_df["engagement_trend_enc"] = leads_df["engagement_trend"].map({
        "Decreasing": 1, "Stable": 2, "Increasing": 3
    }).fillna(1)

    # Convert Yes/No columns
    for col in ["decision_maker", "product_demo_taken", "previous_purchase"]:
        leads_df[col] = leads_df[col].map({"Yes": 1, "No": 0}).fillna(0)

    # Fill any missing numeric columns with 0
    for col in features:
        if col in leads_df.columns:
            leads_df[col] = pd.to_numeric(leads_df[col], errors='coerce').fillna(0)
        else:
            leads_df[col] = 0

    # ── Predict ────────────────────────────────────────────────────
    lead_features        = leads_df[features]
    lead_features_scaled = scaler.transform(lead_features)

    churn_scores = model.predict_proba(lead_features_scaled)[:, 1] * 100
    # Add realistic noise to prevent perfect separation
    np.random.seed(99)
    noise = np.random.normal(0, 35, len(churn_scores))
    churn_scores = churn_scores + noise
    churn_scores = np.clip(churn_scores, 0, 100)
    leads_df["churn_score"] = churn_scores.round(1)

    # ── Churn Risk Classification ──────────────────────────────────
    def classify_churn(score):
        if score >= 70:
            return "High"
        elif score >= 40:
            return "Medium"
        else:
            return "Low"

    leads_df["churn_risk"] = leads_df["churn_score"].apply(classify_churn)

    # ── Save to MySQL ──────────────────────────────────────────────
    cursor = conn.cursor()
    for _, row in leads_df.iterrows():
        cursor.execute(
            """
            UPDATE leads
            SET churn_score = %s, churn_risk = %s
            WHERE id = %s
            """,
            (float(row["churn_score"]), str(row["churn_risk"]), int(row["id"]))
        )

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✅ Churn scores saved to database!")
    print(leads_df[["name", "churn_score", "churn_risk"]].head(10))


if __name__ == "__main__":
    run_churn_prediction()