from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import mysql.connector
import os
from datetime import datetime


def generate_report(output_path="crm_report.pdf"):

    # ── Connect to MySQL ───────────────────────────────────────────
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="197672",
        database="crm_leads"
    )
    cursor = conn.cursor(dictionary=True)

    # ── Fetch Data ─────────────────────────────────────────────────
    cursor.execute("SELECT * FROM leads")
    leads = cursor.fetchall()

    cursor.execute("SELECT COUNT(*) as total FROM leads")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as count FROM leads WHERE status='New'")
    new_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM leads WHERE status='Contacted'")
    contacted_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM leads WHERE status='Converted'")
    converted_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM leads WHERE status='Lost'")
    lost_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM leads WHERE lead_category='Hot'")
    hot_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM leads WHERE lead_category='Warm'")
    warm_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM leads WHERE lead_category='Cold'")
    cold_count = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM leads WHERE churn_risk='High'")
    high_churn = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM leads WHERE churn_risk='Medium'")
    medium_churn = cursor.fetchone()["count"]

    cursor.execute("SELECT COUNT(*) as count FROM leads WHERE churn_risk='Low'")
    low_churn = cursor.fetchone()["count"]

    cursor.execute("SELECT * FROM leads WHERE priority LIKE '%1%' ORDER BY lead_score DESC LIMIT 10")
    urgent_leads = cursor.fetchall()

    cursor.close()
    conn.close()

    # ── Conversion Rate ────────────────────────────────────────────
    conversion_rate = round((converted_count / total) * 100, 2) if total > 0 else 0

    # ── PDF Setup ──────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title", fontSize=22, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#1F3864"), alignment=TA_CENTER, spaceAfter=20
    )
    subtitle_style = ParagraphStyle(
        "Subtitle", fontSize=11, fontName="Helvetica",
        textColor=colors.HexColor("#666666"), alignment=TA_CENTER, spaceAfter=30
    )
    section_style = ParagraphStyle(
        "Section", fontSize=13, fontName="Helvetica-Bold",
        textColor=colors.HexColor("#2E75B6"), spaceBefore=16, spaceAfter=8
    )
    normal_style = ParagraphStyle(
        "Normal", fontSize=10, fontName="Helvetica",
        textColor=colors.HexColor("#333333"), spaceAfter=4
    )

    content = []

    # ── Title ──────────────────────────────────────────────────────
    content.append(Paragraph("CRM Lead Generation System", title_style))
    content.append(Paragraph(f"Report generated on {datetime.now().strftime('%d %B %Y, %I:%M %p')}", subtitle_style))
    content.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#2E75B6")))
    content.append(Spacer(1, 16))

    # ── Summary Stats ──────────────────────────────────────────────
    content.append(Paragraph("Summary Statistics", section_style))

    stats_data = [
        ["Metric", "Count"],
        ["Total Leads", str(total)],
        ["New Leads", str(new_count)],
        ["Contacted", str(contacted_count)],
        ["Converted", str(converted_count)],
        ["Lost", str(lost_count)],
        ["Conversion Rate", f"{conversion_rate}%"],
    ]

    stats_table = Table(stats_data, colWidths=[3 * inch, 3 * inch])
    stats_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1F3864")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#EAF2FB"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    content.append(stats_table)
    content.append(Spacer(1, 16))

    # ── ML Breakdown ───────────────────────────────────────────────
    content.append(Paragraph("ML Model Results", section_style))

    ml_data = [
        ["Category", "Hot", "Warm", "Cold"],
        ["Lead Category", str(hot_count), str(warm_count), str(cold_count)],
        ["Churn Risk", str(high_churn), str(medium_churn), str(low_churn)],
    ]

    ml_table = Table(ml_data, colWidths=[2 * inch, 1.5 * inch, 1.5 * inch, 1.5 * inch])
    ml_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2E75B6")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#EAF2FB"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    content.append(ml_table)
    content.append(Spacer(1, 16))

    # ── Top Urgent Leads ───────────────────────────────────────────
    content.append(Paragraph("Top Priority 1 — Urgent Leads", section_style))

    urgent_data = [["Name", "Email", "Lead Score", "Churn Risk"]]
    for lead in urgent_leads:
        urgent_data.append([
            str(lead.get("name", "—")),
            str(lead.get("email", "—")),
            f"{lead.get('lead_score', 0)}%" if lead.get("lead_score") else "—",
            str(lead.get("churn_risk", "—"))
        ])

    if len(urgent_data) == 1:
        urgent_data.append(["No urgent leads found", "", "", ""])

    urgent_table = Table(urgent_data, colWidths=[2 * inch, 2.5 * inch, 1.2 * inch, 1.3 * inch])
    urgent_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#C00000")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 11),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 10),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.HexColor("#FFF0F0"), colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CCCCCC")),
        ("TOPPADDING", (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
    ]))
    content.append(urgent_table)
    content.append(Spacer(1, 16))

    # ── Footer ─────────────────────────────────────────────────────
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#CCCCCC")))
    content.append(Spacer(1, 8))
    content.append(Paragraph("Generated by CRM Lead Generation System — ML Integration Project", normal_style))

    # ── Build PDF ──────────────────────────────────────────────────
    doc.build(content)
    print(f"✅ Report generated: {output_path}")
    return output_path


if __name__ == "__main__":
    generate_report()