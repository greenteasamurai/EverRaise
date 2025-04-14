# EverRaise Issue Fixer Script
# This script helps diagnose and fix common issues with the EverRaise application

function Write-ColoredMessage {
    param (
        [Parameter(Mandatory=$true)]
        [string]$Message,
        
        [Parameter(Mandatory=$false)]
        [string]$ForegroundColor = "White"
    )
    
    Write-Host $Message -ForegroundColor $ForegroundColor
}

# Get the root directory of the project (parent of the scripts directory)
$RootDir = Split-Path -Parent $PSScriptRoot

# Import shared configuration
Import-Module "$PSScriptRoot\config.psm1" -Force

# Get port numbers from configuration
$BackendPort = Get-BackendPort
$FrontendPort = Get-FrontendPort

Write-ColoredMessage "Using configuration:" -ForegroundColor Cyan
Write-ColoredMessage "  Backend Port: $BackendPort" -ForegroundColor Cyan
Write-ColoredMessage "  Frontend Port: $FrontendPort" -ForegroundColor Cyan

function Fix-PortConflict {
    Write-ColoredMessage "Checking for port conflicts on $BackendPort..." -ForegroundColor Cyan
    
    try {
        $connections = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue
        if ($connections) {
            Write-ColoredMessage "Found processes using port $BackendPort:" -ForegroundColor Yellow
            foreach ($conn in $connections) {
                $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
                if ($process) {
                    Write-ColoredMessage "Process: $($process.ProcessName) (PID: $($process.Id))" -ForegroundColor Yellow
                }
            }
            
            $choice = Read-Host "Do you want to kill these processes? (Y/N)"
            if ($choice -eq "Y" -or $choice -eq "y") {
                foreach ($conn in $connections) {
                    try {
                        $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
                        if ($process) {
                            Write-ColoredMessage "Killing process: $($process.ProcessName) (PID: $($process.Id))" -ForegroundColor Yellow
                            Stop-Process -Id $process.Id -Force
                        }
                    } catch {
                        Write-ColoredMessage "Error killing process: $_" -ForegroundColor Red
                    }
                }
                
                # Check if port is now free
                Start-Sleep -Seconds 2
                $remainingConnections = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue
                if ($remainingConnections) {
                    Write-ColoredMessage "WARNING: Port $BackendPort is still in use after attempted termination" -ForegroundColor Red
                } else {
                    Write-ColoredMessage "SUCCESS: Port $BackendPort is now free" -ForegroundColor Green
                }
            }
        } else {
            Write-ColoredMessage "Port $BackendPort is not currently in use" -ForegroundColor Green
        }
    } catch {
        Write-ColoredMessage "Error checking port usage: $_" -ForegroundColor Red
    }
}

function Fix-Database {
    $backendDir = Join-Path $RootDir "backend"
    $dbPath = Join-Path $backendDir "everraise.db"
    
    if (-not (Test-Path $backendDir)) {
        Write-ColoredMessage "Backend directory not found at $backendDir" -ForegroundColor Red
        return
    }
    
    Write-ColoredMessage "Checking database..." -ForegroundColor Cyan
    
    if (Test-Path $dbPath) {
        Write-ColoredMessage "Database found at $dbPath" -ForegroundColor Yellow
        $choice = Read-Host "Do you want to (B)ackup, (R)emove, or (S)kip database operations? (B/R/S)"
        
        switch ($choice) {
            "B" {
                $backupPath = "$dbPath.backup-$(Get-Date -Format 'yyyyMMdd-HHmmss')"
                try {
                    Copy-Item $dbPath $backupPath -Force
                    Write-ColoredMessage "Database backed up to $backupPath" -ForegroundColor Green
                } catch {
                    Write-ColoredMessage "Error backing up database: $_" -ForegroundColor Red
                }
            }
            "R" {
                try {
                    Rename-Item $dbPath "$dbPath.old" -Force
                    Write-ColoredMessage "Database renamed to everraise.db.old" -ForegroundColor Green
                    Write-ColoredMessage "A new database will be created when you start the application" -ForegroundColor Green
                } catch {
                    Write-ColoredMessage "Error removing database: $_" -ForegroundColor Red
                }
            }
            default {
                Write-ColoredMessage "Skipping database operations" -ForegroundColor Yellow
            }
        }
    } else {
        Write-ColoredMessage "No database found at $dbPath" -ForegroundColor Yellow
        Write-ColoredMessage "A new database will be created when you start the application" -ForegroundColor Green
    }
}

