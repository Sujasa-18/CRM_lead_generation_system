from flask import Flask, request, jsonify, render_template, send_file, Response, session, redirect, url_for
from flask_cors import CORS
from dotenv import load_dotenv
from functools import wraps
import bcrypt
import mysql.connector
import os

# ML model
from ml_model import run_segmentation

load_dotenv()

app = Flask(__name__)
CORS(app)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret")

# Hash the CRM password once at startup
RAW_PASSWORD = os.getenv("CRM_PASSWORD", "admin123")
HASHED_PASSWORD = bcrypt.hashpw(RAW_PASSWORD.encode('utf-8'), bcrypt.gensalt())

# --- Login Required Decorator ---
def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


# --- Database Connection ---
def get_db_connection():
    connection = mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "crm_leads")
    )
    return connection

# --- Log Activity ---
def log_activity(lead_id, action):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO lead_activity (lead_id, action) VALUES (%s, %s)",
            (lead_id, action)
        )
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Activity log error: {e}")


# --- Next Best Action Logic ---
def get_next_action(priority, churn_risk, status, notes, decision_maker=None, product_demo_taken=None, job_role=None):
    if status == "Converted":
        return "Nurture for upsell"
    if status == "Lost":
        return "Re-engage in 30 days"

    if priority and "1" in priority:
        if decision_maker == "Yes":
            return "Schedule executive call immediately"
        if status == "New":
            return "Call immediately"
        if status == "Contacted":
            return "Schedule a demo"
        if notes and "Email Bounced" in notes:
            return "Call — email not working"
        if notes and "Email Opened" in notes:
            return "Send follow-up email now"

    if priority and "2" in priority:
        if product_demo_taken == "Yes":
            return "Send proposal — demo already taken"
        if decision_maker == "Yes":
            return "Schedule decision maker call"
        if churn_risk == "High":
            return "Send re-engagement email"
        if notes and "Page Visited on Website" in notes:
            return "Call while interest is hot"
        return "Send introduction email"

    if priority and "3" in priority:
        if product_demo_taken == "No" and job_role in ["Director", "Executive", "Manager"]:
            return "Offer product demo"
        if churn_risk == "High":
            return "At risk — follow up today"
        return "Follow up in 3 days"

    if priority and "4" in priority:
        return "Monitor — low priority"

    if priority and "5" in priority:
        return "No action needed"

    return "Review lead details"

# --- Login Page ---
@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if bcrypt.checkpw(password.encode('utf-8'), HASHED_PASSWORD):
            session["logged_in"] = True
            return redirect(url_for("home"))
        else:
            error = "Incorrect password. Please try again."
    return render_template("login.html", error=error)

# --- Logout ---
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

# --- Home Page ---
@app.route("/")
@login_required
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

        if not name or not email or not phone:
            return jsonify({"message": "Name, email, and phone are required!"}), 400

        if "@" not in email or "." not in email:
            return jsonify({"message": "Invalid email format!"}), 400

        if not phone.isdigit() or len(phone) < 10:
            return jsonify({"message": "Phone must be numeric and at least 10 digits!"}), 400

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT * FROM leads WHERE email=%s", (email,))
        if cursor.fetchone():
            cursor.close()
            conn.close()
            return jsonify({"message": "Lead with this email already exists!"}), 400

        cursor.execute(
            "INSERT INTO leads (name, email, phone) VALUES (%s, %s, %s)",
            (name, email, phone)
        )

        conn.commit()
        log_activity(cursor.lastrowid, "Lead created")

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

        if data.get("status"):
            log_activity(lead_id, f"Status updated to {data.get('status')}")
        else:
            log_activity(lead_id, "Lead details updated")

        cursor.close()
        conn.close()

        return jsonify({"message": "Lead updated successfully!"}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


# --- View Leads ---
@app.route("/view-leads", methods=["GET"])
def view_leads():
    try:
        status = request.args.get("status", "")
        category = request.args.get("category", "")
        churn = request.args.get("churn", "")
        priority = request.args.get("priority", "")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM leads WHERE 1=1"
        params = []

        if status:
            query += " AND status = %s"
            params.append(status)
        if category:
            query += " AND lead_category = %s"
            params.append(category)
        if churn:
            query += " AND churn_risk = %s"
            params.append(churn)
        if priority:
            query += " AND priority LIKE %s"
            params.append(f"%{priority}%")

        query += " ORDER BY id DESC LIMIT 1000"
        cursor.execute(query, params)

        leads = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"leads": leads}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500
# --- Dashboard Stats (all leads) ---
@app.route("/dashboard-stats", methods=["GET"])
def dashboard_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT status, lead_category, churn_risk, priority, industry, company_size FROM leads")
        leads = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"leads": leads}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Delete Lead ---
