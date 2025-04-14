# Script to clean up stray Node.js processes and free up ports
param(
    [switch]$Force = $false
)

$ErrorActionPreference = "Continue"

# Colors for output
$GREEN = [ConsoleColor]::Green
$RED = [ConsoleColor]::Red
$YELLOW = [ConsoleColor]::Yellow
$CYAN = [ConsoleColor]::Cyan

Write-Host "`n===== Frontend Process Cleanup =====" -ForegroundColor $CYAN
Write-Host "This script will help clean up stray Node.js processes that might be blocking ports." -ForegroundColor $CYAN
Write-Host "====================================" -ForegroundColor $CYAN

# Find Node.js processes
Write-Host "`nLooking for Node.js processes..." -ForegroundColor $CYAN
$nodeProcesses = Get-Process | Where-Object { $_.ProcessName -like "*node*" }

if ($nodeProcesses.Count -eq 0) {
    Write-Host "No Node.js processes found." -ForegroundColor $GREEN
    exit 0
}

# Display found processes
Write-Host "`nFound $($nodeProcesses.Count) Node.js processes:" -ForegroundColor $YELLOW
$nodeProcesses | Format-Table -Property Id, ProcessName, CPU, WorkingSet, Path -AutoSize

if (-not $Force) {
    $confirmation = Read-Host "Do you want to terminate all these processes? (y/n)"
    if ($confirmation -ne 'y') {
        Write-Host "Operation cancelled." -ForegroundColor $YELLOW
        exit 0
    }
}

# Kill the processes
Write-Host "`nTerminating Node.js processes..." -ForegroundColor $CYAN
$successCount = 0
$failCount = 0

foreach ($process in $nodeProcesses) {
    try {
        $process | Stop-Process -Force -ErrorAction Stop
        Write-Host "[SUCCESS] Successfully terminated process with ID $($process.Id)" -ForegroundColor $GREEN
        $successCount++
    } catch {
        Write-Host "[ERROR] Failed to terminate process with ID $($process.Id): $_" -ForegroundColor $RED
        $failCount++
    }
}

# Summary
Write-Host "`n===== Cleanup Summary =====" -ForegroundColor $CYAN
Write-Host "Successfully terminated: $successCount processes" -ForegroundColor $GREEN
if ($failCount -gt 0) {
    Write-Host "Failed to terminate: $failCount processes" -ForegroundColor $RED
}

# Check if ports are still in use
Write-Host "`nChecking common frontend ports..." -ForegroundColor $CYAN
$commonPorts = @(3000, 5173, 5174, 5175, 5176, 5177, 5178, 5179, 5180)
$inUsePorts = @()

foreach ($port in $commonPorts) {
    try {
        $connections = Get-NetTCPConnection -LocalPort $port -ErrorAction SilentlyContinue
        if ($connections) {
            $inUsePorts += $port
            Write-Host "[WARNING] Port $port is still in use by process ID $($connections[0].OwningProcess)" -ForegroundColor $YELLOW
        } else {
            Write-Host "[OK] Port $port is available" -ForegroundColor $GREEN
        }
    } catch {
        Write-Host "Error checking port $port: $_" -ForegroundColor $RED
    }
}

if ($inUsePorts.Count -gt 0) {
    Write-Host "`n[WARNING] Some ports are still in use. You may need to restart your computer to free them up." -ForegroundColor $YELLOW
} else {
    Write-Host "`n[OK] All common frontend ports are now available!" -ForegroundColor $GREEN
}

Write-Host "`nNext steps:" -ForegroundColor $CYAN
Write-Host "1. Start the backend with: .\scripts\start-backend.ps1" -ForegroundColor $CYAN
Write-Host "2. Start the frontend with: .\scripts\start-frontend.ps1" -ForegroundColor $CYAN
Write-Host "3. Use .\scripts\check-connection.ps1 to verify connectivity" -ForegroundColor $CYAN
Write-Host "=================`n" -ForegroundColor $CYAN 