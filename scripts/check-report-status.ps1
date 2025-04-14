# Script to check the status of a report
param(
    [Parameter(Mandatory=$true)]
    [int]$ReportId,
    [string]$BackendUrl = "http://localhost:8000",
    [switch]$WaitForCompletion = $false,
    [int]$MaxWaitTime = 300 # 5 minutes
)

$ErrorActionPreference = "Stop"

# Output banner
Write-Host "===== Report Status Check =====" -ForegroundColor Cyan
Write-Host "Report ID: $ReportId" -ForegroundColor Cyan
Write-Host "Backend URL: $BackendUrl" -ForegroundColor Cyan
if ($WaitForCompletion) {
    Write-Host "Waiting for completion: Yes (max $MaxWaitTime seconds)" -ForegroundColor Cyan
} else {
    Write-Host "Waiting for completion: No" -ForegroundColor Cyan
}
Write-Host "===========================" -ForegroundColor Cyan

# Check report status
function Get-ReportStatus {
    param (
        [int]$Id
    )

    try {
        $response = Invoke-RestMethod -Uri "$BackendUrl/api/v1/reports/$Id" -Method Get -TimeoutSec 10
        return $response
    } catch {
        Write-Host "❌ Error: Could not retrieve report status" -ForegroundColor Red
        Write-Host "Error details: $_" -ForegroundColor Red
        return $null
    }
}

function Display-ReportStatus {
    param (
        [object]$Report
    )

    Write-Host "Report Status: " -NoNewline
    switch ($Report.status) {
        "draft" { Write-Host "DRAFT" -ForegroundColor Gray }
        "pending" { Write-Host "PENDING" -ForegroundColor Yellow }
        "generating" { Write-Host "GENERATING" -ForegroundColor Blue }
        "completed" { Write-Host "COMPLETED" -ForegroundColor Green }
        "failed" { Write-Host "FAILED" -ForegroundColor Red }
        "published" { Write-Host "PUBLISHED" -ForegroundColor Cyan }
        default { Write-Host $Report.status -ForegroundColor Gray }
    }

    Write-Host "Title: $($Report.title)" -ForegroundColor White
    Write-Host "Report Type: $($Report.report_type)" -ForegroundColor White
    Write-Host "Created: $($Report.created_at)" -ForegroundColor White
    
    if ($Report.status -eq "completed" -or $Report.status -eq "published") {
        Write-Host "Generation Time: $($Report.generation_time)s" -ForegroundColor White
        Write-Host "AI Model: $($Report.ai_model_used)" -ForegroundColor White
        
        if ($Report.content) {
            $contentPreview = $Report.content.Substring(0, [Math]::Min(200, $Report.content.Length))
            Write-Host "Content Preview: " -ForegroundColor White
            Write-Host "$contentPreview..." -ForegroundColor Gray
        } else {
            Write-Host "No content available" -ForegroundColor Yellow
        }
    } elseif ($Report.status -eq "failed") {
        Write-Host "Error Message: $($Report.error_message)" -ForegroundColor Red
    }
}

# Get initial report status
$report = Get-ReportStatus -Id $ReportId
if ($null -eq $report) {
    exit 1
}

Display-ReportStatus -Report $report

# If waiting for completion is enabled
if ($WaitForCompletion -and $report.status -ne "completed" -and $report.status -ne "published" -and $report.status -ne "failed") {
    Write-Host "`nWaiting for report completion..." -ForegroundColor Yellow
    
    $startTime = Get-Date
    $completed = $false
    $spinner = @('|', '/', '-', '\')
    $spinnerIndex = 0
    
    while (-not $completed -and ((Get-Date) - $startTime).TotalSeconds -lt $MaxWaitTime) {
        # Show a spinner
        Write-Host "`r$($spinner[$spinnerIndex]) Checking status..." -NoNewline -ForegroundColor Yellow
        $spinnerIndex = ($spinnerIndex + 1) % $spinner.Length
        
        # Wait a bit before checking again
        Start-Sleep -Seconds 3
        
        # Get updated status
        $report = Get-ReportStatus -Id $ReportId
        if ($null -eq $report) {
            continue
        }
        
        if ($report.status -eq "completed" -or $report.status -eq "published" -or $report.status -eq "failed") {
            $completed = $true
        }
    }
    
    # Clear the spinner line
    Write-Host "`r                      " -NoNewline
    
    if ($completed) {
        Write-Host "`nReport processing completed!" -ForegroundColor Green
        Display-ReportStatus -Report $report
    } else {
        Write-Host "`nTimeout waiting for report completion." -ForegroundColor Yellow
        Write-Host "Last known status:" -ForegroundColor Yellow
        Display-ReportStatus -Report $report
    }
}

# Summary
Write-Host "`n===== Summary =====" -ForegroundColor Cyan
Write-Host "Report ID: $ReportId" -ForegroundColor Cyan
Write-Host "Current Status: $($report.status.ToUpper())" -ForegroundColor Cyan
Write-Host "=================`n" -ForegroundColor Cyan 