@app.route("/delete-lead/<int:lead_id>", methods=["DELETE"])
def delete_lead(lead_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        log_activity(lead_id, "Lead deleted")
        cursor.execute("DELETE FROM leads WHERE id=%s", (lead_id,))
        conn.commit()

        cursor.close()
        conn.close()

        return jsonify({"message": "Lead deleted successfully!"}), 200

    except Exception as e:
        return jsonify({"message": f"Error: {str(e)}"}), 500


# --- Search Leads ---
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


# --- Get Lead Activity ---
@app.route("/lead-activity/<int:lead_id>", methods=["GET"])
def get_lead_activity(lead_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(
            "SELECT * FROM lead_activity WHERE lead_id = %s ORDER BY timestamp DESC",
            (lead_id,)
        )
        activity = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({"activity": activity}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


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
    
# --- Run Next Best Action ---
@app.route("/run-next-action", methods=["POST"])
def run_next_action():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT id, priority, churn_risk, status, notes FROM leads")
        leads = cursor.fetchall()

        for lead in leads:
            action = get_next_action(
                lead.get("priority"),
                lead.get("churn_risk"),
                lead.get("status"),
                lead.get("notes"),
                lead.get("decision_maker"),
                lead.get("product_demo_taken"),
                lead.get("job_role")
            )
            cursor.execute(
                "UPDATE leads SET next_action = %s WHERE id = %s",
                (action, lead["id"])
            )

        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({"message": f"Next Best Action updated for {len(leads)} leads!"}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# --- Feature Importance ---
@app.route("/feature-importance", methods=["GET"])
def feature_importance():
    try:
        import joblib
        model = joblib.load("lead_scoring_model.pkl")
        features = [
            "Total Visits", "Time Spent on Website", "Page Views Per Visit",
            "Activity Score", "Profile Score",
            "Do Not Email", "Do Not Call", "Search", "Magazine",
            "Digital Advertisement", "Through Recommendations",
            "Job Role", "Years of Experience", "Industry",
            "Company Size", "Annual Budget", "Decision Maker",
            "Last Contacted Days", "No. of Follow Ups", "Product Demo Taken",
            "Response Time (hrs)", "Previous Purchase", "Location",
            "Age Group", "Lead Source Quality", "Engagement Trend"
        ]
        importance = model.feature_importances_.tolist()
        return jsonify({"features": features, "importance": importance}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Generate PDF Report ---
@app.route("/generate-report", methods=["GET"])
def generate_report_route():
    try:
        from report_generator import generate_report
        path = generate_report("crm_report.pdf")
        return send_file(path, as_attachment=True, download_name="CRM_Report.pdf")
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# --- Export Filtered Leads to CSV ---
@app.route("/export-csv", methods=["GET"])
def export_csv():
    try:
        import csv
        import io

        status   = request.args.get("status", "")
        category = request.args.get("category", "")
        churn    = request.args.get("churn", "")
        priority = request.args.get("priority", "")
        search   = request.args.get("search", "")

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        query = "SELECT * FROM leads WHERE 1=1"
        params = []

        if search:
            query += " AND (name LIKE %s OR email LIKE %s)"
            params.extend([f"%{search}%", f"%{search}%"])
        if status:
            query += " AND status = %s"
            params.append(status)
        if category:
            query += " AND lead_category = %s"
            params.append(category)
        if churn:
            query += " AND churn_risk = %s"
            params.append(churn)
        if priority:
            query += " AND priority LIKE %s"
            params.append(f"%{priority}%")

        query += " ORDER BY id DESC"
        cursor.execute(query, params)
        leads = cursor.fetchall()

        cursor.close()
        conn.close()

        # Build CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            "ID", "Name", "Email", "Phone",
            "Status", "Category", "Churn Risk",
            "Priority", "Lead Score", "Segment", "Notes", "Follow Up Date"
        ])

        # Rows
        for lead in leads:
            writer.writerow([
                lead.get("id", ""),
                lead.get("name", ""),
                lead.get("email", ""),
                lead.get("phone", ""),
                lead.get("status", ""),
                lead.get("lead_category", ""),
                lead.get("churn_risk", ""),
                lead.get("priority", ""),
                lead.get("lead_score", ""),
                lead.get("segment", ""),
                lead.get("notes", ""),
                lead.get("follow_up_date", ""),
            ])

        output.seek(0)

        return Response(
            output.getvalue(),
            mimetype="text/csv",
            headers={
                "Content-Disposition": "attachment; filename=leads_export.csv",
                "Content-Type": "text/csv; charset=utf-8"
            }
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)