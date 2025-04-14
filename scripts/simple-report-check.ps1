# Simple script to check EverRaise reports cache
$backendUrl = "http://localhost:8000"

Write-Host "Checking backend report cache status..."
try {
    $response = Invoke-WebRequest -Uri "$backendUrl/api/v1/reports/diagnostic/cache" -Method GET -TimeoutSec 10
    $data = $response.Content | ConvertFrom-Json
    
    Write-Host "Report Cache Status:"
    Write-Host "--------------------"
    Write-Host "Total reports in cache: $($data.cache_size)"
    Write-Host "Listable reports: $($data.listable_count)"
    
    if ($data.reports.Count -gt 0) {
        Write-Host "Report IDs: $($data.reports.id -join ', ')"
        
        foreach ($report in $data.reports) {
            Write-Host "`nReport: $($report.id)"
            Write-Host "  Status: $($report.status)"
            Write-Host "  Has result: $($report.has_result)"
            if ($report.has_title) {
                Write-Host "  Title: $($report.title)"
            }
        }
    } else {
        Write-Host "No reports found in cache"
    }
} catch {
    Write-Host "Error checking report cache: $_"
} 