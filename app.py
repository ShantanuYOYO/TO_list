import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime, date, timedelta
import pandas as pd
import json
import time
import os
import traceback
import uuid
import html

# ---------- PAGE CONFIGURATION ----------
st.set_page_config(
    page_title="TODO Flow - Smart Task Manager",
    page_icon="✅",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------- CUSTOM CSS ----------
# Design concept: a "task manifest" — tasks read like shipping-label stubs,
# stamped DELIVERED / IN TRANSIT / OVERDUE, with monospace tracking IDs.
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@500;600;700&family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@500;600;700&display=swap');

:root {
    --ink: #1c2430;
    --ink-soft: #5b6472;
    --ink-faint: #94a0ad;
    --paper: #eef0ed;
    --paper-card: #ffffff;
    --rule: #d7dbdf;
    --rule-strong: #b9c0c6;
    --brand: #2b3a55;
    --brand-soft: #3d5074;
    --stamp-red: #b6402c;
    --stamp-red-bg: #f7e7e3;
    --stamp-green: #2f6b52;
    --stamp-green-bg: #e6f0ea;
    --stamp-amber: #a8761f;
    --stamp-amber-bg: #f6efdd;
    --shadow: rgba(28, 36, 48, 0.08);
}

@media (prefers-color-scheme: dark) {
    :root {
        --ink: #e8eaef;
        --ink-soft: #aab1bd;
        --ink-faint: #707886;
        --paper: #11151d;
        --paper-card: #1b212c;
        --rule: #313a48;
        --rule-strong: #424c5c;
        --brand: #8da3d2;
        --brand-soft: #a3b6dc;
        --stamp-red: #e2796a;
        --stamp-red-bg: #2e1d1c;
        --stamp-green: #6cc09a;
        --stamp-green-bg: #1b2922;
        --stamp-amber: #dab15b;
        --stamp-amber-bg: #2c2516;
        --shadow: rgba(0, 0, 0, 0.45);
    }
}

@media (prefers-reduced-motion: reduce) {
    * { transition: none !important; animation: none !important; }
}

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
* { color: var(--ink); }

.stApp { background: var(--paper); }
.main .block-container { max-width: 900px; margin: 0 auto; padding-top: 2.25rem; }

hr { border: none; border-top: 1.5px solid var(--rule); margin: 1rem 0; }

/* ---- Header ---- */
.manifest-header { text-align: center; margin: 0.25rem 0 2rem; }
.manifest-eyebrow {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: var(--ink-faint);
    margin-bottom: 0.6rem;
}
.manifest-title {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 700;
    font-size: 2.6rem;
    color: var(--ink);
    margin: 0;
    letter-spacing: -0.02em;
}
.manifest-rule {
    width: 56px;
    height: 3px;
    background: var(--brand);
    margin: 1rem auto;
    border-radius: 2px;
}
.manifest-sub {
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    color: var(--ink-soft);
    font-weight: 400;
}

h3 {
    font-family: 'Space Grotesk', sans-serif;
    color: var(--ink);
    font-weight: 600;
    font-size: 1.05rem;
    margin: 1.2rem 0 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1.5px solid var(--rule);
    letter-spacing: -0.01em;
}

/* ---- Buttons ---- */
.stButton>button {
    background: var(--brand);
    color: #fff !important;
    border: none;
    padding: 0.65rem 1.5rem;
    font-size: 0.92rem;
    font-weight: 600;
    border-radius: 8px;
    transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
    box-shadow: 0 2px 8px var(--shadow);
    width: 100%;
}
.stButton>button p { color: #fff !important; }
.stButton>button:hover {
    background: var(--brand-soft);
    transform: translateY(-1px);
    box-shadow: 0 6px 16px var(--shadow);
}
.stButton>button:focus-visible { outline: 2px solid var(--brand); outline-offset: 2px; }

/* ---- Inputs ---- */
.stTextInput>div>div>input,
.stDateInput>div>div>input,
.stTextArea>div>div>textarea,
.stSelectbox>div>div>select {
    background-color: var(--paper-card) !important;
    border: 1.5px solid var(--rule) !important;
    border-radius: 8px !important;
    padding: 0.65rem 0.9rem !important;
    color: var(--ink) !important;
}
.stTextInput>div>div>input:focus,
.stDateInput>div>div>input:focus,
.stTextArea>div>div>textarea:focus,
.stSelectbox>div>div>select:focus {
    border-color: var(--brand) !important;
    box-shadow: 0 0 0 3px rgba(43, 58, 85, 0.14) !important;
}

div[data-testid="stForm"] {
    background: var(--paper-card);
    border: 1px solid var(--rule);
    border-radius: 12px;
    padding: 1.5rem 1.75rem 0.5rem;
    box-shadow: 0 4px 16px var(--shadow);
}

/* ---- Tabs ---- */
.stTabs [data-baseweb="tab-list"] {
    gap: 4px;
    background: transparent;
    border-bottom: 1.5px solid var(--rule);
}
.stTabs [data-baseweb="tab"] {
    background: transparent;
    border-radius: 6px 6px 0 0;
    color: var(--ink-faint);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.76rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    font-weight: 600;
    padding: 0.7rem 1.1rem;
    border: none;
}
.stTabs [aria-selected="true"] {
    color: var(--brand) !important;
    background: var(--paper-card);
    border-bottom: 2px solid var(--brand);
}
.stTabs [data-baseweb="tab"] p { color: inherit !important; }

/* ---- Task card: shipping-label style ---- */
.task-card {
    background: var(--paper-card);
    border-radius: 10px;
    box-shadow: 0 4px 16px var(--shadow);
    margin: 0.85rem 0 0.4rem;
    border: 1px solid var(--rule);
    display: flex;
    overflow: hidden;
    position: relative;
}
.task-card.is-overdue { border-color: var(--stamp-red); }
.task-card.is-done { opacity: 0.6; }

.task-stub {
    flex: 0 0 84px;
    border-right: 1.5px dashed var(--rule-strong);
    padding: 1rem 0.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--paper);
}
.task-id {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.7rem;
    font-weight: 600;
    color: var(--ink-faint);
    letter-spacing: 0.04em;
    writing-mode: vertical-rl;
    text-orientation: upright;
    line-height: 1.3;
}

.task-body { flex: 1; padding: 1rem 1.3rem; position: relative; }
.task-text {
    font-size: 1.05rem;
    font-weight: 600;
    color: var(--ink);
    line-height: 1.4;
    padding-right: 6.5rem;
}
.task-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    color: var(--ink-soft);
    margin-top: 0.55rem;
    letter-spacing: 0.02em;
    text-transform: uppercase;
}
.task-meta.overdue-meta { color: var(--stamp-red); font-weight: 600; }

