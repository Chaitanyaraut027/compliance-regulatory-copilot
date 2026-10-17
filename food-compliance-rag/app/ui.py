"""
Optional Streamlit UI for Food Regulatory Compliance RAG.

Run with:
    streamlit run app/ui.py
"""

import os
import streamlit as st
import requests

API_BASE = os.getenv("API_BASE_URL", "http://localhost:8000")

st.set_page_config(
    page_title="FSSAI Food Regulatory Compliance Copilot",
    page_icon="🛡️",
    layout="wide",
)

st.title("🛡️ FSSAI Food Regulatory Compliance Copilot")
st.caption("RAG-powered Food Regulatory Intelligence & Compliance Verification")

# Sidebar navigation
tab_selection = st.sidebar.radio(
    "Navigation",
    ["System Status", "Document Library", "Semantic Search", "Compliance Assessment"],
)

# ── Tab 1: System Status ──
if tab_selection == "System Status":
    st.subheader("System Health & Database Connection")
    try:
        res = requests.get(f"{API_BASE}/health", timeout=5)
        if res.status_code == 200:
            data = res.json()
            st.success(f"API Status: {data.get('status').upper()}")
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Regulatory PDFs in data/", data.get("pdf_count", 0))
                st.write("**OpenAI Configured:**", "✅ Yes" if data.get("openai_configured") else "❌ No")
            with col2:
                db_info = data.get("database") or {}
                st.write("**Database Status:**", db_info.get("status", "unknown"))
                if db_info.get("version"):
                    st.caption(f"DB Engine: {db_info.get('version')[:80]}...")
                elif db_info.get("detail"):
                    st.warning(f"Connection Note: {db_info.get('detail')}")
        else:
            st.error(f"API error: {res.status_code}")
    except Exception as e:
        st.error(f"Could not connect to API at {API_BASE}: {e}")

# ── Tab 2: Document Library ──
elif tab_selection == "Document Library":
    st.subheader("Indexed Regulatory Documents")
    col1, col2 = st.columns([3, 1])
    with col2:
        if st.button("Trigger Ingestion"):
            with st.spinner("Ingesting PDFs..."):
                try:
                    res = requests.post(f"{API_BASE}/ingest", json={}, timeout=300)
                    if res.status_code == 200:
                        st.success("Ingestion executed successfully!")
                        st.json(res.json())
                    else:
                        st.error(f"Ingestion failed: {res.text}")
                except Exception as e:
                    st.error(f"Error: {e}")

    try:
        res = requests.get(f"{API_BASE}/documents", timeout=5)
        if res.status_code == 200:
            docs = res.json()
            if docs:
                for d in docs:
                    with st.expander(f"📄 {d.get('title') or d.get('filename')}"):
                        st.write(f"**Filename:** {d.get('filename')}")
                        st.write(f"**Publication Date:** {d.get('publication_date') or 'N/A'}")
                        st.write(f"**Pages:** {d.get('page_count')}")
                        st.write(f"**Document ID:** `{d.get('id')}`")
            else:
                st.info("No documents indexed yet. Run ingestion after setting up your Supabase database.")
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

    if st.button("Search Regulations"):
        if not query.strip():
            st.warning("Please enter a search query.")
        else:
            with st.spinner("Retrieving from pgvector..."):
                try:
                    res = requests.post(
                        f"{API_BASE}/search",
                        json={"query": query, "top_k": top_k},
                        timeout=30,
                    )
                    if res.status_code == 200:
                        data = res.json()
                        results = data.get("results", [])
                        st.write(f"Found {len(results)} relevant regulatory passages:")
                        for r in results:
                            sim = r.get("similarity", 0)
                            with st.container():
                                st.markdown(f"#### {r.get('doc_title') or r.get('doc_filename')} (Pages {r.get('page_start')}–{r.get('page_end')})")
                                st.caption(f"Similarity Score: {sim:.4f} | Section: {r.get('section_title') or 'N/A'}")
                                st.text_area("Content excerpt", r.get("content"), height=150, key=r.get("chunk_id"))
                                st.divider()
                    else:
                        st.error(f"Search failed: {res.text}")
                except Exception as e:
                    st.error(f"Search request error: {e}")

# ── Tab 4: Compliance Assessment ──
elif tab_selection == "Compliance Assessment":
    st.subheader("RAG Compliance Verification")
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
        with st.spinner("Analyzing against FSSAI regulations..."):
            try:
                res = requests.post(
                    f"{API_BASE}/compliance/check",
                    json={
                        "question": question,
                        "company_evidence": evidence,
                        "compliance_area": area,
                        "facility_description": facility_desc,
                        "top_k": 5,
                    },
                    timeout=90,
                )
                if res.status_code == 200:
                    result = res.json()
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
                        for f in findings:
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

                    st.warning(f"**Disclaimer:** {result.get('disclaimer')}")
                else:
                    st.error(f"Compliance check failed: {res.text}")
            except Exception as e:
                st.error(f"Request failed: {e}")
