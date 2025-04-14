# Script to restart the EverRaise backend reliably
param(
    [int]$Port = 8000
)

$Host.UI.RawUI.WindowTitle = "EverRaise Backend Server"
Write-Host "Restarting EverRaise Backend Server on port $Port..." -ForegroundColor Cyan

# Kill any existing Python processes to ensure clean restart
try {
    # Get any python processes running uvicorn
    $processes = Get-Process -Name python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like "*uvicorn*" }
    
    if ($processes) {
        Write-Host "Found running Python/uvicorn processes. Stopping them..." -ForegroundColor Yellow
        foreach ($process in $processes) {
            Write-Host "Stopping process with PID $($process.Id)..." -ForegroundColor Yellow
            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
        }
    } else {
        Write-Host "No running Python/uvicorn processes found." -ForegroundColor Green
    }
    
    # Also try to kill any processes using the specified port
    $connections = Get-NetTCPConnection -LocalPort $Port -ErrorAction SilentlyContinue
    if ($connections) {
        Write-Host "Found processes using port $Port. Stopping them..." -ForegroundColor Yellow
        foreach ($conn in $connections) {
            $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
            if ($process) {
                Write-Host "Stopping $($process.ProcessName) (PID: $($process.Id))..." -ForegroundColor Yellow
                Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue
            }
        }
    }
} catch {
    Write-Host "Error stopping processes: $_" -ForegroundColor Red
}

# Navigate to the backend directory
$BackendDir = Join-Path $PSScriptRoot "backend"
Write-Host "Changing to directory: $BackendDir" -ForegroundColor Cyan
Set-Location $BackendDir

# Wait a moment to ensure ports are freed up
Start-Sleep -Seconds 2

# Start the backend server
Write-Host "Starting backend server on port $Port..." -ForegroundColor Green
python -m uvicorn app.main:app --host 0.0.0.0 --port $Port --reload

# This line will only be reached if the above command exits
Write-Host "Server has stopped." -ForegroundColor Red 