.stamp {
    position: absolute;
    top: 0.95rem;
    right: 1.2rem;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.64rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    padding: 0.3rem 0.55rem;
    border: 1.5px dashed currentColor;
    border-radius: 5px;
    transform: rotate(-6deg);
    white-space: nowrap;
}
.stamp.delivered { color: var(--stamp-green); background: var(--stamp-green-bg); }
.stamp.overdue { color: var(--stamp-red); background: var(--stamp-red-bg); }
.stamp.pending { color: var(--stamp-amber); background: var(--stamp-amber-bg); }
.stamp.unscheduled { color: var(--ink-faint); background: var(--paper); }

@media (max-width: 640px) {
    .task-card { flex-direction: column; }
    .task-stub {
        flex-direction: row;
        border-right: none;
        border-bottom: 1.5px dashed var(--rule-strong);
        width: 100%;
        padding: 0.4rem 1rem;
    }
    .task-id { writing-mode: horizontal-tb; text-orientation: mixed; }
    .task-text { padding-right: 0; }
}

/* ---- Calendar cards ---- */
.cal-card {
    display: flex;
    align-items: center;
    gap: 0.9rem;
    background: var(--paper-card);
    border: 1px solid var(--rule);
    border-left: 4px solid var(--ink-faint);
    border-radius: 8px;
    padding: 0.85rem 1.1rem;
    margin-bottom: 0.6rem;
}
.cal-card.done { border-left-color: var(--stamp-green); opacity: 0.7; }
.cal-card.overdue { border-left-color: var(--stamp-red); }
.cal-card.pending { border-left-color: var(--stamp-amber); }
.cal-icon { font-size: 1.05rem; }
.cal-task { font-weight: 600; font-size: 0.98rem; }
.cal-meta {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    color: var(--ink-soft);
    margin-top: 0.15rem;
    text-transform: uppercase;
    letter-spacing: 0.02em;
}

