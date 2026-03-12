from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import mysql.connector
import os

# ML model
from ml_model import run_segmentation

app = Flask(__name__)
CORS(app)


# --- Database Connection ---
def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "197672"),
        database=os.getenv("DB_NAME", "crm_leads")
    )
    return connection


# --- Home Page ---
@app.route("/")
def home():
    return render_template("index.html")


# --- Add Lead ---
@app.route("/add-lead", methods=["POST"])
def add_lead():
    try:
        data = request.get_json()

        name = data.get("name")
        email = data.get("email")
        phone = data.get("phone")

        # Validation
        if not name or not email or not phone:
            return jsonify({"message": "Name, email, and phone are required!"}), 400

        if "@" not in email or "." not in email:
            return jsonify({"message": "Invalid email format!"}), 400

        if not phone.isdigit() or len(phone) < 10:
            return jsonify({"message": "Phone must be numeric and at least 10 digits!"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Duplicate email check
        cursor.execute("SELECT * FROM leads WHERE email=%s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"message": "Lead with this email already exists!"}), 400

        # Insert lead
        cursor.execute(
            "INSERT INTO leads (name, email, phone) VALUES (%s, %s, %s)",
            (name, email, phone)
        )

        conn.commit()

        # Run ML segmentation after new lead
        run_segmentation()

        cursor.close()
        conn.close()

        return jsonify({"message": "Lead added successfully!"}), 201

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


# --- Update Lead ---
@app.route("/update-lead/<int:lead_id>", methods=["PUT"])
def update_lead(lead_id):
    try:
        data = request.get_json()

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM leads WHERE id=%s", (lead_id,))
        existing = cursor.fetchone()

        if not existing:
            cursor.close()
            conn.close()
            return jsonify({"message": "Lead not found!"}), 404

        name = data.get("name", existing["name"])
        email = data.get("email", existing["email"])
        phone = data.get("phone", existing["phone"])
        status = data.get("status", existing.get("status"))
        notes = data.get("notes", existing.get("notes"))
        follow_up_date = data.get("follow_up_date", existing.get("follow_up_date"))

        cursor.execute(
            """
            UPDATE leads 
            SET name=%s, email=%s, phone=%s, status=%s, notes=%s, follow_up_date=%s
            WHERE id=%s
            """,
            (name, email, phone, status, notes, follow_up_date, lead_id)
        )

        conn.commit()
        cursor.close()
        conn.close()

        return jsonify({"message": "Lead updated successfully!"}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


# --- View Leads ---
@app.route("/view-leads", methods=["GET"])
def view_leads():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM leads ORDER BY id DESC LIMIT 1000")
        leads = cursor.fetchall()

        cursor.close()
        conn.close()

        return jsonify({"leads": leads}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


# --- Delete Lead ---
@app.route("/delete-lead/<int:lead_id>", methods=["DELETE"])
def delete_lead(lead_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM leads WHERE id=%s", (lead_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Lead deleted successfully!"}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


@app.route("/search-leads", methods=["GET"])
def search_leads():
    try:
        query = request.args.get("q", "")
        status = request.args.get("status", "")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        if status:
            cursor.execute("SELECT * FROM leads WHERE status=%s", (status,))
        elif request.args.get("category"):
            category = request.args.get("category")
            cursor.execute("SELECT * FROM leads WHERE lead_category=%s", (category,))
        elif request.args.get("priority"):
            priority = request.args.get("priority")
            cursor.execute("SELECT * FROM leads WHERE priority LIKE %s", (f"%{priority}%",))
        else:
            cursor.execute(
                "SELECT * FROM leads WHERE name LIKE %s OR email LIKE %s",
                (f"%{query}%", f"%{query}%")
            )

        leads = cursor.fetchall()
        cursor.close()
        conn.close()

        return jsonify({"leads": leads}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


# --- Run ML Segmentation Manually ---
@app.route("/run-segmentation", methods=["POST"])
def run_ml():
    try:
        run_segmentation()
        return jsonify({"message": "Segmentation complete!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
# --- Run Lead Scoring ---
@app.route("/run-lead-scoring", methods=["POST"])
def run_lead_scoring_route():
    try:
        from lead_scoring import run_lead_scoring
        run_lead_scoring()
        return jsonify({"message": "Lead scoring complete!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Run Churn Prediction ---
@app.route("/run-churn-prediction", methods=['POST'])
def run_churn_prediction_route():
    try:
        from churn_model import run_churn_prediction
        run_churn_prediction()
        return jsonify({"message": "Churn prediction complete!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Run Priority Scoring ---
@app.route("/run-priority-scoring", methods=['POST'])
def run_priority_scoring_route():
    try:
        from priority_score import run_priority_scoring
        run_priority_scoring()
        return jsonify({"message": "Priority scoring complete!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Feature Importance ---
@app.route("/feature-importance", methods=["GET"])
def feature_importance():
    try:
        import joblib
        model = joblib.load("lead_scoring_model.pkl")
        features = [
            "TotalVisits", "Time Spent", "Page Views",
            "Activity Score", "Profile Score",
            "Do Not Email", "Do Not Call", "Search", "Magazine",
            "Newspaper", "Digital Ad", "Recommendations"
        ]
        importance = model.feature_importances_.tolist()
        return jsonify({"features": features, "importance": importance}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500
    
if __name__ == "__main__":
    app.run(debug=True)