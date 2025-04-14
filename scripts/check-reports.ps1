# Script to check and diagnose report generation issues
param (
    [string]$BackendUrl = "http://localhost:8000",
    [switch]$Verbose
)

# Import common functions if available
$ScriptsDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$CommonFunctions = Join-Path $ScriptsDir "common-functions.ps1"
if (Test-Path $CommonFunctions) {
    . $CommonFunctions
}

Write-Host "EverRaise Report Diagnostics Tool" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan
Write-Host

# Function to show verbose output
function Write-VerboseOutput {
    param([string]$Message)
    
    if ($Verbose) {
        Write-Host $Message -ForegroundColor Gray
    }
}

# Test connection to the backend
Write-Host "Testing backend connectivity..." -ForegroundColor Yellow
try {
    $healthEndpoint = "$BackendUrl/api/health"
    Write-VerboseOutput "Checking health endpoint: $healthEndpoint"
    
    $healthResponse = Invoke-RestMethod -Uri $healthEndpoint -Method Get -ErrorAction Stop
    
    if ($healthResponse.status -eq "healthy") {
        Write-Host "✓ Backend is running and healthy" -ForegroundColor Green
        
        # Check Ollama status
        Write-Host "`nChecking Ollama LLM service status..." -ForegroundColor Yellow
        try {
            $ollamaEndpoint = "$BackendUrl/api/v1/diagnostics/ollama/status"
            Write-VerboseOutput "Checking Ollama endpoint: $ollamaEndpoint"
            
            $ollamaStatus = Invoke-RestMethod -Uri $ollamaEndpoint -Method Get -ErrorAction Stop
            
            if ($ollamaStatus.available) {
                Write-Host "✓ Ollama LLM service is available" -ForegroundColor Green
                Write-Host "  - Status: $($ollamaStatus.status)" -ForegroundColor White
                Write-Host "  - URL: $($ollamaStatus.url)" -ForegroundColor White
                Write-Host "  - Models: $($ollamaStatus.models -join ', ')" -ForegroundColor White
                Write-Host "  - Default model: $($ollamaStatus.default_model)" -ForegroundColor White
                
                # Check if default model is available
                if ($ollamaStatus.default_model_available) {
                    Write-Host "✓ Default model is available" -ForegroundColor Green
                } else {
                    Write-Host "✗ Default model is not available!" -ForegroundColor Red
                    Write-Host "  - Please run 'ollama pull $($ollamaStatus.default_model)'" -ForegroundColor Yellow
                }
                
                # Check simple test result
                if ($ollamaStatus.simple_test -and $ollamaStatus.simple_test.success) {
                    Write-Host "✓ Simple generation test successful" -ForegroundColor Green
                } else {
                    Write-Host "✗ Simple generation test failed!" -ForegroundColor Red
                    Write-Host "  - Error: $($ollamaStatus.simple_test.error)" -ForegroundColor Yellow
                }
            } else {
                Write-Host "✗ Ollama LLM service is not available!" -ForegroundColor Red
                Write-Host "  - Status: $($ollamaStatus.status)" -ForegroundColor Yellow
                Write-Host "  - Message: $($ollamaStatus.message)" -ForegroundColor Yellow
                Write-Host "`nPossible reasons:" -ForegroundColor Yellow
                Write-Host "1. Ollama is not running (run 'ollama serve' in a separate terminal)" -ForegroundColor White
                Write-Host "2. Ollama is running on a different URL than $($ollamaStatus.url)" -ForegroundColor White
                Write-Host "3. The models aren't pulled (run 'ollama pull llama2')" -ForegroundColor White
            }
        } catch {
            Write-Host "✗ Error checking Ollama status: $_" -ForegroundColor Red
            Write-Host "`nPossible reasons:" -ForegroundColor Yellow
            Write-Host "1. The diagnostics endpoint is not available (backend version might be outdated)" -ForegroundColor White
            Write-Host "2. The backend can't connect to Ollama" -ForegroundColor White
        }
        
        # Check report generation status
        Write-Host "`nChecking recent reports..." -ForegroundColor Yellow
        try {
            $reportsEndpoint = "$BackendUrl/api/v1/reports/list"
            Write-VerboseOutput "Checking reports endpoint: $reportsEndpoint"
            
            $reports = Invoke-RestMethod -Uri $reportsEndpoint -Method Get -ErrorAction Stop
            
            if ($reports -and $reports.Count -gt 0) {
                Write-Host "✓ Found $($reports.Count) reports" -ForegroundColor Green
                
                # Get report statuses
                $completedReports = $reports | Where-Object { $_.status -eq "completed" }
                $pendingReports = $reports | Where-Object { $_.status -eq "pending" }
                $failedReports = $reports | Where-Object { $_.status -eq "failed" }
                $generatingReports = $reports | Where-Object { $_.status -eq "generating" }
                
                Write-Host "Report status breakdown:" -ForegroundColor White
                Write-Host "  - Completed: $($completedReports.Count)" -ForegroundColor $(if ($completedReports.Count -gt 0) { "Green" } else { "White" })
                Write-Host "  - Pending: $($pendingReports.Count)" -ForegroundColor $(if ($pendingReports.Count -gt 0) { "Yellow" } else { "White" })
                Write-Host "  - Generating: $($generatingReports.Count)" -ForegroundColor $(if ($generatingReports.Count -gt 0) { "Yellow" } else { "White" })
                Write-Host "  - Failed: $($failedReports.Count)" -ForegroundColor $(if ($failedReports.Count -gt 0) { "Red" } else { "White" })
                
                # Check for stuck reports
                $stuckReports = $generatingReports | Where-Object { 
                    [DateTime]::Parse($_.created_at) -lt (Get-Date).AddMinutes(-30)
                }
                
                if ($stuckReports -and $stuckReports.Count -gt 0) {
                    Write-Host "`n✗ Found $($stuckReports.Count) potentially stuck reports (generating for >30 minutes)" -ForegroundColor Red
                    $stuckReports | ForEach-Object {
                        Write-Host "  - $($_.title) (ID: $($_.id), Created: $($_.created_at))" -ForegroundColor Yellow
                    }
                }
                
                # Show recent failures
                if ($failedReports -and $failedReports.Count -gt 0) {
                    Write-Host "`nRecent failed reports:" -ForegroundColor Yellow
                    $failedReports | Sort-Object -Property created_at -Descending | Select-Object -First 3 | ForEach-Object {
                        Write-Host "  - $($_.title) (ID: $($_.id), Created: $($_.created_at))" -ForegroundColor Red
                        if ($_.error_message) {
                            Write-Host "    Error: $($_.error_message)" -ForegroundColor Gray
                        }
                    }
                }
            } else {
                Write-Host "! No reports found in the system" -ForegroundColor Yellow
                Write-Host "  Try generating a report from the frontend and then run this script again" -ForegroundColor White
            }
            
            # Provide next steps
            Write-Host "`nNext Steps:" -ForegroundColor Yellow
            Write-Host "1. Check the backend logs for more detailed error messages" -ForegroundColor White
            Write-Host "2. Ensure the LLM service (Ollama) is running and accessible" -ForegroundColor White
            Write-Host "3. Try generating a new report to see if the issue persists" -ForegroundColor White
            Write-Host "4. Check if the frontend is loading the report list from the correct API endpoint" -ForegroundColor White
            
        } catch {
            Write-Host "✗ Error retrieving report diagnostics: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "✗ Backend returned unexpected status code: $($healthResponse.StatusCode)" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Backend is not accessible: $_" -ForegroundColor Red
    Write-Host "Make sure the backend is running on $BackendUrl" -ForegroundColor Yellow
} 