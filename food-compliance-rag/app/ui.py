"""
Streamlit UI for Food Regulatory Compliance Copilot.
Integrated with the Node.js API Gateway (Auth, PDF Upload, Audit Logging)
and FastAPI RAG Compliance Engine.
"""

import os
import streamlit as st
import requests

NODE_API = os.getenv("NODE_API_BASE_URL", "http://localhost:3000/api")
FASTAPI_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="FSSAI Food Regulatory Compliance Copilot",
    page_icon="🛡️",
    layout="wide",
)

# ── Session State for Theme & Auth ──────────────────────────────
if "theme_mode" not in st.session_state:
    st.session_state["theme_mode"] = "dark"

if "token" not in st.session_state:
    st.session_state["token"] = None
if "user" not in st.session_state:
    st.session_state["user"] = None


def get_headers():
    if st.session_state.get("token"):
        return {"Authorization": f"Bearer {st.session_state['token']}"}
    return {}


# ── Dynamic CSS for Light / Dark Mode ───────────────────────────
def apply_theme_css():
    if st.session_state["theme_mode"] == "light":
        css = """
        <style>
            /* ── Base Light Theme ── */
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
            
            /* ── Typography & Headings ── */
            h1, h2, h3, h4, h5, h6, p, span, label, div, [data-testid="stMarkdownContainer"] p {
                color: #0f172a !important;
            }
            [data-testid="stCaptionContainer"] p, .stCaption, small, code {
                color: #334155 !important;
                background-color: transparent !important;
            }
            
            /* ── Buttons (Sign Out, Browse, Trigger, etc.) ── */
            .stButton > button {
                background-color: #f1f5f9 !important;
                color: #0f172a !important;
                border: 1px solid #cbd5e1 !important;
                font-weight: 500 !important;
            }
            .stButton > button:hover {
                background-color: #e2e8f0 !important;
                color: #0284c7 !important;
                border-color: #94a3b8 !important;
            }
            .stButton > button[kind="primary"] {
                background-color: #0284c7 !important;
                color: #ffffff !important;
                border: none !important;
            }
            .stButton > button[kind="primary"]:hover {
                background-color: #0369a1 !important;
                color: #ffffff !important;
            }

            /* ── File Uploader (Fix dark dropzone & browse button) ── */
            [data-testid="stFileUploader"] {
                background-color: #ffffff !important;
                border: 1px dashed #cbd5e1 !important;
                border-radius: 8px !important;
                padding: 1rem !important;
            }
            [data-testid="stFileUploader"] section {
                background-color: #ffffff !important;
            }
            [data-testid="stFileUploader"] section div, 
            [data-testid="stFileUploader"] section span, 
            [data-testid="stFileUploader"] section small {
                color: #475569 !important;
            }
            [data-testid="stFileUploader"] button {
                background-color: #f1f5f9 !important;
                color: #0f172a !important;
                border: 1px solid #cbd5e1 !important;
            }
            [data-testid="stFileUploader"] button:hover {
                background-color: #e2e8f0 !important;
                color: #0284c7 !important;
            }

            /* ── Selectbox / Dropdowns (Fix black dropdown background) ── */
            .stSelectbox [data-baseweb="select"], 
            .stSelectbox [data-baseweb="select"] > div,
            div[data-baseweb="popover"],
            ul[role="listbox"],
            li[role="option"] {
                background-color: #ffffff !important;
                color: #0f172a !important;
                border-color: #cbd5e1 !important;
            }
            .stSelectbox span, .stSelectbox div {
                color: #0f172a !important;
            }
            li[role="option"]:hover, li[aria-selected="true"] {
                background-color: #f1f5f9 !important;
                color: #0284c7 !important;
            }

            /* ── Inputs & Text Areas ── */
            .stTextInput>div>div>input, .stTextArea textarea {
                background-color: #ffffff !important;
                color: #0f172a !important;
                border: 1px solid #cbd5e1 !important;
            }
            .stTextInput>div>div>input:focus, .stTextArea textarea:focus {
                border-color: #0284c7 !important;
                box-shadow: 0 0 0 1px #0284c7 !important;
            }

            /* ── Expanders ── */
            div[data-testid="stExpander"] {
                background-color: #ffffff !important;
                border: 1px solid #e2e8f0 !important;
                border-radius: 8px !important;
                box-shadow: 0 1px 3px rgba(0,0,0,0.04) !important;
            }
            div[data-testid="stExpander"] summary {
                color: #0f172a !important;
            }
            div[data-testid="stExpander"] summary:hover {
                color: #0284c7 !important;
            }
            div[data-testid="stExpander"] summary svg {
                fill: #64748b !important;
            }

            /* ── Alerts & Info Boxes (Fix dark/faint info boxes) ── */
            [data-testid="stAlert"] {
                background-color: #f8fafc !important;
                color: #0f172a !important;
                border: 1px solid #e2e8f0 !important;
            }
            [data-testid="stAlert"] p {
                color: #0f172a !important;
            }

            /* ── Theme Button (Sun / Moon) ── */
            .theme-toggle-container button {
                background-color: #ffffff !important;
                border: 1px solid #cbd5e1 !important;
                color: #0f172a !important;
                font-size: 1.35rem !important;
                border-radius: 9999px !important;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1) !important;
            }
            .theme-toggle-container button:hover {
                background-color: #f1f5f9 !important;
                border-color: #94a3b8 !important;
            }
        </style>
        """
    else:
        css = """
        <style>
            /* ── Base Dark Theme ── */
            .stApp, [data-testid="stAppViewContainer"], [data-testid="stHeader"] {
                background-color: #0e1117 !important;
                color: #fafafa !important;
            }
            [data-testid="stSidebar"] {
                background-color: #161b22 !important;
                border-right: 1px solid #30363d !important;
            }
            .stButton > button {
                background-color: #21262d !important;
                color: #e6edf3 !important;
                border: 1px solid #30363d !important;
            }
            .stButton > button[kind="primary"] {
                background-color: #238636 !important;
                color: #ffffff !important;
                border: none !important;
            }
            .theme-toggle-container button {
                background-color: #21262d !important;
                border: 1px solid #30363d !important;
                color: #f0f6fc !important;
                font-size: 1.35rem !important;
                border-radius: 9999px !important;
            }
        </style>
        """
    st.markdown(css, unsafe_allow_html=True)