/* ---- Overdue alert rows ---- */
.alert-row {
    display: flex;
    align-items: center;
    gap: 0.75rem;
    background: var(--stamp-red-bg);
    border-left: 3px solid var(--stamp-red);
    border-radius: 6px;
    padding: 0.65rem 1rem;
    margin-bottom: 0.5rem;
}
.alert-dot { width: 8px; height: 8px; border-radius: 50%; background: var(--stamp-red); flex-shrink: 0; }
.alert-task { font-weight: 600; flex: 1; }
.alert-due {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    color: var(--stamp-red);
    text-transform: uppercase;
    letter-spacing: 0.03em;
    white-space: nowrap;
}

/* ---- Native alerts (st.success / st.error / st.warning / st.info) ---- */
div[data-testid="stAlert"] {
    border-radius: 8px !important;
    font-family: 'Inter', sans-serif !important;
}

/* ---- Sidebar ---- */
section[data-testid="stSidebar"] {
    background: var(--paper-card);
    border-right: 1px solid var(--rule);
}
section[data-testid="stSidebar"] h1 {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.25rem;
    font-weight: 700;
    text-align: left;
    color: var(--ink);
    margin-bottom: 0.1rem;
}
section[data-testid="stSidebar"] h3 {
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.74rem;
    text-transform: uppercase;
    letter-spacing: 0.07em;
    color: var(--ink-faint);
    font-weight: 600;
    border-bottom: none;
    margin-top: 0.4rem;
    padding-bottom: 0;
}

.console-box {
    background: var(--ink);
    color: #b8e6c4;
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    line-height: 1.6;
    padding: 0.85rem;
    border-radius: 8px;
    max-height: 220px;
    overflow-y: auto;
}

