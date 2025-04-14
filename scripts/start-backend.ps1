# Script to start the EverRaise backend
param(
    [int]$Port = 8000,
    [switch]$Debug = $false
)

# Get the root directory of the project (parent of the scripts directory)
$RootDir = Split-Path -Parent $PSScriptRoot

# Set path to the backend directory
$BackendDir = Join-Path $RootDir "backend"

Write-Host "Starting EverRaise Backend..." -ForegroundColor Cyan
Write-Host "Backend directory: $BackendDir" -ForegroundColor Gray
Write-Host "Backend will be available at: http://localhost:$Port" -ForegroundColor Cyan

# Change to the backend directory
Push-Location $BackendDir

# Check if any existing process is using the port
try {
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($connections) {
        Write-Host "Port $Port is in use. Attempting to forcefully terminate processes..." -ForegroundColor Yellow
        
        foreach ($conn in $connections) {
            $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Forcefully terminating $($process.ProcessName) (PID: $($process.Id))..." -ForegroundColor Yellow
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            }
        }
    }
} catch {
    $errorMessage = $_.Exception.Message
    Write-Host "Error checking port $Port`: $errorMessage" -ForegroundColor Red
}

# Start the backend server
if ($Debug) {
    Write-Host "Starting in DEBUG mode..." -ForegroundColor Yellow
    python -m uvicorn app.main:app --host 0.0.0.0 --port $Port --log-level debug
} else {
    Write-Host "Starting in NORMAL mode..." -ForegroundColor Green
    python -m uvicorn app.main:app --host 0.0.0.0 --port $Port
}

# Pop location back to the original directory
Pop-Location 