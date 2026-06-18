import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
from datetime import datetime, date, timedelta
import pandas as pd
import json
import time
import secrets
import string
import os
import traceback
import ssl
import uuid
import hashlib

# ---------- PAGE CONFIGURATION ----------
st.set_page_config(
    page_title="TODO Flow - Smart Task Manager",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------- CUSTOM CSS (ELEGANT DARK MODE COMPATIBLE) ----------
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Playfair+Display:wght@400;500;600&display=swap');

:root {
    --primary: #0d9488;
    --primary-dark: #0f766e;
    --secondary: #f59e0b;
    --success: #10b981;
    --danger: #ef4444;
    --bg: #ffffff;
    --bg-secondary: #f8fafc;
    --card-bg: #ffffff;
    --text: #0f172a;
    --text-secondary: #475569;
    --text-muted: #94a3b8;
    --border: #e2e8f0;
    --input-bg: #f1f5f9;
    --shadow: rgba(15, 23, 42, 0.06);
}

@media (prefers-color-scheme: dark) {
    :root {
        --primary: #14b8a6;
        --primary-dark: #0d9488;
        --secondary: #fbbf24;
        --success: #34d399;
        --danger: #f87171;
        --bg: #0f172a;
        --bg-secondary: #1e293b;
        --card-bg: #1e293b;
        --text: #f1f5f9;
        --text-secondary: #cbd5e1;
        --text-muted: #64748b;
        --border: #334155;
        --input-bg: #334155;
        --shadow: rgba(0, 0, 0, 0.4);
    }
}

* { font-family: 'Inter', sans-serif; color: var(--text); }

.stApp {
    background: linear-gradient(135deg, var(--bg-secondary) 0%, var(--bg) 100%);
    min-height: 100vh;
}

.main {
    background: transparent;
}

h1 {
    background: linear-gradient(135deg, var(--primary) 0%, var(--secondary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    text-align: center;
    font-size: 3rem;
    font-weight: 700;
    font-family: 'Playfair Display', serif;
    letter-spacing: -0.5px;
    margin-bottom: 0.25rem;
}

h2 {
    color: var(--text-muted);
    text-align: center;
    font-size: 1.25rem;
    font-weight: 400;
    margin-bottom: 2.5rem;
}

h3 {
    color: var(--primary);
    font-weight: 600;
    margin-top: 1.5rem;
    margin-bottom: 1rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

h3::before {
    content: '';
    display: inline-block;
    width: 6px;
    height: 24px;
    background: linear-gradient(180deg, var(--primary) 0%, var(--secondary) 100%);
    border-radius: 3px;
}

.stButton>button {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
    color: white;
    border: none;
    padding: 0.75rem 2rem;
    font-size: 1rem;
    border-radius: 12px;
    font-weight: 600;
    transition: all 0.3s ease;
    box-shadow: 0 6px 20px rgba(13, 148, 136, 0.2);
    width: 100%;
    cursor: pointer;
}

.stButton>button:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 30px rgba(13, 148, 136, 0.3);
}

.stTextInput>div>div>input,
.stDateInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div>select {
    background-color: var(--input-bg) !important;
    border: 2px solid var(--border) !important;
    border-radius: 12px !important;
    padding: 0.75rem 1rem !important;
    color: var(--text) !important;
    transition: all 0.3s ease;
}

.stTextInput>div>div>input:focus,
.stDateInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus,
.stSelectbox>div>div>select:focus {
    border-color: var(--primary) !important;
    box-shadow: 0 0 0 4px rgba(13, 148, 136, 0.1) !important;
}

.card {
    background: var(--card-bg);
    padding: 1.75rem;
    border-radius: 20px;
    box-shadow: 0 12px 30px var(--shadow);
    margin: 1rem 0;
    border: 1px solid var(--border);
    position: relative;
    overflow: hidden;
}

.card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--primary), var(--secondary));
}

.success-msg {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    border-left: 4px solid #10b981;
    color: #065f46;
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1.5rem 0;
    text-align: center;
    font-weight: 500;
}

.error-msg {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
    border-left: 4px solid #ef4444;
    color: #7f1d1d;
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1.5rem 0;
    text-align: center;
}

.info-box {
    background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%);
    border-left: 4px solid #0284c7;
    color: #0c4a6e;
    padding: 1.5rem;
    border-radius: 12px;
    margin: 1.5rem 0;
}

