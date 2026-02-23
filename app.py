import os
import pandas as pd
import dash
from dash import html, dcc, Input, Output, State
import dash_bootstrap_components as dbc

from email_service import (
    _send_email,
    get_latest_salary_slip,
    get_latest_jd,
    get_employee_email
)
from jd_generator import generate_jd_pdf
from salary_slip_engine import generate_salary_slip

# ==========================================
# CONFIGURATION
# ==========================================

EMPLOYEE_FILE = "data/Employee_Master.xlsx"
PDF_FOLDER = "static/generated_pdfs"
LOGO_PATH = "static/logo.png"

# ==========================================
# DATA FUNCTIONS
# ==========================================
def get_employee_details(employee_id):
    if not os.path.exists(EMPLOYEE_FILE):
        return {}

    df = pd.read_excel(EMPLOYEE_FILE)

    row = df[df["Employee ID"] == employee_id]

    if row.empty:
        return {}

    row = row.iloc[0]

    return {
        "designation": row.get("Designation", ""),
        "department": row.get("Department", ""),
        "doj": row.get("Date of Joining (DD-MM-YYYY)", ""),
        "uan": row.get("UAN", ""),
        "pf_number": row.get("PF Number", ""),
        "employee_pan": row.get("PAN", ""),
        "bank_account": row.get("Bank Account Number", "")
    }

def get_jd_dropdown_options():
    if not os.path.exists(PDF_FOLDER):
        return []

    files = [f for f in os.listdir(PDF_FOLDER) if f.startswith("JD_")]

    roles = set()
    for f in files:
        role = f.replace("JD_", "").rsplit("_", 1)[0]
        role = role.replace("_", " ")
        roles.add(role)

    return [{"label": role, "value": role} for role in roles]

def append_employee_to_excel(data):
    if os.path.exists(EMPLOYEE_FILE):
        df = pd.read_excel(EMPLOYEE_FILE)
    else:
        df = pd.DataFrame(columns=[
            "Employee ID", "Name", "Email", "Designation",
            "Department", "Date of Joining (DD-MM-YYYY)",
            "UAN", "PF Number", "PAN", "Bank Account Number"
        ])

    # Prevent duplicate ID
    if data["Employee ID"] in df["Employee ID"].values:
        return False, "Employee ID already exists."

    df = pd.concat([df, pd.DataFrame([data])], ignore_index=True)
    df.to_excel(EMPLOYEE_FILE, index=False)

    return True, "Employee Created Successfully!"

def get_employee_dropdown_options():
    if not os.path.exists(EMPLOYEE_FILE):
        return []

    df = pd.read_excel(EMPLOYEE_FILE)

    options = []
    for _, row in df.iterrows():
        label = f"{row['Employee ID']} - {row['Name']}"
        value = row["Employee ID"]
        options.append({"label": label, "value": value})

    return options

def get_total_employees():
    if os.path.exists(EMPLOYEE_FILE):
        df = pd.read_excel(EMPLOYEE_FILE)
        return len(df)
    return 0


def get_total_salary_slips():
    if os.path.exists(PDF_FOLDER):
        return len([f for f in os.listdir(PDF_FOLDER) if f.startswith("SalarySlip")])
    return 0


def get_total_jds():
    if os.path.exists(PDF_FOLDER):
        return len([f for f in os.listdir(PDF_FOLDER) if f.startswith("JD_")])
    return 0


# ==========================================
# APP SETUP
# ==========================================

app = dash.Dash(
    __name__,
    external_stylesheets=[dbc.themes.DARKLY],
    suppress_callback_exceptions=True
)

server = app.server

# ==========================================
# SIDEBAR WITH LOGO
# ==========================================