/* ---- Footer ---- */
.manifest-footer {
    text-align: center;
    color: var(--ink-faint);
    padding: 2rem 0 1rem;
    margin-top: 2.5rem;
    border-top: 1.5px solid var(--rule);
    font-family: 'JetBrains Mono', monospace;
    font-size: 0.72rem;
    letter-spacing: 0.04em;
    text-transform: uppercase;
}
.manifest-footer strong {
    color: var(--brand);
    font-family: 'Space Grotesk', sans-serif;
    text-transform: none;
    letter-spacing: 0;
    font-size: 0.95rem;
}
</style>
""", unsafe_allow_html=True)

# ---------- CONSTANTS ----------
SCOPES = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
SHEET_NAME = "TODO_Tasks"

# ---------- SESSION STATE INIT ----------
if 'tasks' not in st.session_state:
    st.session_state.tasks = pd.DataFrame()  # holds latest from sheet
if 'last_sync' not in st.session_state:
    st.session_state.last_sync = None
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

            # Drop fully/partially blank rows (stray empty rows in the sheet,
            # e.g. from manual editing, otherwise produce an empty-string ID
            # shared by multiple rows -> duplicate widget keys below).
            blank_id = df['ID'].astype(str).str.strip() == ''
            if blank_id.any():
                log_debug(f"Dropped {blank_id.sum()} row(s) with a blank ID from the sheet.", "WARNING")
                df = df[~blank_id]

            # Guard against duplicate IDs (e.g. a row duplicated by a manual
            # sheet edit, or a copy/paste). Keep the first occurrence only so
            # every ID -> exactly one row, which keeps widget keys unique.
            dup_id = df['ID'].duplicated()
            if dup_id.any():
                log_debug(f"Dropped {dup_id.sum()} duplicate-ID row(s) from the sheet (kept first occurrence).", "WARNING")
                df = df[~dup_id]

            # Due Date and Created Date are stored as date-only (e.g. "2026-06-25").
            # Due Date may be blank for tasks with no due date set, which becomes NaT.
            # format='mixed' keeps this tolerant of any older rows that might still
            # have a time component saved in the same column.
            df['Due Date'] = pd.to_datetime(df['Due Date'], errors='coerce', format='mixed')
            df['Created Date'] = pd.to_datetime(df['Created Date'], errors='coerce', format='mixed')
            df = df.reset_index(drop=True)
        st.session_state.tasks = df
        st.session_state.last_sync = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return df
    except Exception as e:
        st.error(f"❌ Failed to load tasks: {e}")
        log_debug(f"load_tasks error: {e}")
        return pd.DataFrame()

def add_task_to_sheet(task_text, due_date):
    """Add a new task row to the Google Sheet.
    due_date may be a date (no time component) or None if no due date was set.
    The Created Date (just 'Date' in the UI) is always set automatically to today's date."""
    sheet = setup_google_sheets()
    if not sheet:
        return False
    try:
        # Generate unique ID
        new_id = str(uuid.uuid4())[:8].upper()
        created = date.today().strftime("%Y-%m-%d")
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
    """Return list of tasks that are not done, have a due date, and are past it"""
    if st.session_state.tasks.empty:
        load_tasks()
    df = st.session_state.tasks.copy()
    if df.empty:
        return []
    today = pd.Timestamp(date.today())
    mask = df['Due Date'].notna() & (df['Status'] != "Done") & (df['Due Date'] < today)
    overdue = df[mask]
    return overdue.to_dict('records')

# ---------- SIDEBAR CONFIGURATION ----------
with st.sidebar:
    st.title("⚙️ Settings")
    st.caption("Manifest configuration")
    st.markdown("---")

    # Quick actions
    if st.button("🔄 Refresh Tasks Now"):
        load_tasks()
        st.success("Tasks refreshed!")
        time.sleep(1)
        st.rerun()

    # Debug logs (collapsed)
    with st.expander("🔧 Debug Logs"):
        if st.button("Clear Logs"):
            st.session_state.debug_logs.clear()
        logs = st.session_state.debug_logs[-15:]
        if logs:
            logs_html = "<br>".join(html.escape(log) for log in logs)
        else:
            logs_html = "No logs yet."
        st.markdown(f'<div class="console-box">{logs_html}</div>', unsafe_allow_html=True)

