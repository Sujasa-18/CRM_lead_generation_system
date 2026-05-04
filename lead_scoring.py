import pandas as pd
import numpy as np
import mysql.connector
import joblib
import os

from sklearn.ensemble import GradientBoostingClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split, cross_val_score
from sklearn.metrics import accuracy_score, confusion_matrix, classification_report


def run_lead_scoring():

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
    target = "Converted"

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
    n_estimators=100,
    learning_rate=0.05,
    max_depth=3,
    min_samples_split=10,
    min_samples_leaf=5,
    subsample=0.8,
    random_state=42
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
    joblib.dump(model,   os.path.join(base_dir, "lead_scoring_model.pkl"))
    joblib.dump(scaler,  os.path.join(base_dir, "scaler.pkl"))
    joblib.dump(features, os.path.join(base_dir, "lead_scoring_features.pkl"))
    print("\nModel, scaler and features saved!")

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

    raw_scores = model.predict_proba(lead_features_scaled)[:, 1]
# Min-max normalization to use full 0-100 range
    min_score = raw_scores.min()
    max_score = raw_scores.max()
    scores = ((raw_scores - min_score) / (max_score - min_score)) * 100
    scores = np.clip(scores, 0, 100)
    leads_df["lead_score"] = scores.round(1)

    # ── Lead Category ──────────────────────────────────────────────
    def categorize(score):
        if score >= 70:
            return "Hot"
        elif score >= 40:
            return "Warm"
        else:
            return "Cold"

    leads_df["lead_category"] = leads_df["lead_score"].apply(categorize)

    # ── Save to MySQL ──────────────────────────────────────────────
    cursor = conn.cursor()
    for _, row in leads_df.iterrows():
        cursor.execute(
            """
            UPDATE leads
            SET lead_score = %s, lead_category = %s
            WHERE id = %s
            """,
            (float(row["lead_score"]), str(row["lead_category"]), int(row["id"]))
        )

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✅ Lead scores saved to database!")
    print(leads_df[["name", "lead_score", "lead_category"]].head(10))


if __name__ == "__main__":
    run_lead_scoring()