# Script to start the EverRaise frontend
param(
    [switch]$Production = $false
)

# Get the root directory of the project (parent of the scripts directory)
$RootDir = Split-Path -Parent $PSScriptRoot

# Set path to the frontend directory
$FrontendDir = Join-Path $RootDir "frontend"

Write-Host "Starting EverRaise Frontend..." -ForegroundColor Cyan
Write-Host "Frontend directory: $FrontendDir" -ForegroundColor Gray

# Check if the frontend directory exists
if (-not (Test-Path $FrontendDir)) {
    Write-Host "Frontend directory not found at $FrontendDir" -ForegroundColor Red
    exit 1
}

# Change to the frontend directory
Push-Location $FrontendDir

# Start the frontend server
if ($Production) {
    Write-Host "Starting in PRODUCTION mode..." -ForegroundColor Yellow
    npm run build
    npm run start
} else {
    Write-Host "Starting in DEVELOPMENT mode..." -ForegroundColor Green
    npm run dev
}

# Pop location back to the original directory
Pop-Location 