apply_theme_css()


# ══════════════════════════════════════════════════════════════
# GATEWAY SCREEN: If user is NOT logged in, show Login / Register
# ══════════════════════════════════════════════════════════════
if not st.session_state.get("token"):
    col_l, col_center, col_r = st.columns([1, 2, 1])
    
    with col_center:
        st.markdown("<h2 style='text-align: center;'>🛡️ FSSAI Regulatory Compliance Copilot</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Secure AI Compliance Intelligence</p>", unsafe_allow_html=True)
        st.markdown("---")

        auth_tab = st.radio("Please Sign In to Access the Dashboard", ["Login", "Create Account"], horizontal=True)

        if auth_tab == "Login":
            st.subheader("Login to your Account")
            login_email = st.text_input("Email Address", value="test@example.com", key="login_email")
            login_pass = st.text_input("Password", type="password", value="password123", key="login_pass")
            
            if st.button("Sign In", type="primary", use_container_width=True):
                if not login_email or not login_pass:
                    st.warning("Please enter both email and password.")
                else:
                    try:
                        res = requests.post(
                            f"{NODE_API}/auth/login",
                            json={"email": login_email, "password": login_pass},
                            timeout=10,
                        )
                        if res.status_code == 200:
                            data = res.json()
                            st.session_state["token"] = data.get("token")
                            st.session_state["user"] = data.get("user")
                            st.success("Authentication successful! Redirecting to dashboard...")
                            st.rerun()
                        else:
                            st.error(res.json().get("error", "Invalid credentials. Please check your email/password."))
                    except Exception as e:
                        st.error(f"Cannot reach server: {e}")

        else:
            st.subheader("Create a New Account")
            reg_name = st.text_input("Full Name", value="", key="reg_name", placeholder="e.g. John Doe")
            reg_email = st.text_input("Email Address", value="", key="reg_email", placeholder="e.g. user@company.com")
            reg_pass = st.text_input("Password (min 8 characters)", type="password", key="reg_pass")
            
            if st.button("Register & Get Access", type="primary", use_container_width=True):
                if not reg_name or not reg_email or not reg_pass:
                    st.warning("Please fill in all registration fields.")
                elif len(reg_pass) < 8:
                    st.warning("Password must be at least 8 characters long.")
                else:
                    try:
                        res = requests.post(
                            f"{NODE_API}/auth/register",
                            json={"name": reg_name, "email": reg_email, "password": reg_pass},
                            timeout=10,
                        )
                        if res.status_code == 201:
                            data = res.json()
                            st.session_state["token"] = data.get("token")
                            st.session_state["user"] = data.get("user")
                            st.success("Account registered successfully! Redirecting...")
                            st.rerun()
                        else:
                            st.error(res.json().get("error", "Registration failed."))
                    except Exception as e:
                        st.error(f"Cannot reach server: {e}")

        st.markdown("---")
        st.info("💡 **Demo Credentials**: Email `test@example.com` | Password `password123`")

    st.stop()


