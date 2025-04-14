# Master script to start the entire EverRaise application
param(
    [switch]$CleanStart = $false,
    [switch]$SkipBackend = $false,
    [switch]$SkipFrontend = $false
)

$ErrorActionPreference = "Continue"

# Colors for output
$GREEN = [ConsoleColor]::Green
$RED = [ConsoleColor]::Red
$YELLOW = [ConsoleColor]::Yellow
$CYAN = [ConsoleColor]::Cyan

# Banner
Write-Host "`n================================================================" -ForegroundColor $CYAN
Write-Host "               EverRaise Application Launcher                    " -ForegroundColor $CYAN
Write-Host "================================================================" -ForegroundColor $CYAN

# Check if we're in the correct directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$rootDir = Split-Path -Parent $scriptDir

if (!(Test-Path "$rootDir\frontend") -or !(Test-Path "$rootDir\backend")) {
    Write-Host "`n[ERROR] This script must be run from the EverRaise project root directory!" -ForegroundColor $RED
    Write-Host "Current directory: $PWD" -ForegroundColor $RED
    Write-Host "Please change to the project root directory and try again.`n" -ForegroundColor $RED
    exit 1
}

# Clean start if requested
if ($CleanStart) {
    Write-Host "`n[INFO] Clean start requested. Stopping existing processes..." -ForegroundColor $CYAN
    
    # Stop existing processes
    $nodeProcesses = Get-Process | Where-Object { $_.ProcessName -like "*node*" } -ErrorAction SilentlyContinue
    $pythonProcesses = Get-Process | Where-Object { $_.ProcessName -like "*python*" } -ErrorAction SilentlyContinue
    
    foreach ($process in $nodeProcesses) {
        try {
            $process | Stop-Process -Force -ErrorAction SilentlyContinue
            Write-Host "[SUCCESS] Terminated Node.js process (ID: $($process.Id))" -ForegroundColor $GREEN
        } catch {
            Write-Host "[WARNING] Failed to terminate Node.js process (ID: $($process.Id))" -ForegroundColor $YELLOW
        }
    }
    
    foreach ($process in $pythonProcesses) {
        try {
            $process | Stop-Process -Force -ErrorAction SilentlyContinue
            Write-Host "[SUCCESS] Terminated Python process (ID: $($process.Id))" -ForegroundColor $GREEN
        } catch {
            Write-Host "[WARNING] Failed to terminate Python process (ID: $($process.Id))" -ForegroundColor $YELLOW
        }
    }
    
    # Wait a moment for processes to completely terminate
    Start-Sleep -Seconds 2
}

# Start backend if not skipped
if (!$SkipBackend) {
    Write-Host "`n[INFO] Starting backend service..." -ForegroundColor $CYAN
    
    # Start the backend in a new window
    Start-Process powershell.exe -ArgumentList "-NoExit -Command `"& '$rootDir\scripts\start-backend.ps1'`"" -WindowStyle Normal
    
    # Wait for backend to initialize
    Write-Host "[INFO] Waiting for backend to initialize..." -ForegroundColor $CYAN
    Start-Sleep -Seconds 5
    
    # Check if backend is running
    try {
        $backendResponse = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -TimeoutSec 5 -ErrorAction Stop
        if ($backendResponse.StatusCode -eq 200) {
            Write-Host "[SUCCESS] Backend is running successfully!" -ForegroundColor $GREEN
        } else {
            Write-Host "[WARNING] Backend responded with status code $($backendResponse.StatusCode)" -ForegroundColor $YELLOW
        }
    } catch {
        Write-Host "[ERROR] Failed to connect to backend: $_" -ForegroundColor $RED
        Write-Host "[INFO] Backend might still be starting up..." -ForegroundColor $CYAN
    }
} else {
    Write-Host "`n[INFO] Skipping backend startup (as requested)" -ForegroundColor $CYAN
}

# Start frontend if not skipped
if (!$SkipFrontend) {
    Write-Host "`n[INFO] Starting frontend service..." -ForegroundColor $CYAN
    
    # Start the frontend in a new window
    Start-Process powershell.exe -ArgumentList "-NoExit -Command `"& '$rootDir\scripts\start-frontend.ps1'`"" -WindowStyle Normal
    
    # Wait for frontend to initialize
    Write-Host "[INFO] Waiting for frontend to initialize..." -ForegroundColor $CYAN
    Start-Sleep -Seconds 10
    
    # Run the frontend port finder script
    Write-Host "`n[INFO] Checking which port the frontend is running on..." -ForegroundColor $CYAN
    & "$rootDir\scripts\find-frontend-port.ps1"
} else {
    Write-Host "`n[INFO] Skipping frontend startup (as requested)" -ForegroundColor $CYAN
}

# Final instructions
Write-Host "`n================================================================" -ForegroundColor $CYAN
Write-Host "                EverRaise Startup Complete                      " -ForegroundColor $CYAN
Write-Host "================================================================" -ForegroundColor $CYAN
Write-Host "Backend URL: http://localhost:8000" -ForegroundColor $CYAN
Write-Host "Frontend URL: http://localhost:3000 (or check output above for actual port)" -ForegroundColor $CYAN
Write-Host "`nHelpful commands:" -ForegroundColor $CYAN
Write-Host "- Check connection: .\scripts\check-connection.ps1" -ForegroundColor $CYAN
Write-Host "- Find frontend port: .\scripts\find-frontend-port.ps1" -ForegroundColor $CYAN
Write-Host "- Clean up processes: .\scripts\cleanup-frontend.ps1" -ForegroundColor $CYAN
Write-Host "================================================================`n" -ForegroundColor $CYAN 