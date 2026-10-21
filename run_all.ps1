# Food Regulatory Intelligence Co-pilot — Start All Services

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host " Starting Food Regulatory Intelligence Co-pilot... " -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

$root = $PSScriptRoot

# 1. FastAPI
Write-Host "`n[1/3] Starting Python FastAPI on port 8000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\food-compliance-rag'; .\.venv\Scripts\Activate.ps1; uvicorn app.main:app --host 0.0.0.0 --port 8000"

Start-Sleep -Seconds 3

# 2. Node.js
Write-Host "[2/3] Starting Node.js API Gateway on port 3000..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\node-backend'; npm start"

Start-Sleep -Seconds 3

# 3. Streamlit
Write-Host "[3/3] Starting Web User Interface on port 8501..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root'; & 'food-compliance-rag\.venv\Scripts\python.exe' -m streamlit run 'food-compliance-rag\app\ui.py' --server.port 8501"

Write-Host "`n===================================================" -ForegroundColor Green
Write-Host " All services launched!" -ForegroundColor Green
Write-Host " Open your browser at: http://localhost:8501" -ForegroundColor White
Write-Host "===================================================" -ForegroundColor Green