sidebar = html.Div(
    [
        html.Div([
            html.Img(src=f"/{LOGO_PATH}", style={"width": "120px"}),
        ], style={"textAlign": "center", "marginBottom": "20px"}),

        html.H4("SheepAI HRMS", className="text-center"),
        html.Hr(),

        dbc.Nav(
            [
                dbc.NavLink("Dashboard", href="/", active="exact"),
                dbc.NavLink("Job Description", href="/jd"),
                dbc.NavLink("Salary Slip", href="/salary"),
                dbc.NavLink("Email Service", href="/email"),
                dbc.NavLink("Create Employee", href="/create-employee"),  # NEW
            ],
            vertical=True,
            pills=True,
        ),
    ],
    style={
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "width": "18rem",
        "padding": "2rem 1rem",
        "background-color": "#111827",
    },
)

# ==========================================
# CONTENT AREA
# ==========================================

content = html.Div(
    id="page-content",
    style={
        "margin-left": "20rem",
        "margin-right": "2rem",
        "padding": "2rem 1rem",
    },
)

app.layout = html.Div([
    dcc.Location(id="url"),
    dcc.Interval(id="interval-refresh", interval=5000, n_intervals=0),
    sidebar,
    content
])

# ==========================================
# DASHBOARD LAYOUT
# ==========================================

def dashboard_layout():

    return dbc.Container([

        html.H2("HRMS Dashboard Overview", className="mb-4"),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4(id="kpi-employees", className="card-title"),
                    html.P("Total Employees")
                ])
            ], color="primary", inverse=True), md=4),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4(id="kpi-salary", className="card-title"),
                    html.P("Salary Slips Generated")
                ])
            ], color="success", inverse=True), md=4),

            dbc.Col(dbc.Card([
                dbc.CardBody([
                    html.H4(id="kpi-jd", className="card-title"),
                    html.P("Job Descriptions Generated")
                ])
            ], color="warning", inverse=True), md=4),
        ], className="mb-4"),

        dbc.Card([
            dbc.CardBody([
                html.H5("Welcome to SheepAI HRMS"),
                html.P("Manage hiring, payroll and automation from one unified intelligent platform.")
            ])
        ])

    ], fluid=True)

# ==========================================
# JD PAGE
# ==========================================

jd_layout = dbc.Container([

    html.H2("Generate Job Description", className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Input(id="jd-role", placeholder="Role", className="form-control")),
        dbc.Col(dcc.Input(id="jd-dept", placeholder="Department", className="form-control")),
    ], className="mb-3"),

    dbc.Button("Generate JD PDF", id="generate-jd", color="primary", size="lg"),
    html.Br(),
    html.Br(),
    html.Div(id="jd-output")

], fluid=True)

# ==========================================
# SALARY PAGE
# ==========================================

salary_layout = dbc.Container([

    html.H2("Generate Salary Slip", className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Input(id="emp-name", placeholder="Employee Name", className="form-control")),
        dbc.Col(dcc.Dropdown(
            id="emp-id",
            options=get_employee_dropdown_options(),
            placeholder="Select Employee",
        )),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col(dcc.Input(id="basic", type="number", placeholder="Basic", className="form-control")),
        dbc.Col(dcc.Input(id="hra", type="number", placeholder="HRA", className="form-control")),
        dbc.Col(dcc.Input(id="allowance", type="number", placeholder="Allowance", className="form-control")),
        dbc.Col(dcc.Input(id="bonus", type="number", placeholder="Bonus", className="form-control")),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col(dcc.Input(id="pf", type="number", placeholder="Provident Fund (Optional)", className="form-control")),
        dbc.Col(dcc.Input(id="tds", type="number", placeholder="TDS (Optional)", className="form-control")),
        dbc.Col(dcc.Input(id="pt", type="number", placeholder="Professional Tax (Optional)", className="form-control")),
    ], className="mb-3"),

    dbc.Button("Generate Salary Slip", id="generate-salary", color="success", size="lg"),
    html.Br(),
    html.Br(),
    html.Div(id="salary-output")

], fluid=True)


