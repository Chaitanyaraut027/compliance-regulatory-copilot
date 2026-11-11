"""
Generate clean, professional, human-designed architecture, database ER, and UI preview diagrams for README.md.
Uses Matplotlib and Pillow with crisp vector shapes, clear typography, and clean contrast.
"""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch

def create_architecture_diagram():
    fig, ax = plt.subplots(figsize=(16, 10), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Background
    fig.patch.set_facecolor('#0f172a') # Dark slate background
    ax.set_facecolor('#0f172a')
    
    # Title Header
    ax.text(8.0, 9.48, "Food Regulatory Compliance Intelligence System — Architecture", 
            ha='center', va='center', fontsize=18, fontweight='bold', color='#f8fafc', fontfamily='sans-serif')
    ax.text(8.0, 9.15, "Dual-Pipeline RAG: Batch Regulatory Ingestion + Real-Time Zero-Hallucination Compliance Audit", 
            ha='center', va='center', fontsize=11, color='#94a3b8', fontfamily='sans-serif')
    
    # ── Pipeline 1 Container: Ingestion ──
    rect1 = FancyBboxPatch((0.5, 5.0), 15.0, 3.65, boxstyle="round,pad=0.2,rounding_size=0.3",
                           facecolor='#1e293b', edgecolor='#334155', linewidth=1.5, alpha=0.9)
    ax.add_patch(rect1)
    ax.text(0.9, 8.4, "PIPELINE 1: REGULATORY INGESTION & VECTOR INDEXING (OFFLINE / BATCH)", 
            fontsize=10.5, fontweight='bold', color='#38bdf8', fontfamily='sans-serif')
    
    # ── Pipeline 2 Container: Real-Time Audit ──
    rect2 = FancyBboxPatch((0.5, 0.45), 15.0, 4.15, boxstyle="round,pad=0.2,rounding_size=0.3",
                           facecolor='#1e293b', edgecolor='#334155', linewidth=1.5, alpha=0.9)
    ax.add_patch(rect2)
    ax.text(0.9, 4.35, "PIPELINE 2: REAL-TIME COMPLIANCE AUDIT & CITATION ENGINE (ONLINE)", 
            fontsize=10.5, fontweight='bold', color='#4ade80', fontfamily='sans-serif')
    
    def draw_card(x, y, w, h, title, subtitle, bullets, badge, badge_color, bg_color='#0f172a', border_color='#3b82f6'):
        card = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.15,rounding_size=0.2",
                              facecolor=bg_color, edgecolor=border_color, linewidth=1.4)
        ax.add_patch(card)
        # Badge
        if badge:
            badge_len = len(badge) * 0.11 + 0.2
            badge_patch = FancyBboxPatch((x + w - badge_len - 0.15, y + h - 0.38), badge_len, 0.28,
                                         boxstyle="round,pad=0.05,rounding_size=0.1",
                                         facecolor=badge_color, edgecolor='none')
            ax.add_patch(badge_patch)
            ax.text(x + w - 0.15 - badge_len/2, y + h - 0.24, badge,
                    ha='center', va='center', fontsize=7.5, fontweight='bold', color='#ffffff', fontfamily='sans-serif')
        
        # Title
        ax.text(x + 0.2, y + h - 0.3, title, fontsize=10.5, fontweight='bold', color='#f1f5f9', fontfamily='sans-serif')
        if subtitle:
            ax.text(x + 0.2, y + h - 0.55, subtitle, fontsize=8.5, color='#94a3b8', fontfamily='sans-serif')
        
        # Bullets
        curr_y = y + h - 0.85
        for b in bullets:
            ax.text(x + 0.25, curr_y, f"• {b}", fontsize=8.0, color='#cbd5e1', fontfamily='sans-serif')
            curr_y -= 0.28
            
    # Pipeline 1 Cards
    draw_card(0.8, 5.4, 2.8, 2.5, "Official Regulations", "FSSAI Compendiums", 
              ["Labelling & Display", "Food Additives", "Contaminants Limits", "Licensing & Hygiene"],
              "PDF Source", "#64748b", border_color='#475569')
              
    draw_card(4.2, 5.4, 3.0, 2.5, "PyMuPDF + Chunker", "Semantic Chunking",
              ["Page & section tracking", "900-char sliding window", "120-char context overlap", "Deduplication hash"],
              "Python 3.12", "#0284c7", border_color='#0284c7')

    draw_card(7.8, 5.4, 3.0, 2.5, "FastEmbed Engine", "BAAI/bge-small-en-v1.5",
              ["Dense vector generation", "384-dimensional output", "100% Local CPU inference", "Zero API cost / rate limits"],
              "Local AI", "#8b5cf6", border_color='#8b5cf6')

    draw_card(11.4, 5.4, 3.7, 2.5, "Supabase PostgreSQL", "Vector Store with pgvector",
              ["documents (metadata, hash)", "document_chunks (embedding)", "IVFFlat cosine indexing", "Exact page citations"],
              "pgvector", "#10b981", border_color='#10b981')

    # Pipeline 1 Arrows
    def draw_arrow(start, end, label=""):
        ax.annotate('', xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="-|>", color='#38bdf8', lw=2.0, mutation_scale=15))
        if label:
            mx, my = (start[0] + end[0])/2, (start[1] + end[1])/2 + 0.16
            ax.text(mx, my, label, ha='center', va='center', fontsize=7.5, color='#7dd3fc', 
                    fontweight='bold', fontfamily='sans-serif',
                    bbox=dict(boxstyle="round,pad=0.15", facecolor='#0f172a', edgecolor='none', alpha=0.85))

    draw_arrow((3.7, 6.65), (4.15, 6.65), "Extract Text")
    draw_arrow((7.3, 6.65), (7.75, 6.65), "Text Chunks")
    draw_arrow((10.9, 6.65), (11.35, 6.65), "Store Vectors")

    # Pipeline 2 Cards
    draw_card(0.8, 1.0, 2.6, 2.9, "React 19 Frontend", "Tailwind CSS + Vite",
              ["Modern Audit Dashboard", "Policy PDF Drag & Drop", "Evidence input forms", "Live Report & Status UI", "Interactive citations"],
              "Port 5173", "#38bdf8", border_color='#38bdf8')

    draw_card(4.0, 1.0, 2.8, 2.9, "Node.js API Gateway", "Express + PostgreSQL",
              ["JWT Authentication", "Bcrypt security & RBAC", "Multer PDF text parse", "Audit history logging", "FastAPI Proxying"],
              "Port 3000", "#eab308", border_color='#eab308')

    draw_card(7.4, 1.0, 3.4, 2.9, "FastAPI RAG Core", "Python Uvicorn Engine",
              ["Query vector generation", "Top-k pgvector retrieval", "Grounded prompt assembly", "Anti-hallucination rules", "Pydantic schema validation"],
              "Port 8000", "#06b6d4", border_color='#06b6d4')

    draw_card(11.4, 1.0, 3.7, 2.9, "Groq / Llama 3.3", "70B Versatile LLM",
              ["Context-only synthesis", "5-tier compliance status", "evidence_found breakdown", "evidence_missing analysis", "Page-level verifiable proof"],
              "Zero Hallucination", "#ec4899", border_color='#ec4899')

    # Pipeline 2 Arrows
    draw_arrow((3.5, 2.45), (3.95, 2.45), "REST / JSON")
    draw_arrow((6.9, 2.45), (7.35, 2.45), "Auth / Proxy")
    draw_arrow((10.9, 2.45), (11.35, 2.45), "Context + Evidence")

    # Cross-pipeline connection: FastAPI <-> Supabase PostgreSQL
    ax.annotate('', xy=(12.8, 5.35), xytext=(9.2, 3.95),
                arrowprops=dict(arrowstyle="<|-|>", color='#10b981', lw=2.2, linestyle='dashed', mutation_scale=15))
    ax.text(10.6, 4.7, "pgvector Cosine Search (<=>)", ha='center', va='center', fontsize=8.0, 
            color='#6ee7b7', fontweight='bold', fontfamily='sans-serif',
            bbox=dict(boxstyle="round,pad=0.2", facecolor='#0f172a', edgecolor='#10b981', alpha=0.9))

    plt.tight_layout()
    plt.savefig('D:/Regulatory Complance/docs/images/architecture.png', dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("architecture.png created successfully!")


def create_database_er_diagram():
    fig, ax = plt.subplots(figsize=(16, 11), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 11)
    ax.axis('off')
    
    fig.patch.set_facecolor('#0f172a')
    ax.set_facecolor('#0f172a')
    
    # Title
    ax.text(8.0, 10.45, "Food Regulatory Compliance Intelligence System — Relational & Vector Schema", 
            ha='center', va='center', fontsize=17, fontweight='bold', color='#f8fafc', fontfamily='sans-serif')
    ax.text(8.0, 10.15, "PostgreSQL 15+ with pgvector Extension (Supabase Hosted) • 5 Core Entities", 
            ha='center', va='center', fontsize=10.5, color='#94a3b8', fontfamily='sans-serif')

    def draw_table(x, y, w, title, rows, badge, header_color='#1e3a8a'):
        row_height = 0.28
        total_h = 0.6 + len(rows) * row_height
        
        # Outer card
        card = FancyBboxPatch((x, y - total_h), w, total_h, boxstyle="round,pad=0.1,rounding_size=0.15",
                              facecolor='#1e293b', edgecolor='#475569', linewidth=1.3)
        ax.add_patch(card)
        
        # Header box
        header = FancyBboxPatch((x, y - 0.55), w, 0.55, boxstyle="round,pad=0.08,rounding_size=0.15",
                                facecolor=header_color, edgecolor='none')
        ax.add_patch(header)
        ax.text(x + 0.2, y - 0.28, title, fontsize=10.5, fontweight='bold', color='#ffffff', fontfamily='sans-serif')
        
        # Badge
        if badge:
            blen = len(badge) * 0.11 + 0.2
            b_patch = FancyBboxPatch((x + w - blen - 0.15, y - 0.42), blen, 0.26,
                                     boxstyle="round,pad=0.04,rounding_size=0.08",
                                     facecolor='#0f172a', edgecolor='#94a3b8', linewidth=0.8)
            ax.add_patch(b_patch)
            ax.text(x + w - 0.15 - blen/2, y - 0.29, badge,
                    ha='center', va='center', fontsize=7.5, fontweight='bold', color='#38bdf8', fontfamily='sans-serif')
        
        # Rows
        curr_y = y - 0.8
        for col_name, col_type, key_type in rows:
            # Key badge
            if key_type == 'PK':
                ax.text(x + 0.2, curr_y, 'PK', fontsize=7.5, fontweight='bold', color='#eab308', fontfamily='sans-serif')
            elif key_type == 'FK':
                ax.text(x + 0.2, curr_y, 'FK', fontsize=7.5, fontweight='bold', color='#38bdf8', fontfamily='sans-serif')
            elif key_type == 'UQ':
                ax.text(x + 0.2, curr_y, 'UQ', fontsize=7.5, fontweight='bold', color='#c084fc', fontfamily='sans-serif')
            elif key_type == 'VEC':
                ax.text(x + 0.2, curr_y, 'VEC', fontsize=7.0, fontweight='bold', color='#4ade80', fontfamily='sans-serif')
            else:
                ax.text(x + 0.2, curr_y, '  ', fontsize=7.5, color='#64748b')
            
            # Column name
            ax.text(x + 0.65, curr_y, col_name, fontsize=8.0, fontweight='medium', color='#f1f5f9', fontfamily='sans-serif')
            # Column type
            ax.text(x + w - 0.2, curr_y, col_type, ha='right', fontsize=7.5, color='#94a3b8', fontfamily='monospace')
            curr_y -= row_height

    # 1. users table
    users_rows = [
        ('id', 'UUID', 'PK'),
        ('name', 'TEXT', ''),
        ('email', 'TEXT', 'UQ'),
        ('password_hash', 'TEXT', ''),
        ('role', 'TEXT (user/admin)', ''),
        ('created_at', 'TIMESTAMPTZ', ''),
        ('updated_at', 'TIMESTAMPTZ', '')
    ]
    draw_table(0.8, 9.4, 3.8, "users", users_rows, "Auth & RBAC", header_color='#1d4ed8')

    # 2. company_policy_docs table
    docs_policy_rows = [
        ('id', 'UUID', 'PK'),
        ('user_id', 'UUID', 'FK'),
        ('filename', 'TEXT', ''),
        ('extracted_text', 'TEXT', ''),
        ('char_count', 'INTEGER', ''),
        ('created_at', 'TIMESTAMPTZ', '')
    ]
    draw_table(0.8, 5.8, 3.8, "company_policy_docs", docs_policy_rows, "User Uploads", header_color='#0284c7')

    # 3. audit_history table
    audit_rows = [
        ('id', 'UUID', 'PK'),
        ('user_id', 'UUID', 'FK'),
        ('question', 'TEXT', ''),
        ('compliance_area', 'TEXT', ''),
        ('company_evidence', 'TEXT', ''),
        ('facility_description', 'TEXT', ''),
        ('overall_status', 'TEXT', ''),
        ('summary', 'TEXT', ''),
        ('findings', 'JSONB', ''),
        ('disclaimer', 'TEXT', ''),
        ('created_at', 'TIMESTAMPTZ', '')
    ]
    draw_table(5.6, 9.4, 4.4, "audit_history", audit_rows, "Compliance Logs", header_color='#0f766e')

    # 4. documents table
    documents_rows = [
        ('id', 'UUID', 'PK'),
        ('filename', 'TEXT', 'UQ'),
        ('title', 'TEXT', ''),
        ('source_url', 'TEXT', ''),
        ('publication_date', 'TEXT', ''),
        ('version_info', 'TEXT', ''),
        ('page_count', 'INTEGER', ''),
        ('file_hash', 'TEXT', ''),
        ('metadata', 'JSONB', ''),
        ('ingested_at', 'TIMESTAMPTZ', ''),
        ('updated_at', 'TIMESTAMPTZ', '')
    ]
    draw_table(11.0, 9.4, 4.2, "documents", documents_rows, "FSSAI Compendiums", header_color='#6d28d9')

    # 5. document_chunks table
    chunks_rows = [
        ('id', 'UUID', 'PK'),
        ('document_id', 'UUID', 'FK'),
        ('chunk_index', 'INTEGER', ''),
        ('content', 'TEXT', ''),
        ('embedding', 'vector(384)', 'VEC'),
        ('page_start', 'INTEGER', ''),
        ('page_end', 'INTEGER', ''),
        ('section_title', 'TEXT', ''),
        ('metadata', 'JSONB', ''),
        ('content_hash', 'TEXT', ''),
        ('created_at', 'TIMESTAMPTZ', '')
    ]
    draw_table(11.0, 5.1, 4.2, "document_chunks", chunks_rows, "pgvector Embeddings", header_color='#059669')

    # Relationship Arrows
    def draw_rel(start, end, label):
        ax.annotate('', xy=end, xytext=start,
                    arrowprops=dict(arrowstyle="-|>", color='#38bdf8', lw=1.8, linestyle='solid', mutation_scale=12))
        mx, my = (start[0] + end[0])/2, (start[1] + end[1])/2
        ax.text(mx, my, label, ha='center', va='center', fontsize=7.5, color='#e2e8f0',
                bbox=dict(boxstyle="round,pad=0.15", facecolor='#1e293b', edgecolor='#475569', alpha=0.9))

    # users -> audit_history (1 to N)
    draw_rel((4.6, 8.2), (5.58, 8.2), "1 : N")

    # users -> company_policy_docs (1 to N)
    draw_rel((2.7, 6.7), (2.7, 5.82), "1 : N")

    # documents -> document_chunks (1 to N)
    draw_rel((13.1, 5.4), (13.1, 5.12), "1 : N (CASCADE)")

    # Explanatory footer notes
    note_box = FancyBboxPatch((0.8, 0.4), 14.4, 1.4, boxstyle="round,pad=0.15,rounding_size=0.15",
                              facecolor='#1e293b', edgecolor='#334155', linewidth=1.2)
    ax.add_patch(note_box)
    ax.text(1.1, 1.5, "SCHEMA DESIGN & VECTOR SEARCH SPECIFICATIONS", fontsize=9.5, fontweight='bold', color='#38bdf8')
    ax.text(1.1, 1.15, "• FastEmbed Dense Vectors: document_chunks.embedding vector(384) indexed via IVFFlat (lists=100) for fast cosine search.", fontsize=8.0, color='#cbd5e1')
    ax.text(1.1, 0.85, "• Idempotency & Deduplication: Unique constraint uq_document_chunk (document_id, content_hash) prevents re-indexing identical text.", fontsize=8.0, color='#cbd5e1')
    ax.text(1.1, 0.55, "• Grounded Citations: page_start, page_end, and section_title are stored alongside content for exact FSSAI legal traceability.", fontsize=8.0, color='#cbd5e1')

    plt.tight_layout()
    plt.savefig('D:/Regulatory Complance/docs/images/database_er_diagram.png', dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("database_er_diagram.png created successfully!")


def create_ui_preview():
    # Generate high-res visual mockups representing the live UI screens
    fig, ax = plt.subplots(figsize=(16, 9.5), dpi=300)
    ax.set_xlim(0, 16)
    ax.set_ylim(0, 9.5)
    ax.axis('off')
    
    fig.patch.set_facecolor('#090d16')
    ax.set_facecolor('#090d16')
    
    # Title
    ax.text(8.0, 9.15, "Food Regulatory Compliance Portal — Live Dashboard & Audit Report", 
            ha='center', va='center', fontsize=17, fontweight='bold', color='#f8fafc', fontfamily='sans-serif')
    ax.text(8.0, 8.8, "Modern React 19 UI with Real-Time Assessment, Metric KPI Cards, and Grounded FSSAI Citations", 
            ha='center', va='center', fontsize=10.5, color='#94a3b8', fontfamily='sans-serif')

    # Top Metric KPI Cards
    def draw_kpi(x, y, w, h, title, val, sub, color):
        kpi = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.1,rounding_size=0.15",
                             facecolor='#131b2e', edgecolor='#1e293b', linewidth=1.2)
        ax.add_patch(kpi)
        ax.text(x + 0.3, y + h - 0.35, title, fontsize=8.5, color='#94a3b8', fontweight='bold', fontfamily='sans-serif')
        ax.text(x + 0.3, y + h - 0.85, val, fontsize=16, color=color, fontweight='bold', fontfamily='sans-serif')
        ax.text(x + 0.3, y + 0.25, sub, fontsize=7.5, color='#64748b', fontfamily='sans-serif')

    draw_kpi(0.8, 7.3, 3.3, 1.25, "TOTAL AUDITS RUN", "142", "Across 4 FSSAI domains", "#38bdf8")
    draw_kpi(4.5, 7.3, 3.3, 1.25, "OVERALL COMPLIANCE", "84.6%", "+3.2% from last cycle", "#4ade80")
    draw_kpi(8.2, 7.3, 3.3, 1.25, "AVG ASSESSMENT TIME", "1.18s", "pgvector cosine search", "#c084fc")
    draw_kpi(11.9, 7.3, 3.3, 1.25, "REGULATIONS INDEXED", "5 Compendiums", "3,840 semantic chunks", "#fbbf24")

    # Left Panel: Live Compliance Check Form
    left_panel = FancyBboxPatch((0.8, 0.5), 6.8, 6.5, boxstyle="round,pad=0.15,rounding_size=0.2",
                                facecolor='#111827', edgecolor='#1f2937', linewidth=1.3)
    ax.add_patch(left_panel)
    ax.text(1.2, 6.6, "1. Automated Audit Inquiry Input", fontsize=11, fontweight='bold', color='#38bdf8')
    
    # Form input mockups
    def draw_input(x, y, w, h, label, text):
        ax.text(x, y + h + 0.08, label, fontsize=8.0, fontweight='bold', color='#cbd5e1')
        box = FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.08,rounding_size=0.1",
                             facecolor='#1f2937', edgecolor='#374151', linewidth=1.0)
        ax.add_patch(box)
        ax.text(x + 0.15, y + h/2, text, va='center', fontsize=7.5, color='#e5e7eb', fontfamily='sans-serif')

    draw_input(1.2, 5.65, 6.0, 0.45, "Compliance Domain", "Food Labelling & Display Regulations 2022")
    draw_input(1.2, 4.65, 6.0, 0.45, "Regulatory Question", "What are mandatory labelling requirements for packaged foods?")
    
    # Evidence text area
    ax.text(1.2, 4.15, "Company Evidence / Packaging Text", fontsize=8.0, fontweight='bold', color='#cbd5e1')
    ev_box = FancyBboxPatch((1.2, 1.6), 6.0, 2.3, boxstyle="round,pad=0.1,rounding_size=0.1",
                            facecolor='#1f2937', edgecolor='#374151', linewidth=1.0)
    ax.add_patch(ev_box)
    sample_text = [
        "Product Name: NutriCrunch Baked Granola Snack",
        "Ingredients: Rolled oats, honey, almond flakes, dried cranberries, salt.",
        "Net Weight: 250 g | FSSAI Lic. No.: 10018021003456",
        "Mfg Date: 12-Oct-2026 | Expiry: 11-Apr-2027",
        "Storage: Store in a cool, dry place away from sunlight.",
        "Allergen Declaration: Contains Tree Nuts (Almonds)."
    ]
    ey = 3.6
    for line in sample_text:
        ax.text(1.35, ey, line, fontsize=7.2, color='#94a3b8', fontfamily='monospace')
        ey -= 0.35

    # Run Audit Button
    btn = FancyBboxPatch((1.2, 0.8), 6.0, 0.55, boxstyle="round,pad=0.08,rounding_size=0.1",
                         facecolor='#0284c7', edgecolor='none')
    ax.add_patch(btn)
    ax.text(4.2, 1.07, "⚡ Execute AI Compliance Check", ha='center', va='center', 
            fontsize=9.0, fontweight='bold', color='#ffffff')

    # Right Panel: Structured Audit Results & Citations
    right_panel = FancyBboxPatch((8.2, 0.5), 7.0, 6.5, boxstyle="round,pad=0.15,rounding_size=0.2",
                                 facecolor='#111827', edgecolor='#1f2937', linewidth=1.3)
    ax.add_patch(right_panel)
    ax.text(8.6, 6.6, "2. Grounded Findings & Page Citations", fontsize=11, fontweight='bold', color='#4ade80')

    # Status Banner
    status_banner = FancyBboxPatch((8.6, 5.7), 6.2, 0.65, boxstyle="round,pad=0.08,rounding_size=0.1",
                                   facecolor='#14532d', edgecolor='#22c55e', linewidth=1.2)
    ax.add_patch(status_banner)
    ax.text(8.85, 6.02, "STATUS: PARTIALLY COMPLIANT", fontsize=9.5, fontweight='bold', color='#4ade80')
    ax.text(14.5, 6.02, "Confidence: 98.4%", ha='right', fontsize=8.0, color='#86efac')

    # Findings Cards
    def draw_finding_card(y, req, status, stat_color, found, missing):
        card = FancyBboxPatch((8.6, y), 6.2, 1.6, boxstyle="round,pad=0.08,rounding_size=0.1",
                              facecolor='#1e293b', edgecolor='#334155', linewidth=1.0)
        ax.add_patch(card)
        ax.text(8.8, y + 1.35, req, fontsize=8.0, fontweight='bold', color='#f1f5f9')
        ax.text(14.5, y + 1.35, status, ha='right', fontsize=7.5, fontweight='bold', color=stat_color)
        
        ax.text(8.8, y + 0.95, f"✓ Found: {found}", fontsize=7.2, color='#4ade80')
        ax.text(8.8, y + 0.55, f"✗ Missing: {missing}", fontsize=7.2, color='#f87171')
        ax.text(8.8, y + 0.2, "→ Action: Add nutritional info panel (per 100g) and veg logo", fontsize=7.0, color='#cbd5e1')

    draw_finding_card(3.85, "Clause 5(1): Mandatory Declarations", "PARTIALLY COMPLIANT", "#fbbf24",
                      "Name, Net Qty, Dates, FSSAI Lic, Allergen", "Nutritional facts panel, Veg/Non-Veg icon")
    
    draw_finding_card(2.05, "Clause 6(2): Allergen Labelling", "COMPLIANT", "#4ade80",
                      "Mandatory declaration 'Contains Tree Nuts (Almonds)' present", "None")

    # Sources & Page Citations box
    src_box = FancyBboxPatch((8.6, 0.7), 6.2, 1.15, boxstyle="round,pad=0.08,rounding_size=0.1",
                             facecolor='#1e1b4b', edgecolor='#6366f1', linewidth=1.0)
    ax.add_patch(src_box)
    ax.text(8.8, 1.55, "Verified FSSAI Citations (Retrieved from Supabase pgvector):", fontsize=7.5, fontweight='bold', color='#a5b4fc')
    ax.text(8.8, 1.25, "• Compendium_Labelling_Display_17_10_2022.pdf (Pages 12-14, Sec 5.1)", fontsize=7.0, color='#e0e7ff')
    ax.text(8.8, 0.95, "• Compendium_Food_Additives_Regulations_26_03_2021.pdf (Pages 45-47, Sec 3.2)", fontsize=7.0, color='#e0e7ff')

    plt.tight_layout()
    plt.savefig('D:/Regulatory Complance/docs/images/dashboard_preview.png', dpi=300, facecolor=fig.get_facecolor(), edgecolor='none')
    plt.close()
    print("dashboard_preview.png created successfully!")

if __name__ == '__main__':
    create_architecture_diagram()
    create_database_er_diagram()
    create_ui_preview()
