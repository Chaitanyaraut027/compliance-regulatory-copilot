"""
Food Regulatory Intelligence Co-pilot — User Interface
Connects with Node.js API Gateway (Auth, Audit History, PDF/Doc Upload)
and Python FastAPI RAG Service (pgvector search, Groq LLM compliance assessment).
"""

import os
import datetime
import requests
import streamlit as st

NODE_API = os.getenv("NODE_API_BASE_URL", "http://localhost:3000/api")
MAX_FILE_SIZE_BYTES = 5 * 1024 * 1024  # 5 MB limit

st.set_page_config(
    page_title="Food Regulatory Intelligence Co-pilot",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Session State Management ────────────────────────────────────
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "light"
if "token" not in st.session_state:
    st.session_state["token"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None
if "nav_view" not in st.session_state:
    st.session_state["nav_view"] = "Dashboard"
if "current_report" not in st.session_state:
    st.session_state["current_report"] = None
if "viewing_history_id" not in st.session_state:
    st.session_state["viewing_history_id"] = None


def get_headers():
    if st.session_state.get("token"):
        return {"Authorization": f"Bearer {st.session_state['token']}"}
    return {}


def format_date(dt_str):
    if not dt_str:
        return "N/A"
    try:
        # Parse ISO or Postgres timestamp
        cleaned = dt_str.replace("Z", "+00:00")
        dt = datetime.datetime.fromisoformat(cleaned)
        return dt.strftime("%b %d, %Y - %I:%M %p")
    except Exception:
        return str(dt_str)[:19]


def map_status(raw_status):
    raw = (raw_status or "").upper()
    if raw in ("COMPLIANT", "SATISFIED"):
        return {
            "label": "Compliant",
            "badge_color": "#15803d",
            "bg_color": "#dcfce7",
            "border_color": "#86efac",
            "icon": "✅",
            "category": "satisfied",
            "desc": "The available evidence supports the applicable requirement.",
        }
    elif raw in ("PARTIALLY_COMPLIANT", "POTENTIALLY_NON_COMPLIANT", "NEEDS_ATTENTION", "NON_COMPLIANT"):
        return {
            "label": "Needs Attention",
            "badge_color": "#b45309",
            "bg_color": "#fef3c7",
            "border_color": "#fcd34d",
            "icon": "⚠️",
            "category": "attention",
            "desc": "A potential regulatory gap or issue was identified.",
        }
    else:  # MISSING_EVIDENCE, NEEDS_REVIEW, INSUFFICIENT_INFORMATION
        return {
            "label": "Insufficient Information",
            "badge_color": "#1d4ed8",
            "bg_color": "#dbeafe",
            "border_color": "#93c5fd",
            "icon": "ℹ️",
            "category": "insufficient",
            "desc": "There is not enough evidence in the uploaded document to reach a conclusion.",
        }


# ── CSS Theming ────────────────────────────────────────────────
def apply_theme_css():
    is_light = st.session_state["theme_mode"] == "light"
    if is_light:
        css = """
        <style>
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
                background-color: #f8fafc !important;
                color: #0f172a !important;
            }
            [data-testid="stSidebar"] {
                background-color: #ffffff !important;
                border-right: 1px solid #e2e8f0 !important;
            }
            [data-testid="stSidebar"] * {
                color: #0f172a !important;
            }
            h1, h2, h3, h4, h5, h6, p, span, label, div {
                color: #0f172a !important;
            }
            .stButton > button {
                background-color: #ffffff !important;
                color: #0f172a !important;
                border: 1px solid #cbd5e1 !important;
                border-radius: 8px !important;
                font-weight: 500 !important;
                padding: 0.5rem 1rem !important;
                transition: all 0.2s ease !important;
            }
            .stButton > button:hover {
                background-color: #f1f5f9 !important;
                border-color: #0284c7 !important;
                color: #0284c7 !important;
            }
            .stButton > button[kind="primary"] {
                background-color: #0284c7 !important;
                color: #ffffff !important;
                border: none !important;
            }
            .stButton > button[kind="primary"]:hover {
                background-color: #0369a1 !important;
            }
            .status-badge {
                display: inline-flex;
                align-items: center;
                gap: 6px;
                padding: 6px 14px;
                border-radius: 20px;
                font-weight: 600;
                font-size: 0.9rem;
            }
            .report-card {
                background: #ffffff;
                border: 1px solid #e2e8f0;
                border-radius: 12px;
                padding: 1.5rem;
                margin-bottom: 1rem;
                box-shadow: 0 1px 3px rgba(0,0,0,0.05);
            }
            .disclaimer-banner {
                background: #f1f5f9;
                border-left: 4px solid #64748b;
                padding: 0.85rem 1.2rem;
                border-radius: 6px;
                font-size: 0.875rem;
                color: #475569;
                margin: 1rem 0;
            }
        </style>
        """
    else:
        css = """
        <style>
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
                background-color: #090d16 !important;
                color: #f1f5f9 !important;
            }
            [data-testid="stSidebar"] {
                background-color: #111827 !important;
                border-right: 1px solid #1f2937 !important;
            }
            .stButton > button {
                background-color: #1f2937 !important;
                color: #f9fafb !important;
                border: 1px solid #374151 !important;
                border-radius: 8px !important;
            }
            .stButton > button:hover {
                border-color: #38bdf8 !important;
                color: #38bdf8 !important;
            }
            .stButton > button[kind="primary"] {
                background-color: #0284c7 !important;
                color: #ffffff !important;
                border: none !important;
            }
            .report-card {
                background: #111827;
                border: 1px solid #1f2937;
                border-radius: 12px;
                padding: 1.5rem;
                margin-bottom: 1rem;
            }
            .disclaimer-banner {
                background: #1e293b;
                border-left: 4px solid #38bdf8;
                padding: 0.85rem 1.2rem;
                border-radius: 6px;
                font-size: 0.875rem;
                color: #cbd5e1;
                margin: 1rem 0;
            }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


apply_theme_css()


# ══════════════════════════════════════════════════════════════
# SCREEN 1 & 2: REGISTRATION & LOGIN (When not authenticated)
# ══════════════════════════════════════════════════════════════
if not st.session_state.get("token"):
    left_pad, main_col, right_pad = st.columns([1, 2, 1])

    with main_col:
        st.markdown(
            """
            <div style="text-align: center; margin-top: 2rem; margin-bottom: 1.5rem;">
                <span style="font-size: 3rem;">🛡️</span>
                <h1 style="margin: 0.5rem 0 0.2rem 0; font-size: 2rem;">Food Regulatory Intelligence Co-pilot</h1>
                <p style="color: #64748b; font-size: 1rem;">
                    Automated, evidence-based food compliance checking against official regulations
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        auth_choice = st.radio(
            "Account Access",
            ["Log In", "Create New Account"],
            horizontal=True,
            label_visibility="collapsed",
        )

        if auth_choice == "Log In":
            st.markdown("### Log In to Your Account")
            login_email = st.text_input("Work Email Address", value="test@example.com", key="auth_login_email")
            login_pass = st.text_input("Password", type="password", value="password123", key="auth_login_pass")

            if st.button("Log In", type="primary", use_container_width=True):
                if not login_email.strip() or not login_pass:
                    st.warning("Please provide both email and password.")
                else:
                    try:
                        with st.spinner("Authenticating with server..."):
                            resp = requests.post(
                                f"{NODE_API}/auth/login",
                                json={"email": login_email.strip(), "password": login_pass},
                                timeout=15,
                            )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state["token"] = data.get("token")
                            st.session_state["user"] = data.get("user")
                            st.session_state["nav_view"] = "Dashboard"
                            st.success("Login successful! Redirecting...")
                            st.rerun()
                        else:
                            err_msg = resp.json().get("error", "Invalid credentials. Please verify your email and password.")
                            st.error(f"Authentication failed: {err_msg}")
                    except Exception as e:
                        st.error(f"Cannot connect to the server at {NODE_API}. Please ensure the Node.js backend is running. ({e})")

        else:
            st.markdown("### Create an Account")
            reg_name = st.text_input("Your Full Name", placeholder="e.g. Priya Sharma", key="reg_full_name")
            reg_email = st.text_input("Work Email Address", placeholder="e.g. priya@biscuitco.com", key="reg_work_email")
            reg_pass = st.text_input("Password (min 8 characters)", type="password", key="reg_password")

            if st.button("Register Account", type="primary", use_container_width=True):
                if not reg_name.strip() or not reg_email.strip() or not reg_pass:
                    st.warning("Please fill out all registration fields.")
                elif len(reg_pass) < 8:
                    st.warning("Password must be at least 8 characters long.")
                else:
                    try:
                        with st.spinner("Creating your account..."):
                            resp = requests.post(
                                f"{NODE_API}/auth/register",
                                json={"name": reg_name.strip(), "email": reg_email.strip(), "password": reg_pass},
                                timeout=15,
                            )
                        if resp.status_code == 201:
                            data = resp.json()
                            st.session_state["token"] = data.get("token")
                            st.session_state["user"] = data.get("user")
                            st.session_state["nav_view"] = "Dashboard"
                            st.success("Account created successfully! Welcome to the Compliance Co-pilot.")
                            st.rerun()
                        else:
                            err_msg = resp.json().get("error", "Registration could not be completed.")
                            st.error(f"Registration error: {err_msg}")
                    except Exception as e:
                        st.error(f"Cannot reach server: {e}")

        st.markdown(
            """
            <div style="margin-top: 2rem; padding: 1rem; background: rgba(2, 132, 199, 0.08); border-radius: 8px; font-size: 0.875rem;">
                <strong>Demo Credentials:</strong><br>
                Email: <code>test@example.com</code> | Password: <code>password123</code>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.stop()


# ══════════════════════════════════════════════════════════════
# AUTHENTICATED APP SHELL (Sidebar, User Info, Navigation)
# ══════════════════════════════════════════════════════════════
user = st.session_state.get("user") or {}

# ── Sidebar Navigation ──
with st.sidebar:
    st.markdown("### 🛡️ Compliance Co-pilot")
    st.caption("Food Regulatory Intelligence")
    st.markdown("---")

    st.markdown(f"**👤 {user.get('name', 'User')}**")
    st.caption(f"{user.get('email', '')}")

    st.markdown("---")
    st.markdown("#### Navigation")

    nav_options = [
        "Dashboard",
        "Upload Document",
        "Compliance Reports",
        "Search Regulations",
    ]
    
    current_index = nav_options.index(st.session_state["nav_view"]) if st.session_state["nav_view"] in nav_options else 0
    selected_nav = st.radio("Navigation Menu", nav_options, index=current_index, label_visibility="collapsed")
    if selected_nav != st.session_state["nav_view"]:
        st.session_state["nav_view"] = selected_nav
        st.session_state["current_report"] = None
        st.rerun()

    st.markdown("---")
    # Theme toggle
    theme_label = "🌙 Dark Mode" if st.session_state["theme_mode"] == "light" else "☀️ Light Mode"
    if st.button(theme_label, use_container_width=True):
        st.session_state["theme_mode"] = "dark" if st.session_state["theme_mode"] == "light" else "light"
        st.rerun()

    # Step 8: Logout
    if st.button("🚪 Log Out", use_container_width=True):
        st.session_state["token"] = None
        st.session_state["user"] = None
        st.session_state["current_report"] = None
        st.session_state["viewing_history_id"] = None
        st.session_state["nav_view"] = "Dashboard"
        st.rerun()


# ── Render Helper: Detailed Compliance Report View ──────────────
def render_compliance_report(report_data, doc_name=None, date_str=None, allow_back=True):
    overall_status_raw = report_data.get("overall_status", "NEEDS_REVIEW")
    status_info = map_status(overall_status_raw)
    display_doc_name = doc_name or report_data.get("product_name") or "Food Product Specification"
    display_date = format_date(date_str or report_data.get("created_at") or datetime.datetime.now().isoformat())

    # Header Card
    st.markdown(
        f"""
        <div class="report-card" style="border-top: 4px solid {status_info['badge_color']};">
            <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
                <div>
                    <span style="font-size: 0.85rem; color: #64748b; text-transform: uppercase; font-weight: 600;">Product Document</span>
                    <h2 style="margin: 0.2rem 0; font-size: 1.6rem;">{display_doc_name}</h2>
                    <p style="color: #64748b; font-size: 0.9rem; margin: 0;">Date of Analysis: <strong>{display_date}</strong></p>
                </div>
                <div>
                    <span style="background-color: {status_info['bg_color']}; color: {status_info['badge_color']}; border: 1px solid {status_info['border_color']}; padding: 8px 18px; border-radius: 24px; font-weight: 700; font-size: 1rem; display: inline-flex; align-items: center; gap: 6px;">
                        {status_info['icon']} {status_info['label']}
                    </span>
                </div>
            </div>
            <div style="margin-top: 1.2rem; padding: 1rem; background: rgba(0,0,0,0.02); border-radius: 8px; border: 1px solid rgba(0,0,0,0.06);">
                <strong style="color: #0f172a;">Executive Summary:</strong>
                <p style="margin: 0.4rem 0 0 0; line-height: 1.5;">{report_data.get('summary', 'No summary available.')}</p>
            </div>
            <div class="disclaimer-banner">
                <strong>Notice:</strong> {report_data.get('disclaimer', 'This compliance assessment is generated using official regulatory reference documents for informational purposes. It does not constitute formal legal certification.')}
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    findings = report_data.get("findings", [])
    if not findings:
        st.info("No specific requirement breakdown returned for this document.")
        return

    # Categorize findings
    satisfied = [f for f in findings if map_status(f.get("status"))["category"] == "satisfied"]
    attention = [f for f in findings if map_status(f.get("status"))["category"] == "attention"]
    insufficient = [f for f in findings if map_status(f.get("status"))["category"] == "insufficient"]

    # Metrics summary row
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Requirements Evaluated", len(findings))
    with c2:
        st.metric("Requirements Satisfied", len(satisfied), delta=None)
    with c3:
        st.metric("Needs Attention", len(attention), delta=None)
    with c4:
        st.metric("Insufficient Evidence", len(insufficient), delta=None)

    st.markdown("---")
    st.subheader("Detailed Requirements Breakdown")

    # Tabs for finding categories
    tab_att, tab_sat, tab_ins, tab_all = st.tabs([
        f"⚠️ Needs Attention ({len(attention)})",
        f"✅ Satisfied Requirements ({len(satisfied)})",
        f"ℹ️ Insufficient Information ({len(insufficient)})",
        f"All Findings ({len(findings)})",
    ])

    def render_finding_card(f, idx):
        f_status = map_status(f.get("status"))
        with st.expander(f"{f_status['icon']} {f.get('requirement', 'Regulatory Requirement')} — [{f_status['label']}]", expanded=(f_status['category'] != "satisfied")):
            st.markdown(f"**Assessment Status:** <span style='color:{f_status['badge_color']}; font-weight:600;'>{f_status['label']}</span> ({f.get('status')})", unsafe_allow_html=True)
            st.markdown(f"**Explanation:**\n{f.get('explanation', 'No detailed explanation provided.')}")
            
            ev_found = f.get("evidence_found") or []
            if ev_found:
                st.markdown("**Evidence Found in Document:**")
                for e in ev_found:
                    st.markdown(f"- ✅ {e}")
            
            ev_missing = f.get("evidence_missing") or []
            if ev_missing:
                st.markdown("**Missing Information / Evidence Required:**")
                for m in ev_missing:
                    st.markdown(f"- ⚠️ {m}")
                    
            actions = f.get("recommended_actions") or []
            if actions:
                st.markdown("**Suggested Corrective Actions:**")
                for act in actions:
                    st.markdown(f"- 💡 {act}")

            reg_sources = f.get("regulatory_sources") or report_data.get("retrieved_sources") or []
            if reg_sources:
                st.caption("Supporting Regulatory References:")
                for s in reg_sources[:3]:
                    doc_title = s.get("document_name") or s.get("doc_title") or s.get("doc_filename") or "FSSAI Compendium"
                    pages = f"Pages {s.get('page_start')}–{s.get('page_end')}" if s.get("page_start") else ""
                    sec = f" | Section: {s.get('section')}" if s.get("section") else ""
                    st.caption(f"📖 **{doc_title}** {pages}{sec}")

    with tab_att:
        if attention:
            for i, f in enumerate(attention):
                render_finding_card(f, f"att_{i}")
        else:
            st.success("No critical regulatory gaps or issues identified in this category!")

    with tab_sat:
        if satisfied:
            for i, f in enumerate(satisfied):
                render_finding_card(f, f"sat_{i}")
        else:
            st.info("No fully satisfied requirements recorded.")

    with tab_ins:
        if insufficient:
            for i, f in enumerate(insufficient):
                render_finding_card(f, f"ins_{i}")
        else:
            st.success("All requirements had sufficient evidence.")

    with tab_all:
        for i, f in enumerate(findings):
            render_finding_card(f, f"all_{i}")

    st.markdown("---")
    btn_col1, btn_col2, _ = st.columns([1, 1, 2])
    with btn_col1:
        if st.button("📤 Check Another Document", key="report_another_doc", type="primary"):
            st.session_state["current_report"] = None
            st.session_state["nav_view"] = "Upload Document"
            st.rerun()
    with btn_col2:
        if st.button("🏠 Back to Dashboard", key="report_back_dash"):
            st.session_state["current_report"] = None
            st.session_state["nav_view"] = "Dashboard"
            st.rerun()


# ══════════════════════════════════════════════════════════════
# STEP 3: DASHBOARD
# ══════════════════════════════════════════════════════════════
if st.session_state["nav_view"] == "Dashboard":
    st.markdown(f"# Welcome back, {user.get('name', 'Auditor')}! 👋")
    st.markdown(
        """
        <p style="font-size: 1.1rem; color: #64748b;">
            Verify your food product specifications, ingredient lists, and package labels against official food regulations with automated, evidence-backed intelligence.
        </p>
        """,
        unsafe_allow_html=True,
    )

    # Primary Call to Action Banner
    dash_cta_col1, dash_cta_col2 = st.columns([3, 1])
    with dash_cta_col1:
        st.markdown(
            """
            <div style="background: linear-gradient(135deg, rgba(2, 132, 199, 0.12) 0%, rgba(56, 189, 248, 0.08) 100%); border: 1px solid rgba(2, 132, 199, 0.3); border-radius: 12px; padding: 1.5rem; margin: 1rem 0;">
                <h3 style="margin-top:0; color: #0284c7;">Ready to evaluate a food product?</h3>
                <p style="margin-bottom: 0.5rem; color: #334155;">
                    Upload a product specification sheet, label draft, or ingredient declaration (PDF or TXT, max 5 MB). The co-pilot will analyze it against official regulatory compendiums and return a complete compliance report.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with dash_cta_col2:
        st.write("")
        st.write("")
        if st.button("📤 Upload Document", type="primary", use_container_width=True, key="dash_btn_upload_start"):
            st.session_state["nav_view"] = "Upload Document"
            st.session_state["current_report"] = None
            st.rerun()

    st.markdown("---")
    st.subheader("📋 Recent Compliance Checks")

    # Fetch real recent audits from backend
    try:
        res = requests.get(f"{NODE_API}/audit?limit=5", headers=get_headers(), timeout=10)
        if res.status_code == 200:
            audit_json = res.json()
            audits = audit_json.get("data", [])
            total_checks = audit_json.get("pagination", {}).get("total", len(audits))

            if not audits:
                st.info("No compliance checks yet. Upload your first food product document above to generate a report.")
            else:
                st.caption(f"Showing {len(audits)} most recent of {total_checks} total compliance assessments on your account.")
                for a in audits:
                    status_info = map_status(a.get("overall_status"))
                    doc_title = a.get("product_name") or a.get("question") or "Food Product Specification"
                    created_date = format_date(a.get("created_at"))

                    with st.container():
                        c_info, c_action = st.columns([4, 1])
                        with c_info:
                            st.markdown(
                                f"""
                                <div style="display: flex; align-items: center; gap: 10px; margin-bottom: 4px;">
                                    <strong style="font-size: 1.05rem;">{doc_title}</strong>
                                    <span style="background: {status_info['bg_color']}; color: {status_info['badge_color']}; border: 1px solid {status_info['border_color']}; padding: 2px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">
                                        {status_info['icon']} {status_info['label']}
                                    </span>
                                </div>
                                <div style="font-size: 0.85rem; color: #64748b;">
                                    Area: <strong>{a.get('compliance_area')}</strong> | Assessed: {created_date}
                                </div>
                                <div style="font-size: 0.9rem; margin-top: 4px; color: #334155;">
                                    {a.get('summary', '')[:160]}...
                                </div>
                                """,
                                unsafe_allow_html=True,
                            )
                        with c_action:
                            st.write("")
                            if st.button("View Report ↗", key=f"dash_view_{a.get('id')}", use_container_width=True):
                                # Load full report from backend
                                det_resp = requests.get(f"{NODE_API}/audit/{a.get('id')}", headers=get_headers(), timeout=10)
                                if det_resp.status_code == 200:
                                    st.session_state["current_report"] = det_resp.json().get("data")
                                    st.session_state["nav_view"] = "Compliance Reports"
                                    st.rerun()
                                else:
                                    st.error("Failed to fetch full report details.")
                        st.markdown("<hr style='margin: 0.75rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
        else:
            st.error(f"Could not load compliance checks from server: {res.text}")
    except Exception as e:
        st.warning(f"Unable to reach backend service: {e}")


# ══════════════════════════════════════════════════════════════
# STEP 4 & 5 & 6: UPLOAD PRODUCT DOCUMENT & ANALYSE & VIEW REPORT
# ══════════════════════════════════════════════════════════════
elif st.session_state["nav_view"] == "Upload Document":
    # If a report was just generated in this session, show it!
    if st.session_state.get("current_report"):
        render_compliance_report(st.session_state["current_report"])
    else:
        st.title("📤 Upload Food Product Document")
        st.markdown(
            """
            Upload your food product specification, ingredient declaration, or label content. 
            The system will extract the readable text, retrieve relevant requirements from official food regulations, and generate an evidence-based compliance report.
            """
        )

        # Upload card
        with st.container():
            col_doc, col_params = st.columns([3, 2])

            with col_doc:
                st.subheader("1. Select Document")
                uploaded_file = st.file_uploader(
                    "Choose a file (PDF or TXT)",
                    type=["pdf", "txt"],
                    help="Maximum file size: 5 MB. Must contain readable text (not scanned images without OCR).",
                )

                if uploaded_file is not None:
                    # Client-side 5 MB file size check
                    if uploaded_file.size > MAX_FILE_SIZE_BYTES:
                        st.error(f"❌ File size ({uploaded_file.size / (1024*1024):.2f} MB) exceeds the maximum allowed size of 5 MB.")
                        uploaded_file = None
                    else:
                        st.success(f"File selected: **{uploaded_file.name}** ({uploaded_file.size / 1024:.1f} KB)")

            with col_params:
                st.subheader("2. Compliance Details")
                default_prod_name = ""
                if uploaded_file:
                    default_prod_name = os.path.splitext(uploaded_file.name)[0].replace("_", " ").title()

                product_name_input = st.text_input(
                    "Product / Document Name",
                    value=default_prod_name,
                    placeholder="e.g. Crispy Choco Chip Cookies",
                )

                compliance_area = st.selectbox(
                    "Primary Regulatory Compliance Area",
                    [
                        "General Labelling & Display",
                        "Food Additives",
                        "Contaminants & Residues",
                        "Licensing & Registration",
                        "Hygiene & Sanitary Practices",
                    ],
                    help="Select which regulatory domain to evaluate first against official compendiums.",
                )

                facility_info = st.text_input(
                    "Facility / Location Description (Optional)",
                    placeholder="e.g. Biscuit manufacturing facility in Maharashtra",
                )

            st.markdown("---")

            # Check Compliance Action Button
            btn_col, _ = st.columns([2, 3])
            with btn_col:
                run_check = st.button("🔍 Check Compliance", type="primary", use_container_width=True)

            if run_check:
                if uploaded_file is None:
                    st.warning("Please upload a food product document (PDF or TXT) before checking compliance.")
                else:
                    progress_container = st.container()
                    with progress_container:
                        progress_bar = st.progress(10, text="Uploading document to backend...")

                        try:
                            # ── Step 4: Upload to Node.js backend ──
                            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
                            upload_res = requests.post(
                                f"{NODE_API}/upload/policy",
                                files=files,
                                headers=get_headers(),
                                timeout=45,
                            )

                            if upload_res.status_code != 201:
                                err_msg = upload_res.json().get("error", "Document upload failed.")
                                progress_bar.empty()
                                st.error(f"Upload error: {err_msg}")
                            else:
                                upload_data = upload_res.json()
                                extracted_text = upload_data.get("extracted_text", "").strip()

                                if len(extracted_text) < 15:
                                    progress_bar.empty()
                                    st.error("The uploaded document contains little to no readable text. Please upload a document with readable text or specifications.")
                                else:
                                    progress_bar.progress(40, text="Extracting readable text and searching regulatory reference compendiums...")

                                    # ── Step 5: Analyse via Node.js -> FastAPI RAG ──
                                    question_text = (
                                        f"Assess regulatory compliance for product document '{product_name_input or uploaded_file.name}' "
                                        f"against mandatory standards, labelling rules, safety thresholds, and permitted additives."
                                    )

                                    progress_bar.progress(65, text="Running AI compliance analysis against retrieved regulatory clauses...")

                                    check_payload = {
                                        "question": question_text,
                                        "company_evidence": extracted_text,
                                        "compliance_area": compliance_area,
                                        "facility_description": facility_info or None,
                                        "product_name": product_name_input or uploaded_file.name,
                                        "top_k": 5,
                                    }

                                    check_res = requests.post(
                                        f"{NODE_API}/compliance/check",
                                        json=check_payload,
                                        headers=get_headers(),
                                        timeout=120,
                                    )

                                    if check_res.status_code == 200:
                                        progress_bar.progress(100, text="Assessment complete! Generating report...")
                                        result_payload = check_res.json().get("data", {})
                                        # Save in session and display Step 6
                                        st.session_state["current_report"] = result_payload
                                        progress_bar.empty()
                                        st.success("✅ Document analyzed and compliance report saved to history!")
                                        st.rerun()
                                    else:
                                        progress_bar.empty()
                                        err_detail = check_res.json().get("error", check_res.text)
                                        st.error(f"Compliance analysis failed: {err_detail}")

                        except Exception as e:
                            progress_bar.empty()
                            st.error(f"Communication error with backend: {e}")


# ══════════════════════════════════════════════════════════════
# STEP 7: COMPLIANCE REPORTS HISTORY
# ══════════════════════════════════════════════════════════════
elif st.session_state["nav_view"] == "Compliance Reports":
    if st.session_state.get("current_report"):
        render_compliance_report(st.session_state["current_report"])
    else:
        st.title("📋 Compliance Reports History")
        st.caption("Revisit any previous food regulatory compliance assessment performed on your account.")

        try:
            with st.spinner("Loading compliance history..."):
                res = requests.get(f"{NODE_API}/audit?limit=50", headers=get_headers(), timeout=15)
            
            if res.status_code == 200:
                audit_resp = res.json()
                audits = audit_resp.get("data", [])
                pagination = audit_resp.get("pagination", {})
                
                if not audits:
                    st.info("No compliance checks yet. Upload a product document to create your first report.")
                    if st.button("Upload Document Now", type="primary"):
                        st.session_state["nav_view"] = "Upload Document"
                        st.rerun()
                else:
                    st.write(f"Total reports found: **{pagination.get('total', len(audits))}**")
                    st.markdown("---")

                    for a in audits:
                        status_info = map_status(a.get("overall_status"))
                        doc_title = a.get("product_name") or a.get("question") or "Food Product Assessment"
                        created_date = format_date(a.get("created_at"))

                        with st.container():
                            col_txt, col_btn = st.columns([5, 1])
                            with col_txt:
                                st.markdown(
                                    f"""
                                    <div style="display: flex; align-items: center; gap: 10px;">
                                        <h4 style="margin: 0; font-size: 1.1rem;">{doc_title}</h4>
                                        <span style="background: {status_info['bg_color']}; color: {status_info['badge_color']}; border: 1px solid {status_info['border_color']}; padding: 2px 10px; border-radius: 12px; font-size: 0.8rem; font-weight: 600;">
                                            {status_info['icon']} {status_info['label']}
                                        </span>
                                    </div>
                                    <div style="font-size: 0.85rem; color: #64748b; margin-top: 2px;">
                                        Area: <strong>{a.get('compliance_area')}</strong> | Assessed: <strong>{created_date}</strong>
                                    </div>
                                    <p style="margin: 6px 0 0 0; font-size: 0.9rem; color: #334155;">
                                        {a.get('summary', '')[:220]}...
                                    </p>
                                    """,
                                    unsafe_allow_html=True,
                                )
                            with col_btn:
                                st.write("")
                                if st.button("View Report", key=f"hist_btn_{a.get('id')}", use_container_width=True):
                                    det_resp = requests.get(f"{NODE_API}/audit/{a.get('id')}", headers=get_headers(), timeout=10)
                                    if det_resp.status_code == 200:
                                        st.session_state["current_report"] = det_resp.json().get("data")
                                        st.rerun()
                                    else:
                                        st.error("Failed to load report.")

                            st.markdown("<hr style='margin: 1rem 0; border: none; border-top: 1px solid #e2e8f0;'>", unsafe_allow_html=True)
            else:
                st.error(f"Failed to fetch audit history ({res.status_code}): {res.text}")
        except Exception as e:
            st.error(f"Error fetching compliance history: {e}")


# ══════════════════════════════════════════════════════════════
# OPTIONAL HELPER: SEARCH REGULATIONS
# ══════════════════════════════════════════════════════════════
elif st.session_state["nav_view"] == "Search Regulations":
    st.title("🔍 Search Food Regulations")
    st.caption("Look up specific regulatory clauses and compendiums from official food standards.")

    search_query = st.text_input(
        "Search regulatory requirements or topics:",
        value="What mandatory labelling elements must appear on pre-packaged food containers?",
    )
    top_results = st.slider("Maximum matching clauses", min_value=1, max_value=10, value=5)

    if st.button("Search Official Regulations", type="primary"):
        if not search_query.strip():
            st.warning("Please enter a search topic or question.")
        else:
            with st.spinner("Searching regulatory reference compendiums..."):
                try:
                    res = requests.post(
                        f"{NODE_API}/compliance/search",
                        json={"query": search_query.strip(), "top_k": top_results},
                        headers=get_headers(),
                        timeout=30,
                    )
                    if res.status_code == 200:
                        data = res.json().get("data", {})
                        results = data.get("results", [])
                        st.success(f"Found {len(results)} relevant regulatory passages:")

                        for idx, r in enumerate(results, 1):
                            doc_title = r.get("doc_title") or r.get("doc_filename") or "Regulatory Compendium"
                            pages = f"Pages {r.get('page_start')}–{r.get('page_end')}" if r.get("page_start") else ""
                            sec = f" | Section: {r.get('section_title')}" if r.get("section_title") else ""

                            with st.expander(f"{idx}. {doc_title} ({pages}{sec})", expanded=(idx == 1)):
                                st.caption(f"Relevance Score: {r.get('similarity', 0):.4f}")
                                st.write(r.get("content"))
                    else:
                        st.error(f"Search request failed: {res.text}")
                except Exception as e:
                    st.error(f"Error connecting to search service: {e}")