email_layout = dbc.Container([

    html.H2("Email Service", className="mb-4"),

    dcc.Dropdown(
        id="email-type",
        options=[
            {"label": "Send Salary Slip", "value": "salary"},
            {"label": "Send Job Description", "value": "jd"},
        ],
        placeholder="Select Email Type"
    ),

    html.Br(),

    html.Div(
        id="salary-fields",
        children=[
            dcc.Dropdown(
                id="email-employee-id",
                options=get_employee_dropdown_options(),
                placeholder="Select Employee"
            )
        ]
    ),

    html.Div(
        id="jd-fields",
        children=[
            dcc.Dropdown(
                id="email-role",
                options=get_jd_dropdown_options(),
                placeholder="Select JD Role"
            ),
            html.Br(),
            dcc.Input(
                id="email-to",
                placeholder="Recipient Email",
                className="form-control"
            ),
        ]
    ),

    html.Br(),
    dbc.Button("Send Email", id="send-email", color="info"),
    html.Br(),
    html.Br(),
    html.Div(id="email-output")

], fluid=True)


create_employee_layout = dbc.Container([

    html.H2("Create New Employee", className="mb-4"),

    dbc.Row([
        dbc.Col(dcc.Input(id="new-emp-id", placeholder="Employee ID", className="form-control")),
        dbc.Col(dcc.Input(id="new-name", placeholder="Full Name", className="form-control")),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col(dcc.Input(id="new-email", placeholder="Email", className="form-control")),
        dbc.Col(dcc.Input(id="new-designation", placeholder="Designation", className="form-control")),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col(dcc.Input(id="new-department", placeholder="Department", className="form-control")),
        dbc.Col(dcc.Input(id="new-doj", placeholder="Date of Joining (DD-MM-YYYY)", className="form-control")),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col(dcc.Input(id="new-uan", placeholder="UAN", className="form-control")),
        dbc.Col(dcc.Input(id="new-pf", placeholder="PF Number", className="form-control")),
    ], className="mb-3"),

    dbc.Row([
        dbc.Col(dcc.Input(id="new-pan", placeholder="PAN", className="form-control")),
        dbc.Col(dcc.Input(id="new-bank", placeholder="Bank Account", className="form-control")),
    ], className="mb-3"),

    dbc.Button("Create Employee", id="create-employee-btn", color="success", size="lg"),
    html.Br(),
    html.Br(),
    html.Div(id="create-employee-output")

], fluid=True)

# ==========================================
# PAGE ROUTING
# ==========================================

@app.callback(Output("page-content", "children"),
              Input("url", "pathname"))
def render_page(pathname):
    if pathname == "/jd":
        return jd_layout
    elif pathname == "/salary":
        return salary_layout
    elif pathname == "/email":
        return email_layout
    elif pathname == "/create-employee":
        return create_employee_layout
    else:
        return dashboard_layout()
# ==========================================
# KPI AUTO REFRESH
# ==========================================

@app.callback(
    Output("kpi-employees", "children"),
    Output("kpi-salary", "children"),
    Output("kpi-jd", "children"),
    Input("interval-refresh", "n_intervals")
)
def update_kpis(n):
    return (
        get_total_employees(),
        get_total_salary_slips(),
        get_total_jds()
    )

# ==========================================
# JD CALLBACK
# ==========================================

@app.callback(
    Output("jd-output", "children"),
    Input("generate-jd", "n_clicks"),
    State("jd-role", "value"),
    State("jd-dept", "value"),
)
def generate_jd(n, role, dept):
    if not n:
        return ""

    file_path = generate_jd_pdf({
        "role": role,
        "department": dept
    })

    return dbc.Alert("JD Generated Successfully!", color="success")

# ==========================================
# SALARY CALLBACK
# ==========================================

