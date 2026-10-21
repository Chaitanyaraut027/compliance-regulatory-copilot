@echo off
echo ===================================================
echo  Food Regulatory Intelligence Co-pilot (React UI)
echo ===================================================
echo.

echo [1/3] Starting Python FastAPI Backend on port 8000...
start "FastAPI RAG Engine (Port 8000)" cmd /k "cd /d "%~dp0food-compliance-rag" && .\.venv\Scripts\activate && uvicorn app.main:app --host 0.0.0.0 --port 8000"

timeout /t 3 /nobreak >nul

echo [2/3] Starting Node.js API Gateway on port 3000...
start "Node.js API Gateway (Port 3000)" cmd /k "cd /d "%~dp0node-backend" && npm start"

timeout /t 3 /nobreak >nul

echo [3/3] Starting React Frontend on port 5173...
start "React Frontend (Port 5173)" cmd /k "cd /d "%~dp0frontend" && npm run dev"

echo.
echo ===================================================
echo  All 3 services have started!
echo  Open React UI in your browser: http://localhost:5173
echo ===================================================
echo.
pause
