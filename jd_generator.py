import os
import json
from datetime import datetime
from dotenv import load_dotenv
from openai import OpenAI

from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib import enums

# ==========================================
# STATIC COMPANY DETAILS (NON-MODIFIABLE)
# ==========================================

COMPANY_NAME = "SHEEP.AI ADVISORY LLP"
COMPANY_TAGLINE = "Incorporated under LLP Act, 2008"
LLPIN = "abc"
PAN = "abc1"
TAN = "abc2"

# ==========================================
# CONFIG
# ==========================================

# Load .env file
load_dotenv(override=True)

# Initialize client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

PDF_DIR = "static/generated_pdfs"
LOGO_PATH = "static/logo.png"

os.makedirs(PDF_DIR, exist_ok=True)


# ==========================================
# OPENAI JD CONTENT GENERATOR
# ==========================================

def generate_jd_content(data: dict) -> dict:
    """
    Uses OpenAI to generate structured Job Description content.
    """

    system_prompt = f"""
You are an expert HR consultant drafting legally structured Job Descriptions for Indian companies.

Company Name: {COMPANY_NAME}
LLPIN: {LLPIN}

Return STRICT JSON only in the following structure:

{{
    "job_summary": "",
    "key_responsibilities": ["", "", ""],
    "required_skills": ["", "", ""],
    "preferred_skills": ["", "", ""],
    "qualifications": "",
    "compensation_note": "",
    "compliance_note": ""
}}

Guidelines:
- Professional tone
- Suitable for a growing startup
- Indian compliance context
- No markdown
- No explanations outside JSON
"""

    user_prompt = f"""
Role: {data.get("role")}
Department: {data.get("department")}
Location: {data.get("location")}
Experience Required: {data.get("experience")}
Employment Type: {data.get("employment_type")}
Reports To: {data.get("reporting_to")}
Company Overview: {data.get("company_overview")}
"""

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        temperature=0.7
    )

    content = response.choices[0].message.content.strip()

    try:
        return json.loads(content)
    except:
        raise Exception("OpenAI did not return valid JSON.")


# ==========================================
# PDF GENERATOR
# ==========================================

def generate_jd_pdf(data: dict) -> str:

    jd_content = generate_jd_content(data)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"JD_{data.get('role','Role').replace(' ','_')}_{timestamp}.pdf"
    file_path = os.path.join(PDF_DIR, file_name)

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # ==================================
    # LOGO
    # ==================================
    if os.path.exists(LOGO_PATH):
        img = Image(LOGO_PATH, width=1.2 * inch, height=1.2 * inch)
        elements.append(img)

    elements.append(Spacer(1, 10))

    # ==================================
    # LETTERHEAD HEADER
    # ==================================
    elements.append(Paragraph(f"<b>{COMPANY_NAME}</b>", styles['Title']))
    elements.append(Spacer(1, 4))
    elements.append(Paragraph(COMPANY_TAGLINE, styles['Normal']))
    elements.append(Spacer(1, 4))
    elements.append(
        Paragraph(
            f"LLPIN: {LLPIN} | PAN: {PAN} | TAN: {TAN}",
            styles['Normal']
        )
    )

    elements.append(Spacer(1, 12))
    elements.append(HRFlowable(width="100%"))
    elements.append(Spacer(1, 20))

    # ==================================
    # TITLE
    # ==================================
    centered = ParagraphStyle(
        name='centered',
        parent=styles['Heading1'],
        alignment=enums.TA_CENTER
    )

    elements.append(Paragraph(
        f"Job Description – {data.get('role')}",
        centered
    ))
    elements.append(Spacer(1, 20))

    # ==================================
    # JOB SUMMARY
    # ==================================
    elements.append(Paragraph("<b>Job Summary</b>", styles['Heading2']))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(jd_content["job_summary"], styles['Normal']))
    elements.append(Spacer(1, 15))

    # ==================================
    # RESPONSIBILITIES
    # ==================================
    elements.append(Paragraph("<b>Key Responsibilities</b>", styles['Heading2']))
    elements.append(Spacer(1, 8))
    for item in jd_content["key_responsibilities"]:
        elements.append(Paragraph(f"• {item}", styles['Normal']))
    elements.append(Spacer(1, 15))

    # ==================================
    # REQUIRED SKILLS
    # ==================================
    elements.append(Paragraph("<b>Required Skills</b>", styles['Heading2']))
    elements.append(Spacer(1, 8))
    for item in jd_content["required_skills"]:
        elements.append(Paragraph(f"• {item}", styles['Normal']))
    elements.append(Spacer(1, 15))

    # ==================================
    # PREFERRED SKILLS
    # ==================================
    elements.append(Paragraph("<b>Preferred Skills</b>", styles['Heading2']))
    elements.append(Spacer(1, 8))
    for item in jd_content["preferred_skills"]:
        elements.append(Paragraph(f"• {item}", styles['Normal']))
    elements.append(Spacer(1, 15))

    # ==================================
    # QUALIFICATIONS
    # ==================================
    elements.append(Paragraph("<b>Qualifications</b>", styles['Heading2']))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(jd_content["qualifications"], styles['Normal']))
    elements.append(Spacer(1, 20))

    # ==================================
    # COMPENSATION
    # ==================================
    elements.append(Paragraph("<b>Compensation Note</b>", styles['Heading2']))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(jd_content["compensation_note"], styles['Normal']))
    elements.append(Spacer(1, 20))

    # ==================================
    # COMPLIANCE
    # ==================================
    elements.append(Paragraph("<b>Compliance Note</b>", styles['Heading2']))
    elements.append(Spacer(1, 8))
    elements.append(Paragraph(jd_content["compliance_note"], styles['Normal']))

    doc.build(elements)


    return file_path
