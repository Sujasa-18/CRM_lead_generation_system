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

    # ── 1. Load & Train on Kaggle Dataset ──────────────────────────
    base_dir = os.path.dirname(os.path.abspath(__file__))
    csv_path = os.path.join(base_dir, "Lead Scoring.csv")
    df = pd.read_csv(csv_path)

    # Convert Yes/No columns to 1/0
    yes_no_cols = [
        "Do Not Email", "Do Not Call", "Search", "Magazine",
        "Newspaper Article", "Digital Advertisement", "Through Recommendations"
    ]
    for col in yes_no_cols:
        df[col] = df[col].map({"Yes": 1, "No": 0}).fillna(0)

    # ── Feature Selection ──────────────────────────────────────────
    features = [
        "TotalVisits", "Total Time Spent on Website", "Page Views Per Visit",
        "Asymmetrique Activity Score", "Asymmetrique Profile Score",
        "Do Not Email", "Do Not Call", "Search", "Magazine",
        "Newspaper Article", "Digital Advertisement", "Through Recommendations"
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
    X_test_scaled = scaler.transform(X_test)

    # ── Train ML Model ─────────────────────────────────────────────
    model = GradientBoostingClassifier(n_estimators=100, learning_rate=0.1, random_state=42)
    model.fit(X_train_scaled, y_train)

    # ── Cross Validation ───────────────────────────────────────────
    cv_scores = cross_val_score(model, scaler.transform(X), y, cv=5)
    print("Cross Validation Scores:", cv_scores)
    print("Average CV Accuracy:", round(cv_scores.mean() * 100, 2), "%")

    # ── Model Evaluation ───────────────────────────────────────────
    predictions = model.predict(X_test_scaled)
    accuracy = accuracy_score(y_test, predictions)
    print(f"\nModel Accuracy: {round(accuracy * 100, 2)}%")
    print("\nConfusion Matrix:")
    print(confusion_matrix(y_test, predictions))
    print("\nClassification Report:")
    print(classification_report(y_test, predictions))

    # ── Save Model ─────────────────────────────────────────────────
    joblib.dump(model, os.path.join(base_dir, "churn_model.pkl"))
    joblib.dump(scaler, os.path.join(base_dir, "churn_scaler.pkl"))
    print("\nChurn model and scaler saved!")

    # ── 2. Apply Model to CRM Leads ────────────────────────────────
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="197672",
        database="crm_leads"
    )

    leads_df = pd.read_sql("SELECT * FROM leads", conn, index_col=None)

    # ── Generate Behaviour Features ────────────────────────────────
    np.random.seed(24)
    leads_df["TotalVisits"] = np.random.randint(1, 12, len(leads_df))
    leads_df["Total Time Spent on Website"] = np.random.randint(30, 900, len(leads_df))
    leads_df["Page Views Per Visit"] = np.random.randint(1, 10, len(leads_df))
    leads_df["Asymmetrique Activity Score"] = np.random.randint(5, 25, len(leads_df))
    leads_df["Asymmetrique Profile Score"] = np.random.randint(5, 25, len(leads_df))
    leads_df["Do Not Email"] = np.random.randint(0, 2, len(leads_df))
    leads_df["Do Not Call"] = np.random.randint(0, 2, len(leads_df))
    leads_df["Search"] = np.random.randint(0, 2, len(leads_df))
    leads_df["Magazine"] = np.random.randint(0, 2, len(leads_df))
    leads_df["Newspaper Article"] = np.random.randint(0, 2, len(leads_df))
    leads_df["Digital Advertisement"] = np.random.randint(0, 2, len(leads_df))
    leads_df["Through Recommendations"] = np.random.randint(0, 2, len(leads_df))

    # ── Prepare & Predict ──────────────────────────────────────────
    lead_features = leads_df[features]
    lead_features_scaled = scaler.transform(lead_features)

    churn_scores = model.predict_proba(lead_features_scaled)[:, 1] * 100
    churn_scores = churn_scores + np.random.uniform(-5, 5, len(churn_scores))
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

    # ── Save Results to MySQL ──────────────────────────────────────
    cursor = conn.cursor()
    for _, row in leads_df.iterrows():
        cursor.execute(
            """
            UPDATE leads
            SET churn_score = %s,
                churn_risk = %s
            WHERE id = %s
            """,
            (float(row["churn_score"]), str(row["churn_risk"]), int(row["id"]))
        )

    conn.commit()
    cursor.close()
    conn.close()

    print("\n✅ Churn scores saved to database!")
    print(leads_df[["name", "email", "churn_score", "churn_risk"]].head(10))


if __name__ == "__main__":
    run_churn_prediction()