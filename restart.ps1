# PowerShell script to restart EverRaise frontend and backend

Write-Host "Restarting EverRaise servers..." -ForegroundColor Green

# Check if the running processes are already running
$frontendProcess = Get-Process -Name "npm" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "frontend" }
$backendProcess = Get-Process -Name "python" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -match "uvicorn" }

# Stop processes if they exist
if ($frontendProcess) {
    Write-Host "Stopping frontend server..." -ForegroundColor Yellow
    Stop-Process -Id $frontendProcess.Id -Force
}

if ($backendProcess) {
    Write-Host "Stopping backend server..." -ForegroundColor Yellow
    Stop-Process -Id $backendProcess.Id -Force
}

# Give some time for processes to fully stop
Start-Sleep -Seconds 2

# Start the servers in separate windows
Write-Host "Starting backend server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd backend; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"

Write-Host "Starting frontend server..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd frontend; npm run dev"

Write-Host "Servers restarted. Don't forget to create an admin user with:" -ForegroundColor Green
Write-Host "cd backend; .\create_admin.ps1" -ForegroundColor Yellow
Write-Host ""
Write-Host "Login Credentials:" -ForegroundColor Cyan
Write-Host "Email: admin@example.com" -ForegroundColor White
Write-Host "Password: adminpassword" -ForegroundColor White 