# Script to check the status of reports in the EverRaise backend
# Usage: .\scripts\report-diagnostic.ps1

# Configuration
$backendUrl = "http://localhost:8000"
$apiEndpoint = "/api/v1/reports/diagnostic/cache"

Write-Host "EverRaise Report Cache Diagnostic Tool" -ForegroundColor Cyan
Write-Host "=======================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking backend at $backendUrl..." -ForegroundColor Yellow

try {
    # Check if the backend is running
    $healthResponse = Invoke-WebRequest -Uri "$backendUrl/api/v1/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    
    if ($healthResponse.StatusCode -eq 200) {
        Write-Host "✓ Backend is online" -ForegroundColor Green
        
        try {
            # Request report cache diagnostic data
            $diagnosticResponse = Invoke-WebRequest -Uri "$backendUrl$apiEndpoint" -Method GET -TimeoutSec 10 -ErrorAction Stop
            $diagnosticData = $diagnosticResponse.Content | ConvertFrom-Json
            
            Write-Host ""
            Write-Host "Report Cache Diagnostic Results:" -ForegroundColor Cyan
            Write-Host "--------------------------------" -ForegroundColor Cyan
            
            # Display cache overview
            Write-Host "Cache size: $($diagnosticData.cache_size) reports" -ForegroundColor White
            Write-Host "Listable reports: $($diagnosticData.listable_count)" -ForegroundColor White
            
            # Display status counts
            Write-Host ""
            Write-Host "Report Status Counts:" -ForegroundColor Yellow
            $diagnosticData.status_counts.PSObject.Properties | ForEach-Object {
                $color = "White"
                if ($_.Name -eq "complete") { $color = "Green" }
                if ($_.Name -eq "error") { $color = "Red" }
                if ($_.Name -eq "processing") { $color = "Yellow" }
                
                Write-Host "  $($_.Name): $($_.Value)" -ForegroundColor $color
            }
            
            # Display individual reports if there are any
            if ($diagnosticData.reports.Count -gt 0) {
                Write-Host ""
                Write-Host "Individual Report Details:" -ForegroundColor Yellow
                
                foreach ($report in $diagnosticData.reports) {
                    $statusColor = "White"
                    if ($report.status -eq "complete") { $statusColor = "Green" }
                    if ($report.status -eq "error") { $statusColor = "Red" }
                    if ($report.status -eq "processing") { $statusColor = "Yellow" }
                    
                    Write-Host ""
                    Write-Host "Report ID: $($report.id)" -ForegroundColor Cyan
                    Write-Host "  Status: $($report.status)" -ForegroundColor $statusColor
                    Write-Host "  Progress: $($report.progress * 100)%" -ForegroundColor White
                    Write-Host "  Has result: $($report.has_result)" -ForegroundColor White
                    
                    if ($report.has_result) {
                        Write-Host "  Result type: $($report.result_type)" -ForegroundColor White
                        
                        if ($report.has_title) {
                            Write-Host "  Title: $($report.title)" -ForegroundColor White
                        } else {
                            Write-Host "  Title: Missing!" -ForegroundColor Red
                        }
                        
                        if ($report.has_report_type) {
                            Write-Host "  Report type: $($report.report_type)" -ForegroundColor White
                        } else {
                            Write-Host "  Report type: Missing!" -ForegroundColor Red
                        }
                        
                        if ($report.has_status) {
                            Write-Host "  Result status: $($report.result_status)" -ForegroundColor White
                        }
                        
                        if ($report.has_content) {
                            Write-Host "  Content: $($report.content_type) with $($report.content_size) items" -ForegroundColor White
                            if ($report.content_keys) {
                                Write-Host "  Content sections: $($report.content_keys -join ', ')" -ForegroundColor White
                            }
                        } else {
                            Write-Host "  Content: Missing!" -ForegroundColor Red
                        }
                        
                        if ($report.has_summary) {
                            Write-Host "  Has summary: Yes" -ForegroundColor White
                        } else {
                            Write-Host "  Has summary: No" -ForegroundColor Red
                        }
                        
                        if ($report.has_data_sources) {
                            Write-Host "  Has data sources: Yes" -ForegroundColor White
                        } else {
                            Write-Host "  Has data sources: No" -ForegroundColor Red
                        }
                        
                        Write-Host "  Listable: $($report.listable)" -ForegroundColor $(if ($report.listable) { "Green" } else { "Red" })
                    }
                    
                    if ($report.error) {
                        Write-Host "  Error: $($report.error)" -ForegroundColor Red
                    }
                }
            } else {
                Write-Host ""
                Write-Host "No reports found in cache" -ForegroundColor Yellow
            }
            
            # Add troubleshooting tips
            Write-Host ""
            Write-Host "Troubleshooting Tips:" -ForegroundColor Cyan
            Write-Host "--------------------" -ForegroundColor Cyan
            
            if ($diagnosticData.cache_size -eq 0) {
                Write-Host "✗ No reports in cache. Try generating a new report." -ForegroundColor Red
            } elseif ($diagnosticData.listable_count -eq 0) {
                Write-Host "✗ There are reports in the cache, but none are listable. Check for missing attributes." -ForegroundColor Red
            } else {
                Write-Host "✓ There are $($diagnosticData.listable_count) listable reports in the cache." -ForegroundColor Green
                
                # Check for common issues
                $incompleteReports = @($diagnosticData.reports | Where-Object { $_.status -eq "processing" })
                if ($incompleteReports.Count -gt 0) {
                    Write-Host "! There are $($incompleteReports.Count) reports still processing." -ForegroundColor Yellow
                }
                
                $errorReports = @($diagnosticData.reports | Where-Object { $_.status -eq "error" })
                if ($errorReports.Count -gt 0) {
                    Write-Host "✗ There are $($errorReports.Count) reports with errors." -ForegroundColor Red
                }
            }
            
            Write-Host ""
            Write-Host "Next Steps:" -ForegroundColor Yellow
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
    Write-Host "Make sure the backend is running on $backendUrl" -ForegroundColor Yellow
} 