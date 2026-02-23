import os
from datetime import datetime
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    Image,
    HRFlowable
)
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.pagesizes import A4
from reportlab.lib import enums
from num2words import num2words

# ==========================================
# STATIC COMPANY DETAILS (WILL NOT CHANGE)
# ==========================================

COMPANY_NAME = "SHEEP.AI ADVISORY LLP"
COMPANY_TAGLINE = "Incorporated under LLP Act, 2008"
LLPIN = "ACQ-1759"
PAN = "AFRFS4064A"
TAN = "LKNS29836C"

# ==================================
# CONFIGURATION
# ==================================

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
PDF_DIR = os.path.join(STATIC_DIR, "generated_pdfs")
LOGO_PATH = os.path.join(STATIC_DIR, "logo.png")

os.makedirs(PDF_DIR, exist_ok=True)


# ==================================
# CALCULATION ENGINE
# ==================================

def calculate_salary_components(data: dict) -> dict:
    """
    Startup mode: All deductions manual.
    """

    basic = data.get("basic", 0)
    hra = data.get("hra", 0)
    allowance = data.get("allowance", 0)
    bonus = data.get("bonus", 0)

    gross = basic + hra + allowance + bonus

    # Manual deductions
    pf = data.get("pf", 0)
    tds = data.get("tds", 0)
    pt = data.get("pt", 0)

    total_deductions = pf + tds + pt

    net = gross - total_deductions

    # ✅ Now update dictionary AFTER calculation
    data.update({
        "gross": gross,
        "pf": pf,
        "tds": tds,
        "pt": pt,
        "total_deductions": total_deductions,
        "net": net,
        "net_words": num2words(net, lang="en_IN").replace("euro", "rupees")
    })

    return data

# ==================================
# PDF GENERATOR
# ==================================

def generate_salary_slip(data: dict) -> str:
    """
    Generates legally compliant Indian Salary Slip PDF.
    Returns file path.
    """

    data = calculate_salary_components(data)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    file_name = f"SalarySlip_{data.get('employee_id','EMP')}_{timestamp}.pdf"
    file_path = os.path.join(PDF_DIR, file_name)

    doc = SimpleDocTemplate(file_path, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    # ==================================
    # LOGO
    # ==================================
    if os.path.exists(LOGO_PATH):
        img = Image(LOGO_PATH, width=1.5 * inch, height=1.5 * inch)
        elements.append(img)

    elements.append(Spacer(1, 12))

    # ==================================
    # LETTERHEAD HEADER
    # ==================================
    elements.append(Paragraph("<b>SHEEP.AI ADVISORY LLP</b>", styles['Title']))
    elements.append(Paragraph("Incorporated under LLP Act, 2008", styles['Normal']))
    elements.append(Paragraph(f"LLPIN: {LLPIN} | PAN: {PAN} | TAN: {TAN}",styles['Normal']))

    elements.append(Spacer(1, 10))
    elements.append(HRFlowable(width="100%"))
    elements.append(Spacer(1, 15))

    # ==================================
    # TITLE
    # ==================================
    centered = ParagraphStyle(
        name='centered',
        parent=styles['Heading1'],
        alignment=enums.TA_CENTER
    )

    elements.append(Paragraph(f"Salary Slip - {data.get('month','')}", centered))
    elements.append(Spacer(1, 20))

    # ==================================
    # EMPLOYEE DETAILS
    # ==================================
    employee_table_data = [
        ["Employee Name", data.get("name","")],
        ["Employee ID", data.get("employee_id","")],
        ["Designation", data.get("designation","")],
        ["Department", data.get("department","")],
        ["Date of Joining", data.get("doj","")],
        ["UAN", data.get("uan","")],
        ["PF Number", data.get("pf_number","")],
        ["PAN", data.get("employee_pan","")],
        ["Bank Account", data.get("bank_account","")]
    ]

    employee_table = Table(employee_table_data, colWidths=[2.5*inch, 3*inch])
    employee_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (0,-1), colors.whitesmoke),
    ]))

    elements.append(employee_table)
    elements.append(Spacer(1, 25))

    # ==================================
    # EARNINGS
    # ==================================
    earnings_data = [
        ["Earnings", "Amount (₹)"],
        ["Basic Salary", data["basic"]],
        ["HRA", data["hra"]],
        ["Allowance", data["allowance"]],
        ["Bonus", data["bonus"]],
        ["Gross Earnings", data["gross"]],
    ]

    earnings_table = Table(earnings_data, colWidths=[3*inch, 2.5*inch])
    earnings_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))

    elements.append(earnings_table)
    elements.append(Spacer(1, 20))

    # ==================================
    # DEDUCTIONS
    # ==================================
    deductions_data = [
        ["Deductions", "Amount (₹)"],
        ["Provident Fund", data["pf"]],
        ["TDS", data["tds"]],
        ["Professional Tax", data["pt"]],
        ["Total Deductions", data["total_deductions"]],
    ]

    deductions_table = Table(deductions_data, colWidths=[3*inch, 2.5*inch])
    deductions_table.setStyle(TableStyle([
        ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
        ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
    ]))

    elements.append(deductions_table)
    elements.append(Spacer(1, 25))

    # ==================================
    # NET PAY
    # ==================================

    elements.append(Paragraph(
        f"<b>Net Pay:</b> ₹ {data['net']}",
        styles['Heading2']
    ))
    elements.append(Spacer(1, 10))
    
    elements.append(Paragraph(
        f"<b>Net Pay (in words):</b> {data['net_words']}",
        styles['Normal']
    ))

    # ==================================
    # COMPLIANCE DECLARATION
    # ==================================
    elements.append(HRFlowable(width="100%"))
    elements.append(Spacer(1, 10))

    elements.append(Paragraph("<b>Compliance Declaration</b>", styles['Heading3']))
    elements.append(Spacer(1, 8))

    compliance_text = """
    1. Issued under the Employees’ Provident Funds and Miscellaneous Provisions Act, 1952.
    2. TDS deducted as per Income Tax Act, 1961.
    3. Professional Tax deducted as per applicable State laws.
    4. Generated under Payment of Wages Act, 1936.
    5. This is a computer-generated document and does not require physical signature.
    """

    elements.append(Paragraph(compliance_text, styles['Normal']))

    elements.append(Spacer(1, 20))
    elements.append(Paragraph(
        "Email: hr@sheepai.info | Website: www.sheepai.info",
        styles['Normal']
    ))

    doc.build(elements)

    return file_path