@echo off
echo ===================================================
echo  Food Regulatory Intelligence Co-pilot
echo ===================================================
echo.

echo [1/3] Starting Python FastAPI Backend on port 8000...
start "FastAPI RAG Engine (Port 8000)" cmd /k "cd /d "%~dp0food-compliance-rag" && .\.venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/3] Starting Node.js API Gateway on port 3000...
start "Node.js API Gateway (Port 3000)" cmd /k "cd /d "%~dp0node-backend" && npm start"

timeout /t 3 /nobreak >nul

echo [3/3] Starting Web User Interface on port 8501...
start "Streamlit Web UI (Port 8501)" cmd /k "cd /d "%~dp0" && food-compliance-rag\.venv\Scripts\python.exe -m streamlit run food-compliance-rag\app\ui.py --server.port 8501"

echo.
echo ===================================================
echo  All 3 services have started!
echo  Open in your browser: http://localhost:8501
echo ===================================================
echo.
pause
