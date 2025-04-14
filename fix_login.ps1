Write-Host "Starting login fix script" -ForegroundColor Green

# First, let's stop any running processes
$frontendProcesses = Get-Process -Name "npm" -ErrorAction SilentlyContinue
$backendProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue

if ($frontendProcesses) {
    Write-Host "Stopping frontend processes..." -ForegroundColor Yellow
    $frontendProcesses | Stop-Process -Force
}

if ($backendProcesses) {
    Write-Host "Stopping backend processes..." -ForegroundColor Yellow
    $backendProcesses | Stop-Process -Force
}

# Small delay to ensure processes are stopped
Start-Sleep -Seconds 2

# Install httpx for diagnostics endpoint if needed
Write-Host "Installing required Python packages..." -ForegroundColor Blue
Set-Location -Path ".\backend"
py -m pip install httpx
py -m pip install aiosqlite
Set-Location -Path ".."

# Fix database issues
Write-Host "Running database fix script..." -ForegroundColor Cyan
if (Test-Path ".\fix_database.ps1") {
    & .\fix_database.ps1
} else {
    Write-Host "Database fix script not found! Please run it separately." -ForegroundColor Red
    
    # Fallback - Create admin user directly
    Write-Host "Creating admin user..." -ForegroundColor Blue
    Set-Location -Path ".\backend"
    if (Test-Path "create_admin.ps1") {
        & .\create_admin.ps1
    } else {
        python create_admin.py
    }
    Set-Location -Path ".."
}

# Start backend server
Write-Host "Starting backend server..." -ForegroundColor Green
$backendWindow = Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "cd backend; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -PassThru

# Start frontend server
Write-Host "Starting frontend server..." -ForegroundColor Green
$frontendWindow = Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "cd frontend; npm run dev" -PassThru

# Wait a moment for servers to start
Start-Sleep -Seconds 5

# Open the login page
Write-Host "Opening login page..." -ForegroundColor Cyan
Start-Process "http://localhost:5173/login"

Write-Host "Fix script complete!" -ForegroundColor Green
Write-Host "Use these credentials to log in:" -ForegroundColor Green
Write-Host "Email: admin@example.com" -ForegroundColor Yellow
Write-Host "Password: adminpassword" -ForegroundColor Yellow
Write-Host "To stop the servers, close the terminal windows or press Ctrl+C in each one." -ForegroundColor Magenta 