@app.callback(
    Output("salary-output", "children"),
    Input("generate-salary", "n_clicks"),
    State("emp-name", "value"),
    State("emp-id", "value"),
    State("basic", "value"),
    State("hra", "value"),
    State("allowance", "value"),
    State("bonus", "value"),
    State("pf", "value"),
    State("tds", "value"),
    State("pt", "value"),
)
def generate_salary(n, name, emp_id, basic, hra, allowance, bonus, pf, tds, pt):

    if not n:
        return ""

    # 🔥 Fetch employee details from Excel
    employee_details = get_employee_details(emp_id)

    generate_salary_slip({
        "name": name,
        "employee_id": emp_id,
        "basic": basic or 0,
        "hra": hra or 0,
        "allowance": allowance or 0,
        "bonus": bonus or 0,
        "pf": pf or 0,
        "tds": tds or 0,
        "pt": pt or 0,
        **employee_details  # 🔥 merge details here
    })

    return dbc.Alert("Salary Slip Generated Successfully!", color="success")

    
@app.callback(
    Output("salary-fields", "style"),
    Output("jd-fields", "style"),
    Input("email-type", "value"),
)
def toggle_email_fields(email_type):

    if email_type == "salary":
        return {"display": "block"}, {"display": "none"}

    elif email_type == "jd":
        return {"display": "none"}, {"display": "block"}

    return {"display": "none"}, {"display": "none"}
    
@app.callback(
    Output("email-output", "children"),
    Input("send-email", "n_clicks"),
    State("email-type", "value"),
    State("email-employee-id", "value"),
    State("email-role", "value"),
    State("email-to", "value"),
)
def handle_email(n, email_type, employee_id, role, to_email):

    if not n:
        return ""

    try:
        if email_type == "salary":

            attachment = get_latest_salary_slip(employee_id)
            recipient = get_employee_email(employee_id)

            if not attachment:
                return dbc.Alert("Salary slip not found.", color="danger")

            if not recipient:
                return dbc.Alert("Employee email not found.", color="danger")

            _send_email(
                recipient,
                "Salary Slip",
                "Please find attached your salary slip.",
                attachment
            )

            return dbc.Alert(f"Salary slip sent to {recipient}", color="success")

        elif email_type == "jd":

            attachment = get_latest_jd(role)

            if not attachment:
                return dbc.Alert("JD not found.", color="danger")

            _send_email(
                to_email,
                f"Job Description - {role}",
                "Please find attached JD.",
                attachment
            )

            return dbc.Alert("JD sent successfully!", color="success")

        else:
            return dbc.Alert("Select Email Type.", color="danger")

    except Exception as e:
        return dbc.Alert(str(e), color="danger")


@app.callback(
    Output("create-employee-output", "children"),
    Input("create-employee-btn", "n_clicks"),
    State("new-emp-id", "value"),
    State("new-name", "value"),
    State("new-email", "value"),
    State("new-designation", "value"),
    State("new-department", "value"),
    State("new-doj", "value"),
    State("new-uan", "value"),
    State("new-pf", "value"),
    State("new-pan", "value"),
    State("new-bank", "value"),
)
def create_employee(n, emp_id, name, email, designation, department,
                    doj, uan, pf, pan, bank):

    if not n:
        return ""

    if not emp_id or not name or not email:
        return dbc.Alert("Employee ID, Name, and Email are required.", color="danger")

    success, message = append_employee_to_excel({
        "Employee ID": emp_id,
        "Name": name,
        "Email": email,
        "Designation": designation,
        "Department": department,
        "Date of Joining (DD-MM-YYYY)": doj,
        "UAN": uan,
        "PF Number": pf,
        "PAN": pan,
        "Bank Account Number": bank,
    })

    if success:
        return dbc.Alert(message, color="success")
    else:
        return dbc.Alert(message, color="danger")

# ==========================================
# RUN SERVER ON 8080
# ==========================================

if __name__ == "__main__":
    app.run(
        debug=True,
        host="0.0.0.0",
        port=8080
    )