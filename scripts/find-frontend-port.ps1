# Script to find which port the Vite frontend is running on
param(
    [string]$BaseUrl = "http://localhost"
)

$ErrorActionPreference = "Continue"

# Colors for output
$GREEN = [ConsoleColor]::Green
$RED = [ConsoleColor]::Red
$YELLOW = [ConsoleColor]::Yellow
$CYAN = [ConsoleColor]::Cyan

function Test-Port {
    param (
        [string]$BaseUrl,
        [int]$Port
    )

    $url = "$BaseUrl`:$Port"
    try {
        $response = Invoke-WebRequest -Uri $url -Method HEAD -TimeoutSec 2 -ErrorAction Stop
        # Check if it contains any Vite-specific headers or content
        if ($response.StatusCode -eq 200) {
            Write-Host "Found active port at $url" -ForegroundColor $GREEN
            return $true
        }
        return $false
    }
    catch {
        return $false
    }
}

Write-Host "`n===== EverRaise Frontend Port Finder =====" -ForegroundColor $CYAN
Write-Host "This script will identify which port the frontend is running on." -ForegroundColor $CYAN
Write-Host "=============================================" -ForegroundColor $CYAN

Write-Host "`nSearching for Vite frontend server..." -ForegroundColor $CYAN

# Check for Node.js processes to see if frontend is running
$nodeProcesses = Get-Process | Where-Object { $_.ProcessName -like "*node*" }
if ($nodeProcesses.Count -eq 0) {
    Write-Host "`n[WARNING] No Node.js processes found. Frontend might not be running!" -ForegroundColor $YELLOW
    Write-Host "Run the following command to start the frontend:" -ForegroundColor $CYAN
    Write-Host ".\scripts\start-frontend.ps1" -ForegroundColor $CYAN
    exit 0
}

# Common Vite ports to check
$commonPorts = @(3000, 5173, 5174, 5175, 5176, 5177, 5178, 5179, 5180, 5181, 5182, 5183, 5184, 5185)
$foundPort = $false

Write-Host "`nChecking common Vite ports..." -ForegroundColor $CYAN

foreach ($port in $commonPorts) {
    Write-Host "Checking $BaseUrl`:$port... " -NoNewline
    
    if (Test-Port -BaseUrl $BaseUrl -Port $port) {
        Write-Host "[SUCCESS] Frontend found running on port $port!" -ForegroundColor $GREEN
        $foundPort = $true
        
        # Verify it's the EverRaise frontend
        try {
            $indexResponse = Invoke-WebRequest -Uri "$BaseUrl`:$port" -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($indexResponse.Content -match "EverRaise" -or $indexResponse.Content -match "Echo") {
                Write-Host "[CONFIRMED] This appears to be the EverRaise frontend" -ForegroundColor $GREEN
            } else {
                Write-Host "[WARNING] This port is active but might not be the EverRaise frontend" -ForegroundColor $YELLOW
            }
        } catch {
            Write-Host "[WARNING] Could not verify if this is the EverRaise frontend" -ForegroundColor $YELLOW
        }
        
        break
    } else {
        Write-Host "[NOT FOUND]" -ForegroundColor $RED
    }
}

if (-not $foundPort) {
    Write-Host "`n[WARNING] Could not find the frontend on any common port." -ForegroundColor $YELLOW
    
    # Check for TCP connections from Node.js processes
    Write-Host "`nChecking for TCP connections from Node.js processes:" -ForegroundColor $CYAN
    
    foreach ($process in $nodeProcesses) {
        $connections = Get-NetTCPConnection -OwningProcess $process.Id -State Listen -ErrorAction SilentlyContinue
        
        if ($connections) {
            foreach ($conn in $connections) {
                if ($conn.LocalAddress -eq "0.0.0.0" -or $conn.LocalAddress -eq "127.0.0.1" -or $conn.LocalAddress -eq "::") {
                    Write-Host "[FOUND] Node.js process (ID: $($process.Id)) is listening on port $($conn.LocalPort)" -ForegroundColor $GREEN
                    Write-Host "Try connecting to http://localhost:$($conn.LocalPort)" -ForegroundColor $CYAN
                }
            }
        }
    }
}

Write-Host "`n===== Recommendations =====" -ForegroundColor $CYAN
Write-Host "1. When running the connection check script, specify the correct port:" -ForegroundColor $CYAN
Write-Host "   .\scripts\check-connection.ps1 -FrontendUrl 'http://localhost:PORT'" -ForegroundColor $CYAN
Write-Host "2. If you're still having issues, clean up stray processes:" -ForegroundColor $CYAN
Write-Host "   .\scripts\cleanup-frontend.ps1" -ForegroundColor $CYAN
Write-Host "3. Then restart both backend and frontend:" -ForegroundColor $CYAN
Write-Host "   .\scripts\start-backend.ps1" -ForegroundColor $CYAN
Write-Host "   .\scripts\start-frontend.ps1" -ForegroundColor $CYAN
Write-Host "=========================" -ForegroundColor $CYAN 