function Start-Servers {
    Write-ColoredMessage "Starting servers the correct way..." -ForegroundColor Cyan
    
    # First make sure port is free
    $connections = Get-NetTCPConnection -LocalPort $BackendPort -ErrorAction SilentlyContinue
    if ($connections) {
        Write-ColoredMessage "Port $BackendPort is still in use. Please fix the port conflict first." -ForegroundColor Red
        return
    }
    
    $backendDir = Join-Path $RootDir "backend"
    $frontendDir = Join-Path $RootDir "frontend"
    
    # Check if directories exist
    if (-not (Test-Path $backendDir)) {
        Write-ColoredMessage "Backend directory not found at $backendDir" -ForegroundColor Red
        return
    }
    
    if (-not (Test-Path $frontendDir)) {
        Write-ColoredMessage "Frontend directory not found at $frontendDir" -ForegroundColor Red
        return
    }
    
    # Create .env file for frontend with correct backend URL
    $frontendEnvFile = Join-Path $frontendDir ".env.local"
    Write-ColoredMessage "Creating frontend environment file at $frontendEnvFile" -ForegroundColor Cyan
    $envContent = @"
# Auto-generated by EverRaise startup script
VITE_API_URL=http://localhost:{0}
"@ -f $BackendPort
    Set-Content -Path $frontendEnvFile -Value $envContent -Force
    
    # Start backend in a new window
    Write-ColoredMessage "Starting backend server..." -ForegroundColor Green
    Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$backendDir'; python -m uvicorn app.main:app --host 0.0.0.0 --port $BackendPort"
    
    # Wait a bit for backend to start
    Write-ColoredMessage "Waiting for backend to start..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Start frontend in a new window
    Write-ColoredMessage "Starting frontend server..." -ForegroundColor Green
    Start-Process powershell.exe -ArgumentList "-NoExit", "-Command", "cd '$frontendDir'; npm run dev"
    
    Write-ColoredMessage "Servers should be starting in separate windows" -ForegroundColor Green
    Write-ColoredMessage "Frontend will be available at: http://localhost:$FrontendPort" -ForegroundColor Cyan
    Write-ColoredMessage "Backend will be available at: http://localhost:$BackendPort" -ForegroundColor Cyan
}

# Show the main menu
function Show-Menu {
    Write-Host
    Write-ColoredMessage "=== EverRaise Issue Fixer ===" -ForegroundColor Cyan
    Write-ColoredMessage "1. Fix port $BackendPort conflict (kill processes using port $BackendPort)"
    Write-ColoredMessage "2. Fix database issues (backup or remove database)"
    Write-ColoredMessage "3. Start servers correctly (in separate windows)"
    Write-ColoredMessage "4. Fix everything and start servers"
    Write-ColoredMessage "5. Exit"
    Write-ColoredMessage "=============================" -ForegroundColor Cyan
    $choice = Read-Host "Enter your choice (1-5)"
    return $choice
}

# Main menu loop
while ($true) {
    $choice = Show-Menu
    
    switch ($choice) {
        "1" {
            Fix-PortConflict
            Write-Host "Press Enter to continue..."
            Read-Host
        }
        "2" {
            Fix-Database
            Write-Host "Press Enter to continue..."
            Read-Host
        }
        "3" {
            Start-Servers
            Write-Host "Press Enter to continue..."
            Read-Host
        }
        "4" {
            Fix-PortConflict
            Fix-Database
            Start-Servers
            Write-Host "Press Enter to continue..."
            Read-Host
        }
        "5" {
            Write-ColoredMessage "Exiting..." -ForegroundColor Cyan
            return
        }
        default {
            Write-ColoredMessage "Invalid option. Please try again." -ForegroundColor Red
            Write-Host "Press Enter to continue..."
            Read-Host
        }
    }
} 