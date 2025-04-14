# Simple commands for running EverRaise components
# This file provides common commands to help avoid syntax issues in PowerShell

# Function to show colored output
function Write-ColoredMessage {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [string]$ForegroundColor = "White"
    )
    
    Write-Host $Message -ForegroundColor $ForegroundColor
}

# Show the menu
function Show-Menu {
    Write-ColoredMessage "=== EverRaise Management Commands ===" -ForegroundColor Cyan
    Write-ColoredMessage "1. Run backend server"
    Write-ColoredMessage "2. Run frontend server"
    Write-ColoredMessage "3. Start both backend and frontend (recommended)"
    Write-ColoredMessage "4. Check status of ports"
    Write-ColoredMessage "5. Kill process using port 8000"
    Write-ColoredMessage "6. Exit"
    Write-ColoredMessage "==============================="-ForegroundColor Cyan
}

# Main menu loop
function Main-Menu {
    $backendDir = Join-Path $PSScriptRoot "backend"
    $frontendDir = Join-Path $PSScriptRoot "frontend"
    
    while ($true) {
        Show-Menu
        $choice = Read-Host "Enter your choice (1-6)"
        
        switch ($choice) {
            "1" {
                Write-ColoredMessage "Starting backend server..." -ForegroundColor Green
                Push-Location $backendDir
                Start-Process -FilePath "python" -ArgumentList "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000" -NoNewWindow
                Pop-Location
                Write-ColoredMessage "Backend server started in a new window." -ForegroundColor Green
            }
            "2" {
                Write-ColoredMessage "Starting frontend server..." -ForegroundColor Green
                Push-Location $frontendDir
                Start-Process -FilePath "npm" -ArgumentList "run", "dev" -NoNewWindow
                Pop-Location
                Write-ColoredMessage "Frontend server started in a new window." -ForegroundColor Green
            }
            "3" {
                Write-ColoredMessage "Starting both servers using run-everraise.ps1..." -ForegroundColor Green
                & "$PSScriptRoot\run-everraise.ps1"
            }
            "4" {
                Write-ColoredMessage "Checking port status..." -ForegroundColor Yellow
                $port8000 = $null
                $port5173 = $null
                
                try {
                    $port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
                    $port5173 = Get-NetTCPConnection -LocalPort 5173 -ErrorAction SilentlyContinue
                } catch {
                    Write-ColoredMessage "Unable to check port status. Running as administrator may help." -ForegroundColor Red
                }
                
                if ($port8000) {
                    $process = Get-Process -Id $port8000.OwningProcess -ErrorAction SilentlyContinue
                    Write-ColoredMessage "Port 8000 is in use by: $($process.ProcessName) (PID: $($process.Id))" -ForegroundColor Red
                } else {
                    Write-ColoredMessage "Port 8000 is available." -ForegroundColor Green
                }
                
                if ($port5173) {
                    $process = Get-Process -Id $port5173.OwningProcess -ErrorAction SilentlyContinue
                    Write-ColoredMessage "Port 5173 is in use by: $($process.ProcessName) (PID: $($process.Id))" -ForegroundColor Red
                } else {
                    Write-ColoredMessage "Port 5173 is available." -ForegroundColor Green
                }
                
                Write-Host "Press Enter to continue..." -ForegroundColor Cyan
                Read-Host
            }
            "5" {
                Write-ColoredMessage "Attempting to kill process using port 8000..." -ForegroundColor Yellow
                try {
                    $port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
                    if ($port8000) {
                        $process = Get-Process -Id $port8000.OwningProcess -ErrorAction SilentlyContinue
                        if ($process) {
                            Write-ColoredMessage "Stopping process: $($process.ProcessName) (PID: $($process.Id))" -ForegroundColor Yellow
                            $process | Stop-Process -Force
                            Write-ColoredMessage "Process terminated successfully." -ForegroundColor Green
                        } else {
                            Write-ColoredMessage "Could not identify the process using port 8000." -ForegroundColor Red
                        }
                    } else {
                        Write-ColoredMessage "No process found using port 8000." -ForegroundColor Green
                    }
                } catch {
                    Write-ColoredMessage "Failed to kill process. Error: $_" -ForegroundColor Red
                    Write-ColoredMessage "Try running this script as administrator." -ForegroundColor Yellow
                }
                
                Write-Host "Press Enter to continue..." -ForegroundColor Cyan
                Read-Host
            }
            "6" {
                Write-ColoredMessage "Exiting..." -ForegroundColor Cyan
                return
            }
            default {
                Write-ColoredMessage "Invalid option. Please try again." -ForegroundColor Red
            }
        }
    }
}

# Start the main menu
Main-Menu 