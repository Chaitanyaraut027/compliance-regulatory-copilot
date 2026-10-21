# Food Regulatory Intelligence Co-pilot — Start All Services with React UI

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

# 3. React Frontend
Write-Host "[3/3] Starting React Web UI on port 5173..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$root\frontend'; npm run dev"

Write-Host "`n===================================================" -ForegroundColor Green
Write-Host " All services launched!" -ForegroundColor Green
Write-Host " Open your browser at: http://localhost:5173" -ForegroundColor White
Write-Host "===================================================" -ForegroundColor Green