# ══════════════════════════════════════════════════════════════
# DASHBOARD (Accessible ONLY when authenticated with JWT token)
# ══════════════════════════════════════════════════════════════

# ── Sidebar Account & Navigation ──
user = st.session_state.get("user") or {}

st.sidebar.markdown("### 👤 User Profile")
st.sidebar.success(f"**{user.get('name', 'User')}**")

email_display = user.get('email', '')
role_display = user.get('role', 'user').upper()
st.sidebar.markdown(f"📧 **{email_display}**")
st.sidebar.markdown(f"🛡️ Role: **{role_display}**")

if st.sidebar.button("🚪 Sign Out", use_container_width=True):
    st.session_state["token"] = None
    st.session_state["user"] = None
    st.rerun()

st.sidebar.divider()
st.sidebar.markdown("### 🧭 Navigation")

nav_options = [
    "System Status",
    "Document Library",
    "Semantic Search",
    "Compliance Assessment",
    "Company Policy Upload",
    "Audit History",
]
tab_selection = st.sidebar.radio("Go to:", nav_options)

# ── Main Header with Light / Dark Mode Toggle Icon ──
head_title, head_toggle = st.columns([10, 1])
with head_title:
    st.title("🛡️ FSSAI Food Regulatory Compliance Copilot")
    st.caption(f"Logged in as **{user.get('name')}** | AI Compliance Intelligence Active")
with head_toggle:
    st.write("")  # vertical spacing
    theme_icon = "☀️" if st.session_state["theme_mode"] == "light" else "🌙"
    st.markdown('<div class="theme-toggle-container">', unsafe_allow_html=True)
    if st.button(theme_icon, key="dash_header_theme_toggle", help=f"Switch to {'Dark' if st.session_state['theme_mode'] == 'light' else 'Light'} Mode"):
        st.session_state["theme_mode"] = "dark" if st.session_state["theme_mode"] == "light" else "light"
        st.rerun()
    st.markdown('</div>', unsafe_allow_html=True)

# ── Tab 1: System Status ──
if tab_selection == "System Status":
    st.subheader("System Health & Service Connectivity")
    
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Node.js Gateway (Port 3000)")
        try:
            res_node = requests.get(f"{NODE_API.replace('/api', '')}/", timeout=5)
            if res_node.status_code == 200:
                ndata = res_node.json()
                st.success(f"Status: {ndata.get('status', 'running').upper()}")
                st.write(f"Service: {ndata.get('service')}")
                st.caption(f"Active Endpoints: {list(ndata.get('endpoints', {}).keys())}")
            else:
                st.error(f"Node.js Gateway returned status {res_node.status_code}")
        except Exception as e:
            st.error(f"Node.js Gateway unreachable: {e}")

    with col2:
        st.markdown("### FastAPI RAG Backend (Port 8000)")
        try:
            res = requests.get(f"{NODE_API}/compliance/health", timeout=10)
            if res.status_code == 200:
                data = res.json().get("data", {})
                st.success(f"Status: {data.get('status', '').upper()}")
                st.write(f"**LLM Provider:** {data.get('llm_provider')} | **Embedding:** {data.get('embedding_provider')}")
                db_info = data.get("database") or {}
                st.write(f"**Supabase DB:** {db_info.get('status', 'unknown')}")
                if db_info.get("version"):
                    st.caption(f"Engine: {db_info.get('version')[:60]}...")
                st.metric("Regulatory PDFs Indexed in data/", data.get("pdf_count", 0))
            else:
                st.error(f"FastAPI health check failed: {res.text}")
        except Exception as e:
            st.error(f"Could not connect to FastAPI proxy: {e}")