# ---------- MAIN HEADER ----------
st.markdown("""
<div class="manifest-header">
    <div class="manifest-eyebrow">Task Manifest · Synced with Google Sheets</div>
    <h1 class="manifest-title">TODO Flow</h1>
    <div class="manifest-rule"></div>
    <div class="manifest-sub">Every task tracked, stamped, and accounted for.</div>
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

        # Display each task as a manifest-style label card with checkbox
        for idx, row in df.iterrows():
            task_id = row['ID']
            task_text_raw = row['Task']
            task_text = html.escape(str(task_text_raw))
            due_date = row['Due Date']  # pandas Timestamp (date only) or NaT
            status = row['Status']
            is_done = status == "Done"
            has_due_date = pd.notna(due_date)
            overdue = has_due_date and (not is_done) and (due_date.date() < date.today())

            if is_done:
                stamp_class, stamp_label = "delivered", "DELIVERED"
            elif not has_due_date:
                stamp_class, stamp_label = "unscheduled", "NO DUE DATE"
            elif overdue:
                stamp_class, stamp_label = "overdue", "OVERDUE"
            else:
                stamp_class, stamp_label = "pending", "IN TRANSIT"

            card_classes = "task-card"
            if overdue:
                card_classes += " is-overdue"
            if is_done:
                card_classes += " is-done"

            if has_due_date:
                due_display = f"Due {due_date.strftime('%b %d, %Y')}"
            else:
                due_display = "No due date set"
            meta_class = "task-meta overdue-meta" if overdue else "task-meta"

            with st.container():
                st.markdown(f"""
                <div class="{card_classes}">
                    <div class="task-stub"><span class="task-id">{task_id}</span></div>
                    <div class="task-body">
                        <span class="stamp {stamp_class}">{stamp_label}</span>
                        <div class="task-text">{task_text}</div>
                        <div class="{meta_class}">{due_display}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                # Checkbox to toggle status
                col1, col2, col3 = st.columns([0.5, 0.5, 5])
                with col1:
                    new_status = st.checkbox("Done", value=is_done, key=f"chk_{idx}_{task_id}",
                                             help="Mark task as completed")
                with col2:
                    if st.button("🗑️", key=f"del_{idx}_{task_id}", help="Delete task"):
                        # Delete logic (optional, not requested but useful)
                        pass  # Implement if needed

                # If checkbox changed, update sheet and session state
                if new_status != is_done:
                    new_status_str = "Done" if new_status else "Not Done"
                    if update_task_status(task_id, new_status_str):
                        # Update local DataFrame
                        st.session_state.tasks.loc[st.session_state.tasks['ID'] == task_id, 'Status'] = new_status_str
                        st.success(f"Task '{str(task_text_raw)[:30]}...' updated!")
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
    st.caption("Add a new entry to today's manifest. The creation date is set automatically.")
    with st.form("add_task_form"):
        task_input = st.text_input("Task Description", placeholder="What needs to be done?")
        has_due_date = st.checkbox("Set a due date", value=True,
                                    help="Uncheck to add a task with no due date.")
        due_date_input = st.date_input("Due Date", value=date.today(), disabled=not has_due_date)
        submit = st.form_submit_button("Add Task")

        if submit:
            if not task_input.strip():
                st.error("Please enter a task description.")
            else:
                due_date_value = due_date_input if has_due_date else None
                if add_task_to_sheet(task_input.strip(), due_date_value):
                    if has_due_date:
                        st.success("Task added successfully!")
                    else:
                        st.success("Task added successfully (no due date set)!")
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
        dated = df[df['Due Date'].notna()].copy()
        undated_count = len(df) - len(dated)

        if show_all:
            filtered = dated[dated['Due Date'].dt.date <= pick_date]
        else:
            filtered = dated[dated['Due Date'].dt.date == pick_date]

        if filtered.empty:
            st.info(f"No tasks {'on or before' if show_all else 'on'} {pick_date.strftime('%b %d, %Y')}.")
        else:
            st.success(f"Found {len(filtered)} task(s).")
            for _, row in filtered.iterrows():
                status = row['Status']
                due = row['Due Date']
                task_text = html.escape(str(row['Task']))
                overdue = (due.date() < date.today()) and status != "Done"

                if status == "Done":
                    cal_class, icon = "done", "✅"
                elif overdue:
                    cal_class, icon = "overdue", "🔴"
                else:
                    cal_class, icon = "pending", "🟡"

                due_display = due.strftime('%b %d, %Y')
                st.markdown(f"""
                <div class="cal-card {cal_class}">
                    <div class="cal-icon">{icon}</div>
                    <div>
                        <div class="cal-task">{task_text}</div>
                        <div class="cal-meta">Due {due_display} · {html.escape(str(status))}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

        if undated_count:
            st.caption(f"📌 {undated_count} task(s) have no due date set and aren't shown here — see the My Tasks tab.")

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
                task_text = html.escape(str(t['Task']))
                st.markdown(f"""
                <div class="alert-row">
                    <span class="alert-dot"></span>
                    <span class="alert-task">{task_text}</span>
                    <span class="alert-due">Due {due_str}</span>
                </div>
                """, unsafe_allow_html=True)

# ---------- FOOTER ----------
st.markdown("""
<div class="manifest-footer">
    <strong>TODO Flow</strong><br>
    Synced with Google Sheets
</div>
""", unsafe_allow_html=True)
