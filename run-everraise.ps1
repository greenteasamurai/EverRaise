# Main script to run EverRaise after reorganization
# This script serves as a frontend to the scripts in the scripts directory

param(
    [int]$BackendPort = 0  # 0 = use default from config
)

$ScriptsDir = Join-Path $PSScriptRoot "scripts"

# Import shared configuration if it exists
$configModule = Join-Path $ScriptsDir "config.psm1"
if (Test-Path $configModule) {
    Import-Module $configModule -Force
    # Use the provided port or get the default
    if ($BackendPort -eq 0) {
        $BackendPort = Get-BackendPort
    }
    Write-Host "Using backend port: $BackendPort" -ForegroundColor Cyan
}

# Display welcome message
Clear-Host
Write-Host "EverRaise Application Launcher" -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host "This script will help you start the EverRaise application."
Write-Host

# Menu options
function Show-Menu {
    Write-Host "Menu Options:" -ForegroundColor Green
    Write-Host "1. Start EverRaise (Backend and Frontend)"
    Write-Host "2. Start Backend Only"
    Write-Host "3. Start Frontend Only"
    Write-Host "4. Fix Common Issues"
    Write-Host "5. Run Tests"
    Write-Host "6. Exit"
    Write-Host
    $option = Read-Host "Select an option (1-6)"
    return $option
}

# Execute the selected option
function Execute-Option {
    param (
        [string]$Option
    )
    
    switch ($Option) {
        "1" {
            Write-Host "`nStarting EverRaise (Backend and Frontend)..." -ForegroundColor Cyan
            if ($BackendPort -gt 0) {
                & "$ScriptsDir\run-everraise.ps1" -BackendPort $BackendPort
            } else {
                & "$ScriptsDir\run-everraise.ps1"
            }
        }
        "2" {
            Write-Host "`nStarting Backend Only..." -ForegroundColor Cyan
            if ($BackendPort -gt 0) {
                & "$ScriptsDir\start-backend.ps1" -Port $BackendPort
            } else {
                & "$ScriptsDir\start-backend.ps1"
            }
        }
        "3" {
            Write-Host "`nStarting Frontend Only..." -ForegroundColor Cyan
            & "$ScriptsDir\start-frontend.ps1"
        }
        "4" {
            Write-Host "`nLaunching Issue Fixer..." -ForegroundColor Cyan
            & "$ScriptsDir\fix-issues.ps1"
        }
        "5" {
            Write-Host "`nRunning Tests..." -ForegroundColor Cyan
            & "$ScriptsDir\run_all_tests.ps1"
        }
        "6" {
            Write-Host "`nExiting..." -ForegroundColor Cyan
            exit
        }
        default {
            Write-Host "`nInvalid option. Please try again." -ForegroundColor Red
            Pause
            return
        }
    }
}

# Display port configuration notice
Write-Host "NOTE: You can customize the backend port by running:" -ForegroundColor Yellow
Write-Host "      .\run-everraise.ps1 -BackendPort <port_number>" -ForegroundColor Yellow
Write-Host

# Main loop
while ($true) {
    $option = Show-Menu
    Execute-Option -Option $option
    
    # If we reach here, we need to prompt to continue or exit
    Write-Host
    $continue = Read-Host "Press Enter to return to menu or type 'exit' to quit"
    if ($continue -eq "exit") {
        break
    }
    
    Clear-Host
    Write-Host "EverRaise Application Launcher" -ForegroundColor Cyan
    Write-Host "============================" -ForegroundColor Cyan
    if ($BackendPort -gt 0) {
        Write-Host "Using backend port: $BackendPort" -ForegroundColor Cyan
    }
} 