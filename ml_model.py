import mysql.connector
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler


def run_segmentation():

    # Connect to database
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="197672",
        database="crm_leads"
    )

    # Load leads
    df = pd.read_sql("SELECT * FROM leads", conn)
    print(f"✅ Loaded {len(df)} leads from database")

    # ----- Feature Engineering -----

    status_map = {"New": 1, "Contacted": 2, "Converted": 3, "Lost": 0}
    df["status_num"] = df["status"].map(status_map).fillna(1)

    df["has_notes"] = df["notes"].apply(
        lambda x: 1 if x and str(x).strip() != "" else 0
    )

    df["has_followup"] = df["follow_up_date"].apply(
        lambda x: 1 if x else 0
    )

    df["created_at"] = pd.to_datetime(df["created_at"])
    df["days_since_created"] = (
        pd.Timestamp.now() - df["created_at"]
    ).dt.days

    features = df[[
        "status_num",
        "has_notes",
        "has_followup",
        "days_since_created"
    ]]

    # ----- Scaling -----

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    # ----- KMeans Clustering -----

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df["cluster"] = kmeans.fit_predict(scaled_features)

    # ----- Label clusters -----

    cluster_means = (
        df.groupby("cluster")["status_num"]
        .mean()
        .sort_values(ascending=False)
    )

    labels = ["Hot", "Warm", "Cold"]
    cluster_labels = {}

    for i, cluster_id in enumerate(cluster_means.index):
        cluster_labels[cluster_id] = labels[i]

    df["category"] = df["cluster"].map(cluster_labels)

    # ----- Save categories to database -----

    cursor = conn.cursor()

    for _, row in df.iterrows():
        cursor.execute(
            "UPDATE leads SET category = %s WHERE id = %s",
            (row["category"], row["id"])
        )

    conn.commit()
    cursor.close()
    conn.close()

    print("✅ Categories saved to database!")
    print("✅ ML Model ran successfully!")