# Food Regulatory Intelligence Co-pilot — React Frontend

A modern, high-performance React application replacing the previous Streamlit prototype (`food-compliance-rag/app/ui.py`) with 100% feature parity, responsive UI, enterprise design, and fluid transitions.

---

## 🛠️ Technology Stack

1. **Framework & Language:**
   - **React 19** with **TypeScript**
   - **Vite** build tool and development server

2. **Styling & Theming:**
   - **Tailwind CSS v4**
   - Dark Mode & Light Mode support with smooth theme toggle and persistence in `localStorage`
   - Custom status badges and cards with official regulatory coloring

3. **Icons & UI Elements:**
   - **Lucide React** (`lucide-react`) for icons (shield, upload, check, alert, chevron, moon, sun, etc.)

4. **Networking & State:**
   - **Axios** with request interceptors for automatic JWT Bearer token management
   - React Context API for global state (`AuthContext`, `ThemeContext`)
   - Multipart `FormData` handling for file uploads (PDF / TXT)

---

## 🚀 Features

- **Authentication:**
  - Login & Registration views with input validation
  - Demo credentials one-click display: `test@example.com` / `password123`
  - JWT token storage in `localStorage` and automatic header injection
  - User session display and logout

- **Dashboard:**
  - Welcome greeting with user's name
  - Quick action callout to evaluate documents
  - Recent compliance checks list fetched from Node.js API Gateway (`/api/audit?limit=5`)
  - Status badges, dates, area badges, and summary snippets
  - Direct "View Report" navigation

- **Document Upload & AI Assessment:**
  - Drag-and-drop or file picker for **PDF** or **TXT** files
  - Client-side 5 MB file size validation
  - Product / Document name auto-detection from filename
  - Primary Regulatory Compliance Area dropdown selector:
    - *General Labelling & Display*
    - *Food Additives*
    - *Contaminants & Residues*
    - *Licensing & Registration*
    - *Hygiene & Sanitary Practices*
  - Optional facility location description
  - 4-stage animated progress feedback:
    1. Uploading document to Node.js backend (`/api/upload/policy`)
    2. Extracting readable text and searching regulatory compendiums
    3. Running AI compliance analysis (`/api/compliance/check`)
    4. Rendering interactive report

- **Interactive Compliance Report View:**
  - Header card with overall status badge (Compliant, Needs Attention, Insufficient Information)
  - Executive summary and legal disclaimer banner
  - 4 summary metrics cards:
    - Total Requirements Evaluated
    - Requirements Satisfied
    - Needs Attention
    - Insufficient Information
  - 4 Categorized breakdown tabs:
    - ⚠️ Needs Attention ({count})
    - ✅ Satisfied Requirements ({count})
    - ℹ️ Insufficient Information ({count})
    - All Findings ({count})
  - Collapsible finding cards showing:
    - Detailed explanation
    - Evidence found in document (✅)
    - Missing information / evidence required (⚠️)
    - Suggested corrective actions (💡)
    - Supporting regulatory compendium references (page numbers, section titles)

- **Audit Reports History:**
  - Searchable list of all previous assessments (`/api/audit?limit=50`)
  - Direct report viewer for each history item

- **Search Regulations:**
  - Semantic similarity search against regulatory compendiums (`/api/compliance/search`)
  - Adjustable results slider (1 to 10 matching clauses)
  - Expandable passages showing similarity score, document name, page numbers, and section

---

## 🏃 Running the React Frontend

### Prerequisites
Make sure the **Python FastAPI** service (port 8000) and **Node.js Gateway** (port 3000) are running.

### Development Mode
```bash
cd frontend
npm install
npm run dev
```
Access at: **http://localhost:5173**

### Production Build
```bash
cd frontend
npm run build
npm run preview
```

### Start All Services Together
Run the root script:
```cmd
run_react.bat
```
or in PowerShell:
```powershell
.\run_react.ps1
```
