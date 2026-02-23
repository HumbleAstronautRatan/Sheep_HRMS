import os
import glob
import base64
import pandas as pd
from dotenv import load_dotenv
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Mail,
    Attachment,
    FileContent,
    FileName,
    FileType,
    Disposition,
)

# ==========================================
# LOAD ENV
# ==========================================

load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")
SENDER = "hr@sheepai.info"

PDF_FOLDER = "static/generated_pdfs"
EMPLOYEE_FILE = "data/Employee_Master.xlsx"


# ==========================================
# FILE HELPERS
# ==========================================

def get_latest_salary_slip(employee_id):
    pattern = os.path.join(PDF_FOLDER, f"SalarySlip_{employee_id}_*.pdf")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)


def get_latest_jd(role):
    role_clean = role.replace(" ", "_")
    pattern = os.path.join(PDF_FOLDER, f"JD_{role_clean}_*.pdf")
    files = glob.glob(pattern)
    if not files:
        return None
    return max(files, key=os.path.getctime)


def get_employee_email(employee_id):
    if not os.path.exists(EMPLOYEE_FILE):
        return None

    df = pd.read_excel(EMPLOYEE_FILE)
    row = df[df["Employee ID"] == employee_id]

    if row.empty:
        return None

    return row.iloc[0]["Email"]


# ==========================================
# CORE SEND FUNCTION (SENDGRID)
# ==========================================

def _send_email(to_email, subject, body, attachment_path=None):

    if not SENDGRID_API_KEY:
        raise Exception("SENDGRID_API_KEY not set in .env file")

    message = Mail(
        from_email=SENDER,
        to_emails=to_email,
        subject=subject,
        plain_text_content=body,
    )

    # Attach PDF if provided
    if attachment_path:
        with open(attachment_path, "rb") as f:
            encoded_file = base64.b64encode(f.read()).decode()

        attachment = Attachment(
            FileContent(encoded_file),
            FileName(os.path.basename(attachment_path)),
            FileType("application/pdf"),
            Disposition("attachment"),
        )

        message.attachment = attachment

    sg = SendGridAPIClient(SENDGRID_API_KEY)
    response = sg.send(message)

    if response.status_code >= 400:
        raise Exception(f"SendGrid Error: {response.body}")

    return True


# ==========================================
# SALARY SLIP EMAIL
# ==========================================

def send_salary_email(employee_name: str, to_email: str, month: str, attachment_path: str):

    subject = f"Salary Slip - {month}"

    body = f"""
Dear {employee_name},

Please find attached your salary slip for {month}.

If you have any questions regarding your compensation,
please contact the HR department.

Regards,
HR Team
SheepAI Advisory LLP
"""

    return _send_email(to_email, subject, body, attachment_path)


# ==========================================
# JD EMAIL
# ==========================================

def send_jd_email(to_email: str, role: str, attachment_path: str):

    subject = f"Job Description - {role}"

    body = f"""
Dear Recipient,

Please find attached the Job Description for the role of {role}.

Regards,
HR Team
SheepAI Advisory LLP
"""

    return _send_email(to_email, subject, body, attachment_path)


# ==========================================
# GENERIC EMAIL
# ==========================================

def send_generic_email(to_email: str, subject: str, body: str, attachment_path: str = None):
    return _send_email(to_email, subject, body, attachment_path)