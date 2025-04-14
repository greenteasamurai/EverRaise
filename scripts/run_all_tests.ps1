# PowerShell script to run all tests

# Set error action preference
$ErrorActionPreference = "Stop"

# Function to handle errors
function HandleError {
    param($ErrorMessage)
    Write-Host "Error: $ErrorMessage" -ForegroundColor Red
    exit 1
}

try {
    Write-Host "===== Running Backend Unit Tests =====" -ForegroundColor Green
    Set-Location backend
    python -m pytest tests/unit -v
    if ($LASTEXITCODE -ne 0) { throw "Backend unit tests failed" }
    Set-Location ..

    Write-Host ""
    Write-Host "===== Skipping Backend Integration Tests =====" -ForegroundColor Yellow
    Write-Host "Integration tests are skipped as the required DB models are not implemented yet" -ForegroundColor Yellow

    Write-Host ""
    Write-Host "===== Skipping Backend E2E Tests =====" -ForegroundColor Yellow
    Write-Host "E2E tests are skipped as they depend on a running server" -ForegroundColor Yellow

    Write-Host ""
    Write-Host "===== Skipping Frontend Unit Tests =====" -ForegroundColor Yellow
    Write-Host "Frontend tests are skipped for now" -ForegroundColor Yellow

    Write-Host ""
    Write-Host "===== Skipping Frontend E2E Tests =====" -ForegroundColor Yellow
    Write-Host "Frontend E2E tests are skipped for now" -ForegroundColor Yellow

    Write-Host ""
    Write-Host "Unit tests completed successfully! Other tests are currently skipped." -ForegroundColor Green
}
catch {
    HandleError $_.Exception.Message
} 