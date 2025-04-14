# Script to test the report generation API
param(
    [string]$BackendUrl = "http://localhost:8000",
    [string]$ReportType = "investor_update",
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"

# Output banner
Write-Host "===== Report Generation API Test =====" -ForegroundColor Cyan
Write-Host "Backend URL: $BackendUrl" -ForegroundColor Cyan
Write-Host "Report Type: $ReportType" -ForegroundColor Cyan
Write-Host "====================================" -ForegroundColor Cyan

# Step 1: Check if backend is running
Write-Host "`nStep 1: Checking if backend is running..." -ForegroundColor Green
try {
    $healthResponse = Invoke-RestMethod -Uri "$BackendUrl/api/v1/health" -Method Get -TimeoutSec 5
    Write-Host "✅ Success! Backend is running." -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Backend is not running at $BackendUrl" -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    Write-Host "Try starting the backend with 'scripts\start-backend.ps1'" -ForegroundColor Yellow
    exit 1
}

# Step 2: Check Ollama status via diagnostics endpoint
Write-Host "`nStep 2: Checking Ollama connection via diagnostics..." -ForegroundColor Green
try {
    $diagnosticsUrl = "$BackendUrl/api/v1/diagnostics/ollama/status"
    $diagResponse = Invoke-RestMethod -Uri $diagnosticsUrl -Method Get -TimeoutSec 10
    
    if ($Verbose) {
        Write-Host "Response: $($diagResponse | ConvertTo-Json -Depth 3)" -ForegroundColor Gray
    }
    
    if ($diagResponse.available) {
        Write-Host "✅ Success! Backend can connect to Ollama at $($diagResponse.url)" -ForegroundColor Green
        Write-Host "Available models: $($diagResponse.models -join ', ')" -ForegroundColor Green
        
        if ($diagResponse.simple_test.success) {
            Write-Host "✅ Simple test passed: '$($diagResponse.simple_test.response)'" -ForegroundColor Green
            Write-Host "Response time: $($diagResponse.simple_test.time_ms)ms" -ForegroundColor Green
        } else {
            Write-Host "❌ Simple test failed: $($diagResponse.simple_test.error)" -ForegroundColor Red
            Write-Host "Continuing anyway, but report generation might fail." -ForegroundColor Yellow
        }
    } else {
        Write-Host "❌ Error: Backend cannot connect to Ollama" -ForegroundColor Red
        Write-Host "Error details: $($diagResponse.error)" -ForegroundColor Red
        Write-Host "Continuing anyway, but report generation will likely fail." -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error: Cannot access diagnostics endpoint" -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    Write-Host "Continuing anyway, but diagnostics should be fixed." -ForegroundColor Yellow
}

# Step 3: Test report generation with minimal data
Write-Host "`nStep 3: Testing report generation..." -ForegroundColor Green

$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$reportRequest = @{
    reportType = $ReportType
    prompt = "Test report $timestamp"
    status = "draft"
    startDate = (Get-Date).AddDays(-7).ToString("yyyy-MM-dd")
    endDate = (Get-Date).ToString("yyyy-MM-dd")
    dataSources = @("gmail", "notion", "google_calendar")
}

$body = $reportRequest | ConvertTo-Json
Write-Host "Sending report request: " -ForegroundColor Cyan
Write-Host "$body" -ForegroundColor Gray

try {
    $startTime = Get-Date
    $reportResponse = Invoke-RestMethod -Uri "$BackendUrl/api/v1/reports/generate" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 180
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalSeconds
    
    if ($Verbose) {
        Write-Host "Full Response: $($reportResponse | ConvertTo-Json -Depth 5)" -ForegroundColor Gray
    }
    
    Write-Host "✅ Success! Report generated in $($duration.ToString("0.00")) seconds" -ForegroundColor Green
    if ($reportResponse.status -eq "completed") {
        Write-Host "Report Status: COMPLETED" -ForegroundColor Green
        Write-Host "Report ID: $($reportResponse.id)" -ForegroundColor Green
        Write-Host "Report Preview (first 200 chars):" -ForegroundColor Green
        Write-Host ($reportResponse.content.Substring(0, [Math]::Min(200, $reportResponse.content.Length)) + "...") -ForegroundColor White
    } elseif ($reportResponse.status -eq "in_progress") {
        Write-Host "Report Status: IN PROGRESS (Some reports are generated asynchronously)" -ForegroundColor Yellow
        Write-Host "Report ID: $($reportResponse.id)" -ForegroundColor Yellow
        Write-Host "Check report status with the /api/v1/reports/{id} endpoint" -ForegroundColor Yellow
    } else {
        Write-Host "Report Status: $($reportResponse.status)" -ForegroundColor Yellow
        Write-Host "Report ID: $($reportResponse.id)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "❌ Error: Failed to generate report" -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    
    # Try to extract more information from the error
    try {
        if ($_.Exception.Response) {
            $reader = New-Object System.IO.StreamReader($_.Exception.Response.GetResponseStream())
            $responseBody = $reader.ReadToEnd()
            $reader.Close()
            Write-Host "Response body:" -ForegroundColor Red
            Write-Host $responseBody -ForegroundColor Red
        }
    } catch {
        Write-Host "Could not extract response body." -ForegroundColor Red
    }
    
    exit 1
}

# Summary
Write-Host "`n===== Summary =====" -ForegroundColor Cyan
Write-Host "Backend is running: ✅" -ForegroundColor Green
Write-Host "Report generation API was tested: ✅" -ForegroundColor Green
Write-Host "`nIf the report generation was successful but the application still shows 'Generating Report...'," -ForegroundColor Cyan
Write-Host "the issue might be with the frontend not correctly handling the response or polling." -ForegroundColor Cyan
Write-Host "=================`n" -ForegroundColor Cyan 