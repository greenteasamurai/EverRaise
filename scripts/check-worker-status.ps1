# Script to check and manage the status of report generation workers
param(
    [string]$BackendUrl = "http://localhost:8000",
    [switch]$Restart = $false,
    [switch]$ForceRestart = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"

# Output banner
Write-Host "===== Report Worker Status Check =====" -ForegroundColor Cyan
Write-Host "Backend URL: $BackendUrl" -ForegroundColor Cyan
Write-Host "Restart if needed: $Restart" -ForegroundColor Cyan
Write-Host "Force restart: $ForceRestart" -ForegroundColor Cyan
Write-Host "===================================" -ForegroundColor Cyan

function Check-ProcessRunning {
    param (
        [string]$ProcessName,
        [string]$CommandLineContains
    )
    
    $processes = Get-Process -Name $ProcessName -ErrorAction SilentlyContinue | 
                Where-Object { $_.CommandLine -match $CommandLineContains }
    
    return ($processes -ne $null -and $processes.Count -gt 0)
}

function Get-QueueStatus {
    try {
        $response = Invoke-RestMethod -Uri "$BackendUrl/api/v1/diagnostics/queue/status" -Method Get -TimeoutSec 10
        return $response
    } catch {
        Write-Host "❌ Error accessing queue status endpoint: $_" -ForegroundColor Red
        return $null
    }
}

# Check if Redis is running
$redisRunning = Check-ProcessRunning -ProcessName "redis-server" -CommandLineContains "redis"
if ($redisRunning) {
    Write-Host "✅ Redis server is running" -ForegroundColor Green
} else {
    Write-Host "❌ Redis server is not running" -ForegroundColor Red
}

# Check if RQ Worker is running
$workerRunning = Check-ProcessRunning -ProcessName "python" -CommandLineContains "rq worker"
if ($workerRunning) {
    Write-Host "✅ RQ Worker process is running" -ForegroundColor Green
} else {
    Write-Host "❌ RQ Worker process is not running" -ForegroundColor Red
}

# Check queue status from API
Write-Host "`nChecking queue status from API..." -ForegroundColor Yellow
$queueStatus = Get-QueueStatus
if ($queueStatus -ne $null) {
    Write-Host "Queue diagnostic data retrieved successfully" -ForegroundColor Green
    
    if ($Verbose) {
        Write-Host "Queue details:" -ForegroundColor Cyan
        Write-Host ($queueStatus | ConvertTo-Json -Depth 3) -ForegroundColor Gray
    }
    
    # Display queue status
    if ($queueStatus.redis_connected) {
        Write-Host "✅ Backend can connect to Redis" -ForegroundColor Green
        Write-Host "Queue name: $($queueStatus.queue_stats.name)" -ForegroundColor White
        Write-Host "Jobs in queue: $($queueStatus.queue_stats.count)" -ForegroundColor White
        Write-Host "Failed jobs: $($queueStatus.queue_stats.failed_job_count)" -ForegroundColor White
        Write-Host "Scheduled jobs: $($queueStatus.queue_stats.scheduled_job_count)" -ForegroundColor White
        
        if ($queueStatus.queue_stats.failed_job_count -gt 0) {
            Write-Host "`nRecent failed jobs:" -ForegroundColor Yellow
            foreach ($job in $queueStatus.queue_stats.recent_failed_jobs) {
                Write-Host "  Job ID: $($job.id)" -ForegroundColor White
                Write-Host "  Created at: $($job.created_at)" -ForegroundColor White
                if ($Verbose) {
                    Write-Host "  Error: $($job.exc_info)" -ForegroundColor Gray
                }
                Write-Host ""
            }
        }
    } else {
        Write-Host "❌ Backend cannot connect to Redis: $($queueStatus.redis_error)" -ForegroundColor Red
    }
} else {
    Write-Host "Failed to get queue status from API" -ForegroundColor Red
}

# Determine if we need to restart the worker
$needRestart = $false
if ($ForceRestart) {
    $needRestart = $true
    Write-Host "`nForce restart requested" -ForegroundColor Yellow
} elseif (!$workerRunning) {
    $needRestart = $true
    Write-Host "`nWorker is not running and needs to be started" -ForegroundColor Yellow
} elseif ($queueStatus -ne $null -and $queueStatus.redis_connected -and $queueStatus.queue_stats.failed_job_count -gt 5) {
    $needRestart = $true
    Write-Host "`nHigh number of failed jobs detected, restart recommended" -ForegroundColor Yellow
}

# Restart the worker if needed and if the restart flag is set
if ($needRestart -and $Restart) {
    Write-Host "`nAttempting to restart the worker process..." -ForegroundColor Yellow
    
    # Kill existing worker process if running
    if ($workerRunning) {
        Write-Host "Stopping existing worker process..." -ForegroundColor Yellow
        Get-Process -Name "python" | Where-Object { $_.CommandLine -match "rq worker" } | Stop-Process -Force
        Start-Sleep -Seconds 2
    }
    
    try {
        # Start the worker process
        Write-Host "Starting new worker process..." -ForegroundColor Yellow
        
        # Call the worker start script
        $workerScript = Join-Path -Path (Get-Location) -ChildPath "scripts\start-worker.ps1"
        if (Test-Path $workerScript) {
            Start-Process -FilePath "powershell.exe" -ArgumentList "-File `"$workerScript`"" -NoNewWindow
            Write-Host "✅ Worker process started" -ForegroundColor Green
        } else {
            # If script doesn't exist, create a default one and run it
            Write-Host "Worker start script not found, creating a basic one..." -ForegroundColor Yellow
            $defaultScript = @"
# Basic worker start script
cd (Join-Path -Path (Get-Location) -ChildPath "backend")
.\venv\Scripts\activate
python -m rq worker default --with-scheduler
"@
            $defaultScriptPath = Join-Path -Path (Get-Location) -ChildPath "scripts\start-worker.ps1"
            $defaultScript | Out-File -FilePath $defaultScriptPath -Encoding utf8
            Start-Process -FilePath "powershell.exe" -ArgumentList "-File `"$defaultScriptPath`"" -NoNewWindow
            Write-Host "✅ Created and started basic worker script" -ForegroundColor Green
        }
    } catch {
        Write-Host "❌ Error restarting worker: $_" -ForegroundColor Red
    }
} elseif ($needRestart) {
    Write-Host "`nWorker needs to be restarted. Run with -Restart flag to restart automatically." -ForegroundColor Yellow
}

# Summary
Write-Host "`n===== Summary =====" -ForegroundColor Cyan
Write-Host "Redis running: $(if ($redisRunning) { '✅' } else { '❌' })" -ForegroundColor $(if ($redisRunning) { "Green" } else { "Red" })
Write-Host "Worker process running: $(if ($workerRunning) { '✅' } else { '❌' })" -ForegroundColor $(if ($workerRunning) { "Green" } else { "Red" })
if ($queueStatus -ne $null -and $queueStatus.redis_connected) {
    Write-Host "Queue connection: ✅" -ForegroundColor Green
    Write-Host "Jobs in queue: $($queueStatus.queue_stats.count)" -ForegroundColor White
    Write-Host "Failed jobs: $($queueStatus.queue_stats.failed_job_count)" -ForegroundColor White
} else {
    Write-Host "Queue connection: ❌" -ForegroundColor Red
}

if ($needRestart -and !$Restart) {
    Write-Host "`nRecommended action: Restart worker with:" -ForegroundColor Yellow
    Write-Host ".\scripts\check-worker-status.ps1 -Restart" -ForegroundColor White
}

Write-Host "=================`n" -ForegroundColor Cyan 