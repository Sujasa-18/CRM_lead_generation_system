from groq import Groq
import mysql.connector
import os
from dotenv import load_dotenv

load_dotenv()

# Configure Groq
client = Groq(api_key=os.getenv("GROQ_API_KEY"))
MODEL = "llama-3.3-70b-versatile"

def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", "197672"),
        database=os.getenv("DB_NAME", "crm_leads")
    )

def get_db_schema():
    return """
    Table: leads
    Columns:
    - id (int)
    - name (varchar)
    - email (varchar)
    - phone (varchar)
    - status (varchar) -- values: New, Contacted, Converted, Lost
    - notes (text)
    - follow_up_date (date)
    - lead_score (float) -- 0 to 100
    - lead_category (varchar) -- values: Hot, Warm, Cold
    - churn_score (float) -- 0 to 100
    - churn_risk (varchar) -- values: High, Medium, Low
    - priority (varchar) -- values: Priority 1 - Urgent, Priority 2 - Follow Up, Priority 3 - Nurture, Priority 4 - Monitor, Priority 5 - No Action
    - next_action (varchar)
    - job_role (varchar) -- values: Analyst, Developer, Consultant, Manager, Director, Executive
    - years_of_experience (int)
    - industry (varchar) -- values: Technology, Finance, Healthcare, Retail, Education, Manufacturing
    - company_size (varchar) -- values: Small, Medium, Large, Enterprise
    - annual_budget (varchar) -- values: Low, Medium, High
    - decision_maker (varchar) -- values: Yes, No
    - last_contacted_days (int)
    - number_of_follow_ups (int)
    - product_demo_taken (varchar) -- values: Yes, No
    - response_time_hours (int)
    - previous_purchase (varchar) -- values: Yes, No
    - location (varchar) -- values: Metro, Tier 2, Tier 3
    - age_group (varchar) -- values: 20-30, 31-40, 41-50, 50+
    - lead_source_quality (varchar) -- values: Referral, Organic, Paid, Cold
    - engagement_trend (varchar) -- values: Increasing, Stable, Decreasing
    """

def generate_sql(user_question):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": f"""You are a SQL expert for a CRM database. Generate a MySQL query to answer the user's question.

Database schema:
{get_db_schema()}

Rules:
- Return ONLY the SQL query, nothing else
- No explanations, no markdown, no backticks
- Use COUNT(*) for counting
- Use AVG() for averages
- Use GROUP BY for comparisons
- Always use valid MySQL syntax
- Limit results to 20 rows maximum
- For percentage calculations use ROUND((COUNT(*) * 100.0 / (SELECT COUNT(*) FROM leads)), 2)"""
            },
            {
                "role": "user",
                "content": user_question
            }
        ],
        temperature=0
    )
    sql = response.choices[0].message.content.strip()
    sql = sql.replace("```sql", "").replace("```", "").strip()
    return sql

def format_answer(user_question, sql_query, results):
    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": """You are a helpful CRM assistant. Format database results into clear natural language answers.
Rules:
- Be concise and direct
- Use numbers from the data
- Format nicely with bullet points if multiple items
- If results are empty say no data was found
- Don't mention SQL or technical details
- Keep response under 100 words"""
            },
            {
                "role": "user",
                "content": f"Question: {user_question}\nData: {results}"
            }
        ],
        temperature=0.3
    )
    return response.choices[0].message.content.strip()

def chat(user_question):
    try:
        # Step 1 — Generate SQL
        sql_query = generate_sql(user_question)
        print(f"Generated SQL: {sql_query}")

        # Step 2 — Run SQL
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute(sql_query)
        results = cursor.fetchall()
        cursor.close()
        conn.close()

        # Step 3 — Format answer
        answer = format_answer(user_question, sql_query, results)
        return {"answer": answer, "success": True}

    except Exception as e:
        print(f"Error: {e}")
        return {
            "answer": "Sorry I couldn't process that question. Please try rephrasing it.",
            "success": False,
            "error": str(e)
        }

if __name__ == "__main__":
    test_questions = [
        "How many total leads do we have?",
        "Which industry has the most hot leads?",
        "What is the average lead score?"
    ]
    for q in test_questions:
        print(f"Q: {q}")
        result = chat(q)
        print(f"A: {result['answer']}")
        print()