# ── Tab 2: Document Library ──
elif tab_selection == "Document Library":
    st.subheader("Indexed Regulatory Documents")
    
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Trigger Ingestion (Admin)"):
            with st.spinner("Ingesting PDFs..."):
                try:
                    res = requests.post(
                        f"{NODE_API}/compliance/ingest",
                        json={},
                        headers=get_headers(),
                        timeout=300,
                    )
                    if res.status_code == 200:
                        st.success("Ingestion executed successfully!")
                        st.json(res.json())
                    else:
                        st.error(f"Ingestion response ({res.status_code}): {res.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

    try:
        res = requests.get(f"{NODE_API}/compliance/documents", headers=get_headers(), timeout=10)
        if res.status_code == 200:
            docs = res.json().get("data", [])
            if docs:
                for d in docs:
                    with st.expander(f"📄 {d.get('title') or d.get('filename')}"):
                        st.write(f"**Filename:** {d.get('filename')}")
                        st.write(f"**Publication Date:** {d.get('publication_date') or 'N/A'}")
                        st.write(f"**Pages:** {d.get('page_count')}")
                        st.write(f"**Document ID:** `{d.get('id')}`")
            else:
                st.info("No documents indexed yet.")
        else:
            st.error(f"Unable to load documents: {res.text}")
    except Exception as e:
        st.warning(f"Unable to load documents: {e}")

# ── Tab 3: Semantic Search ──
elif tab_selection == "Semantic Search":
    st.subheader("Search Regulatory Knowledge Base")
    
    query = st.text_input(
        "Enter compliance query or regulation topic:",
        value="What hygiene records should a food facility maintain?",
    )
    top_k = st.slider("Number of results", min_value=1, max_value=10, value=5)

    if st.button("Search Regulations", type="primary"):
        if not query.strip():
            st.warning("Please enter a search query.")
        else:
            with st.spinner("Retrieving from Supabase pgvector..."):
                try:
                    res = requests.post(
                        f"{NODE_API}/compliance/search",
                        json={"query": query, "top_k": top_k},
                        headers=get_headers(),
                        timeout=30,
                    )
                    if res.status_code == 200:
                        data = res.json().get("data", {})
                        results = data.get("results", [])
                        st.write(f"Found {len(results)} relevant regulatory passages:")
                        for r in results:
                            sim = r.get("similarity", 0)
                            with st.container():
                                st.markdown(f"#### {r.get('doc_title') or r.get('doc_filename')} (Pages {r.get('page_start')}–{r.get('page_end')})")
                                st.caption(f"Similarity Score: {sim:.4f} | Section: {r.get('section_title') or 'N/A'}")
                                st.text_area("Content excerpt", r.get("content"), height=150, key=f"chunk_{r.get('chunk_id')}")
                                st.divider()
                    else:
                        st.error(f"Search failed: {res.text}")
                except Exception as e:
                    st.error(f"Search request error: {e}")

# ── Tab 4: Compliance Assessment ──
elif tab_selection == "Compliance Assessment":
    st.subheader("RAG Compliance Verification (Saved to Audit History)")

    question = st.text_input(
        "Compliance Question / Requirement:",
        value="What mandatory labelling elements must appear on pre-packaged food containers?",
    )
    area = st.selectbox(
        "Compliance Area:",
        ["General Labelling & Display", "Contaminants & Residues", "Food Additives", "Licensing & Registration", "Hygiene & Sanitary Practices"],
    )
    evidence = st.text_area(
        "Company Policy / Audit Evidence Document:",
        value="Our product labels currently include: Product Brand Name, List of Ingredients in descending order, Net Quantity, Batch Number, Date of Manufacture, Best Before Date, Manufacturer Name and Complete Address, and FSSAI License Number with Logo.",
        height=150,
    )
    facility_desc = st.text_input(
        "Facility Description (Optional):",
        value="Packaged snack foods manufacturer in Maharashtra",
    )

    if st.button("Run Compliance Assessment", type="primary"):
        with st.spinner("Analyzing against FSSAI regulations & Groq LLM..."):
            try:
                res = requests.post(
                    f"{NODE_API}/compliance/check",
                    json={
                        "question": question,
                        "company_evidence": evidence,
                        "compliance_area": area,
                        "facility_description": facility_desc,
                        "top_k": 5,
                    },
                    headers=get_headers(),
                    timeout=120,
                )
                if res.status_code == 200:
                    payload = res.json()
                    result = payload.get("data", payload)
                    status = result.get("overall_status")
                    
                    status_colors = {
                        "COMPLIANT": "green",
                        "PARTIALLY_COMPLIANT": "orange",
                        "MISSING_EVIDENCE": "blue",
                        "POTENTIALLY_NON_COMPLIANT": "red",
                        "NEEDS_REVIEW": "gray",
                    }
                    st.markdown(f"### Overall Status: :{status_colors.get(status, 'gray')}[{status}]")
                    st.info(result.get("summary"))

                    findings = result.get("findings", [])
                    if findings:
                        st.subheader("Detailed Compliance Findings")
                        for idx, f in enumerate(findings):
                            with st.expander(f"Requirement: {f.get('requirement')} [{f.get('status')}]"):
                                st.write("**Status:**", f.get("status"))
                                st.write("**Explanation:**", f.get("explanation"))
                                if f.get("evidence_found"):
                                    st.write("**Evidence Found:**", ", ".join(f.get("evidence_found")))
                                if f.get("evidence_missing"):
                                    st.write("**Evidence Missing:**", ", ".join(f.get("evidence_missing")))
                                if f.get("recommended_actions"):
                                    st.write("**Recommended Actions:**")
                                    for act in f.get("recommended_actions"):
                                        st.write(f"- {act}")

                    st.success("✅ Assessment successfully recorded to your Audit History.")
                    st.warning(f"**Disclaimer:** {result.get('disclaimer')}")
                else:
                    st.error(f"Compliance check failed ({res.status_code}): {res.text}")
            except Exception as e:
                st.error(f"Request failed: {e}")

# ── Tab 5: Company Policy Upload ──
elif tab_selection == "Company Policy Upload":
    st.subheader("📄 Upload Company Policy Document (PDF)")
    st.caption("Upload your organization's internal standard or policy PDF. The Node.js gateway extracts text in-memory and stores it for compliance audits.")

    uploaded_file = st.file_uploader("Select PDF Policy File", type=["pdf"])
    if uploaded_file is not None:
        if st.button("Upload & Extract Text", type="primary"):
            with st.spinner("Uploading and extracting text via Node.js..."):
                try:
                    files = {"file": (uploaded_file.name, uploaded_file.getvalue(), "application/pdf")}
                    res = requests.post(
                        f"{NODE_API}/upload/policy",
                        files=files,
                        headers=get_headers(),
                        timeout=60,
                    )
                    if res.status_code == 201:
                        data = res.json()
                        st.success(f"Uploaded successfully! Extracted {data.get('char_count', 0)} characters.")
                        with st.expander("Preview Extracted Text"):
                            st.text_area("Extracted Policy Text", data.get("extracted_text", ""), height=250)
                    else:
                        st.error(f"Upload failed: {res.text}")
                except Exception as e:
                    st.error(f"Error during upload: {e}")

    st.divider()
    st.subheader("Your Uploaded Policy Documents")
    try:
        res = requests.get(f"{NODE_API}/upload/policies", headers=get_headers(), timeout=10)
        if res.status_code == 200:
            policies = res.json().get("data", [])
            if policies:
                for p in policies:
                    with st.expander(f"📑 {p.get('filename')} ({p.get('char_count')} chars) — {p.get('created_at')}"):
                        st.write(f"**Document ID:** `{p.get('id')}`")
                        st.write(f"**Uploaded on:** {p.get('created_at')}")
            else:
                st.info("No policy documents uploaded yet.")
    except Exception as e:
        st.error(f"Failed to fetch policies: {e}")

# ── Tab 6: Audit History ──
elif tab_selection == "Audit History":
    st.subheader("📋 Compliance Audit History")
    st.caption("Browse all historical compliance evaluations performed on your account.")

    try:
        res = requests.get(f"{NODE_API}/audit", headers=get_headers(), timeout=10)
        if res.status_code == 200:
            audit_data = res.json()
            audits = audit_data.get("data", [])
            pagination = audit_data.get("pagination", {})
            
            st.caption(f"Total audits recorded: **{pagination.get('total', len(audits))}**")
            
            if audits:
                for a in audits:
                    status = a.get("overall_status", "UNKNOWN")
                    with st.expander(f"[{status}] {a.get('question')} — {a.get('created_at')}"):
                        st.write(f"**Compliance Area:** {a.get('compliance_area')}")
                        st.write(f"**Overall Status:** `{status}`")
                        st.write(f"**Summary:** {a.get('summary')}")
                        st.caption(f"Audit Record ID: `{a.get('id')}`")
                        
                        if st.button("View Full Findings", key=f"btn_{a.get('id')}"):
                            det_res = requests.get(f"{NODE_API}/audit/{a.get('id')}", headers=get_headers(), timeout=10)
                            if det_res.status_code == 200:
                                det = det_res.json().get("data", {})
                                st.json(det.get("findings"))
            else:
                st.info("No compliance audits found. Run an evaluation from the 'Compliance Assessment' tab to create your first audit record.")
        else:
            st.error(f"Failed to fetch audit history: {res.text}")
    except Exception as e:
        st.error(f"Error fetching audit history: {e}")