/* Tabs styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 12px;
    background: var(--card-bg);
    padding: 10px;
    border-radius: 16px;
    border: 1px solid var(--border);
    box-shadow: 0 4px 12px var(--shadow);
}

.stTabs [data-baseweb="tab"] {
    background: var(--bg);
    border-radius: 10px;
    color: var(--text-muted);
    font-weight: 500;
    padding: 10px 24px;
    border: 1px solid var(--border);
}

.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, var(--primary) 0%, var(--primary-dark) 100%);
    color: white !important;
    border-color: var(--primary);
}

.footer {
    text-align: center;
    color: var(--text-muted);
    padding: 2rem;
    margin-top: 3rem;
    border-top: 1px solid var(--border);
}
</style>
""", unsafe_allow_html=True)

# ---------- CONSTANTS ----------
DEFAULT_EMAIL = "your_default_email@gmail.com"  # Will be overridden from secrets or sidebar
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
SHEET_NAME = "TODO_Tasks"

# ---------- SESSION STATE INIT ----------
if 'tasks' not in st.session_state:
    st.session_state.tasks = pd.DataFrame()  # holds latest from sheet
if 'last_sync' not in st.session_state:
    st.session_state.last_sync = None
if 'add_form' not in st.session_state:
    st.session_state.add_form = {'task': '', 'due_date': date.today()}
if 'filter_date' not in st.session_state:
    st.session_state.filter_date = date.today()
if 'show_calendar_tasks' not in st.session_state:
    st.session_state.show_calendar_tasks = []
if 'email_reminder_sent' not in st.session_state:
    st.session_state.email_reminder_sent = False
if 'debug_logs' not in st.session_state:
    st.session_state.debug_logs = []

# ---------- UTILITY FUNCTIONS ----------
def log_debug(msg, level="INFO"):
    t = datetime.now().strftime('%H:%M:%S')
    st.session_state.debug_logs.append(f"[{t}] [{level}] {msg}")
    if len(st.session_state.debug_logs) > 100:
        st.session_state.debug_logs = st.session_state.debug_logs[-100:]

def get_google_credentials():
    """Load Google service account credentials from st.secrets"""
    try:
        # Try common section names
        for section in ["google_credentials", "google", "gcp_service_account", "gcp"]:
            if section in st.secrets:
                creds_dict = dict(st.secrets[section])
                # Ensure private key is properly formatted
                pk = creds_dict.get("private_key", "")
                if pk and "\\n" in pk:
                    creds_dict["private_key"] = pk.replace("\\n", "\n")
                if "-----BEGIN PRIVATE KEY-----" not in pk and len(pk) > 100:
                    creds_dict["private_key"] = f"-----BEGIN PRIVATE KEY-----\n{pk}\n-----END PRIVATE KEY-----\n"
                return creds_dict
        # Fallback: top-level keys
        if all(k in st.secrets for k in ["type", "project_id", "private_key", "client_email"]):
            return dict(st.secrets)
        log_debug("No Google credentials found in secrets.", "ERROR")
        return None
    except Exception as e:
        log_debug(f"Error loading Google credentials: {e}", "ERROR")
        return None

def setup_google_sheets():
    """Connect to the TODO Google Sheet, create if needed"""
    try:
        creds_dict = get_google_credentials()
        if not creds_dict:
            st.error("❌ Google credentials not found in Streamlit secrets.")
            return None
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, SCOPES)
        client = gspread.authorize(creds)
        try:
            sheet = client.open(SHEET_NAME).sheet1
        except gspread.SpreadsheetNotFound:
            st.error(f"❌ Google Sheet '{SHEET_NAME}' not found. Create it and share with {creds_dict['client_email']}")
            return None
        # Ensure headers exist
        if sheet.row_count == 0 or not sheet.row_values(1):
            sheet.append_row(["ID", "Task", "Due Date", "Status", "Created Date"])
            log_debug("Added headers to sheet.")
        return sheet
    except Exception as e:
        st.error(f"❌ Google Sheets connection failed: {e}")
        log_debug(f"setup_google_sheets error: {traceback.format_exc()}")
        return None

def load_tasks():
    """Fetch all tasks from sheet and store in session state as DataFrame"""
    sheet = setup_google_sheets()
    if not sheet:
        return pd.DataFrame()
    try:
        data = sheet.get_all_values()
        if len(data) <= 1:
            df = pd.DataFrame(columns=["ID", "Task", "Due Date", "Status", "Created Date"])
        else:
            df = pd.DataFrame(data[1:], columns=data[0])
            # Convert date columns
            df['Due Date'] = pd.to_datetime(df['Due Date'], errors='coerce').dt.date
            df['Created Date'] = pd.to_datetime(df['Created Date'], errors='coerce')
        st.session_state.tasks = df
        st.session_state.last_sync = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return df
    except Exception as e:
        st.error(f"❌ Failed to load tasks: {e}")
        log_debug(f"load_tasks error: {e}")
        return pd.DataFrame()

def add_task_to_sheet(task_text, due_date):
    """Add a new task row to the Google Sheet"""
    sheet = setup_google_sheets()
    if not sheet:
        return False
    try:
        # Generate unique ID
        new_id = str(uuid.uuid4())[:8].upper()
        created = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        due_str = due_date.strftime("%Y-%m-%d") if due_date else ""
        row = [new_id, task_text, due_str, "Not Done", created]
        sheet.append_row(row)
        log_debug(f"Added task: {task_text}")
        return True
    except Exception as e:
        st.error(f"❌ Failed to add task: {e}")
        log_debug(f"add_task error: {e}")
        return False

def update_task_status(task_id, new_status):
    """Update the Status column for a given task ID"""
    sheet = setup_google_sheets()
    if not sheet:
        return False
    try:
        data = sheet.get_all_values()
        for i, row in enumerate(data[1:], start=2):  # rows are 1-indexed
            if row[0] == task_id:
                sheet.update_cell(i, 4, new_status)  # column 4 = Status
                return True
        log_debug(f"Task ID {task_id} not found for update.", "WARNING")
        return False
    except Exception as e:
        st.error(f"❌ Failed to update task: {e}")
        log_debug(f"update_task_status error: {e}")
        return False

def get_overdue_tasks():
    """Return list of tasks that are not done and past due date"""
    if st.session_state.tasks.empty:
        load_tasks()
    df = st.session_state.tasks.copy()
    if df.empty:
        return []
    today = date.today()
    overdue = df[(df['Status'] != "Done") & (df['Due Date'] < today)]
    return overdue.to_dict('records')

def send_email_notification(overdue_tasks, to_email=None):
    """Send an email alert about overdue tasks"""
    try:
        # Load email credentials
        email_sections = ['EMAIL', 'email', 'gmail', 'GMAIL']
        sender = None
        password = None
        for section in email_sections:
            if section in st.secrets:
                sec = st.secrets[section]
                sender = sec.get('sender_email') or sec.get('email') or sec.get('user')
                password = sec.get('sender_password') or sec.get('password') or sec.get('pass')
                if sender and password:
                    break
        if not sender or not password:
            # Direct keys
            sender = st.secrets.get('EMAIL_SENDER') or st.secrets.get('sender_email')
            password = st.secrets.get('EMAIL_PASSWORD') or st.secrets.get('sender_password')
        if not sender or not password:
            log_debug("Email credentials not configured", "ERROR")
            return False, "Email credentials missing in secrets."

        recipient = to_email or DEFAULT_EMAIL
        if not recipient or '@' not in recipient:
            return False, "No valid recipient email set."

        msg = MIMEMultipart('alternative')
        msg['From'] = formataddr(("TODO Flow Reminder", sender))
        msg['To'] = recipient
        msg['Subject'] = f"⏰ Overdue Tasks Alert - {date.today().strftime('%b %d, %Y')}"

        # Build HTML table of overdue tasks
        rows = ""
        for t in overdue_tasks:
            due_str = t['Due Date'].strftime('%Y-%m-%d') if hasattr(t['Due Date'], 'strftime') else str(t['Due Date'])
            rows += f"<tr><td style='padding:8px; border-bottom:1px solid #ddd;'>{t['Task']}</td><td style='padding:8px; color:#ef4444;'>{due_str}</td></tr>"

        html = f"""
        <html><body style="font-family:Arial,sans-serif;">
        <div style="max-width:600px; margin:auto; padding:20px;">
            <h2 style="color:#0d9488;">📋 Overdue Tasks Reminder</h2>
            <p>The following tasks are past their due date and still marked as <b>Not Done</b>:</p>
            <table style="width:100%; border-collapse:collapse; margin:20px 0;">
                <tr style="background:#0d9488; color:white;"><th style="padding:10px;">Task</th><th>Due Date</th></tr>
                {rows}
            </table>
            <p style="color:#64748b;">Please complete them or update their status in TODO Flow.</p>
            <hr>
            <p style="font-size:12px; color:#94a3b8;">Sent by TODO Flow • hrvolarfashion@gmail.com</p>
        </div></body></html>
        """

        msg.attach(MIMEText(html, 'html'))

        # Create SMTP connection
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465, timeout=10, context=context)
        server.login(sender, password)
        server.sendmail(sender, recipient, msg.as_string())
        server.quit()
        return True, f"Reminder sent to {recipient}"
    except Exception as e:
        log_debug(f"Email error: {traceback.format_exc()}")
        return False, str(e)

# ---------- SIDEBAR CONFIGURATION ----------
with st.sidebar:
    st.title("⚙️ TODO Flow Settings")
    st.markdown("---")
    # Email recipient for reminders
    st.subheader("📧 Default Reminder Email")
    reminder_email = st.text_input("Send reminders to:", value=DEFAULT_EMAIL,
                                   help="Enter the email to receive overdue task alerts.")
    st.markdown("---")

    # Quick actions
    if st.button("🔄 Refresh Tasks Now"):
        load_tasks()
        st.success("Tasks refreshed!")
        time.sleep(1)
        st.rerun()

    if st.button("📤 Send Overdue Reminders"):
        with st.spinner("Checking for overdue tasks..."):
            overdue = get_overdue_tasks()
            if not overdue:
                st.warning("No overdue tasks found.")
            else:
                success, msg = send_email_notification(overdue, reminder_email)
                if success:
                    st.success(msg)
                    st.session_state.email_reminder_sent = True
                else:
                    st.error(f"Failed to send: {msg}")

    # Debug logs (collapsed)
    with st.expander("🔧 Debug Logs"):
        if st.button("Clear Logs"):
            st.session_state.debug_logs.clear()
        for log in st.session_state.debug_logs[-15:]:
            st.text(log)

# ---------- MAIN HEADER ----------
st.markdown("""
<div style="text-align: center; margin-top: 1rem;">
    <h1>✅ TODO Flow</h1>
    <h2>Smart Task Manager with Google Sheets Sync</h2>
</div>
""", unsafe_allow_html=True)

# ---------- TABS ----------
tab1, tab2, tab3, tab4 = st.tabs([
    "📋 My Tasks",
    "➕ Add New Task",
    "📅 Calendar View",
    "⚡ Overdue Alerts"
])

# ========== TAB 1: MY TASKS ==========
with tab1:
    st.markdown("### 📌 All Tasks")
    if st.button("🔄 Load / Refresh from Sheet", key="refresh_tab1"):
        load_tasks()
        st.success("Data refreshed!")
        time.sleep(0.5)
        st.rerun()

    # Load tasks if not yet loaded
    if st.session_state.tasks.empty:
        load_tasks()

    df = st.session_state.tasks.copy()
    if df.empty:
        st.info("No tasks found. Add your first task in the 'Add New Task' tab.")
    else:
        # Sort by due date ascending
        df = df.sort_values(by=['Due Date', 'Created Date'], ascending=[True, False])

        # Display each task as a card with checkbox
        for idx, row in df.iterrows():
            task_id = row['ID']
            task_text = row['Task']
            due_date = row['Due Date']
            status = row['Status']
            is_done = status == "Done"
            overdue = (due_date < date.today()) and (status != "Done")

            # Style card based on status
            border_color = "#10b981" if is_done else ("#ef4444" if overdue else "#0d9488")
            opacity = "0.7" if is_done else "1"
            with st.container():
                st.markdown(f"""
                <div class="card" style="border-left: 4px solid {border_color}; opacity: {opacity};">
                    <div style="display: flex; align-items: center; gap: 1rem;">
                        <div style="flex: 1;">
                            <div style="font-size: 1.1rem; font-weight: 600; color: var(--text);">
                                {task_text}
                            </div>
                            <div style="font-size: 0.9rem; color: var(--text-muted); margin-top: 0.25rem;">
                                📅 Due: {due_date.strftime('%b %d, %Y') if hasattr(due_date, 'strftime') else due_date}
                                {"<span style='color:#ef4444; font-weight:600;'> (Overdue)</span>" if overdue else ""}
                                {"<span style='color:#10b981;'> (Completed)</span>" if is_done else ""}
                            </div>
                        </div>
                        <div style="display: flex; align-items: center; gap: 0.5rem;">
                            <span style="font-size: 0.85rem; color: var(--text-muted);">{status}</span>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Checkbox to toggle status
                col1, col2, col3 = st.columns([0.5, 0.5, 5])
                with col1:
                    new_status = st.checkbox("Done", value=is_done, key=f"chk_{task_id}",
                                             help="Mark task as completed",
                                             on_change=None)
                with col2:
                    if st.button("🗑️", key=f"del_{task_id}", help="Delete task"):
                        # Delete logic (optional, not requested but useful)
                        pass  # Implement if needed

                # If checkbox changed, update sheet and session state
                if new_status != is_done:
                    new_status_str = "Done" if new_status else "Not Done"
                    if update_task_status(task_id, new_status_str):
                        # Update local DataFrame
                        st.session_state.tasks.loc[st.session_state.tasks['ID'] == task_id, 'Status'] = new_status_str
                        st.success(f"Task '{task_text[:30]}...' updated!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error("Failed to update task.")

        # Show last sync time
        if st.session_state.last_sync:
            st.caption(f"Last synced: {st.session_state.last_sync}")

# ========== TAB 2: ADD NEW TASK ==========
with tab2:
    st.markdown("### ➕ Create a New Task")
    with st.form("add_task_form"):
        task_input = st.text_input("Task Description", placeholder="What needs to be done?")
        due_input = st.date_input("Due Date", value=date.today())
        submit = st.form_submit_button("Add Task")

        if submit:
            if not task_input.strip():
                st.error("Please enter a task description.")
            else:
                if add_task_to_sheet(task_input.strip(), due_input):
                    st.success("Task added successfully!")
                    # Refresh local tasks
                    load_tasks()
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error("Failed to add task to Google Sheets.")

# ========== TAB 3: CALENDAR VIEW ==========
with tab3:
    st.markdown("### 📅 Task Calendar")
    pick_date = st.date_input("Select a date to view tasks", value=date.today(), key="cal_date")
    show_all = st.checkbox("Show all tasks up to this date", value=False)

    # Load tasks
    if st.session_state.tasks.empty:
        load_tasks()
    df = st.session_state.tasks.copy()

    if df.empty:
        st.info("No tasks in the system.")
    else:
        if show_all:
            filtered = df[df['Due Date'] <= pick_date]
        else:
            filtered = df[df['Due Date'] == pick_date]

        if filtered.empty:
            st.info(f"No tasks {'on or before' if show_all else 'on'} {pick_date.strftime('%b %d, %Y')}.")
        else:
            st.success(f"Found {len(filtered)} task(s).")
            for _, row in filtered.iterrows():
                status = row['Status']
                due = row['Due Date']
                overdue = (due < date.today()) and status != "Done"
                icon = "✅" if status == "Done" else ("🔴" if overdue else "🟡")
                st.markdown(f"""
                <div class="card" style="margin-bottom: 0.5rem;">
                    <b>{icon} {row['Task']}</b><br>
                    <small>Due: {due.strftime('%b %d, %Y')} | Status: {status}</small>
                </div>
                """, unsafe_allow_html=True)

# ========== TAB 4: OVERDUE ALERTS ==========
with tab4:
    st.markdown("### ⚡ Overdue Tasks Monitor")
    if st.button("🔍 Check for Overdue Tasks"):
        overdue = get_overdue_tasks()
        if not overdue:
            st.success("All tasks are on track! No overdue items.")
        else:
            st.warning(f"Found {len(overdue)} overdue task(s):")
            for t in overdue:
                due_str = t['Due Date'].strftime('%b %d, %Y') if hasattr(t['Due Date'], 'strftime') else t['Due Date']
                st.markdown(f"- **{t['Task']}** — Due: {due_str}")

            st.markdown("---")
            send_col1, send_col2 = st.columns(2)
            with send_col1:
                if st.button("📧 Send Reminder Email", key="send_reminder_tab4"):
                    with st.spinner("Sending..."):
                        success, msg = send_email_notification(overdue, reminder_email)
                        if success:
                            st.success(msg)
                        else:
                            st.error(f"Failed: {msg}")
            with send_col2:
                st.caption(f"Reminder will be sent to: **{reminder_email}**")

# ---------- FOOTER ----------
st.markdown("""
<div class="footer">
    <div style="margin-bottom: 0.5rem;">
        <strong style="color: var(--primary);">TODO Flow</strong> — Smart Task Management
    </div>
    <div style="font-size: 0.85rem; color: var(--text-muted);">
        Synced with Google Sheets • Automated Reminders
    </div>
</div>
""", unsafe_allow_html=True)
