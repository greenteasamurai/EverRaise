# Master diagnostic script for EverRaise report generation
param(
    [switch]$FixIssues = $false,
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Continue"

# Define text colors and formatting
$CYAN = [ConsoleColor]::Cyan
$GREEN = [ConsoleColor]::Green
$RED = [ConsoleColor]::Red
$YELLOW = [ConsoleColor]::Yellow
$MAGENTA = [ConsoleColor]::Magenta

function Write-Header {
    param ([string]$Text)
    Write-Host "`n===============================================" -ForegroundColor $CYAN
    Write-Host " $Text" -ForegroundColor $CYAN
    Write-Host "===============================================" -ForegroundColor $CYAN
}

function Write-StepHeader {
    param ([string]$Text)
    Write-Host "`n>> $Text" -ForegroundColor $MAGENTA
}

function Write-Success {
    param ([string]$Text)
    Write-Host "✅ $Text" -ForegroundColor $GREEN
}

function Write-Error {
    param ([string]$Text)
    Write-Host "❌ $Text" -ForegroundColor $RED
}

function Write-Warning {
    param ([string]$Text)
    Write-Host "⚠️ $Text" -ForegroundColor $YELLOW
}

# Show banner
Write-Header "EverRaise Report Generation Diagnostics"
Write-Host "This script will diagnose issues with the report generation feature.`n"
Write-Host "Will fix issues automatically: $FixIssues"
Write-Host "Verbose mode: $Verbose"

# Check if Ollama is installed
Write-StepHeader "Checking if Ollama is installed"
try {
    $ollamaVersion = ollama -v 2>&1
    Write-Success "Ollama is installed: $ollamaVersion"
} catch {
    Write-Error "Ollama is not installed or not in the PATH"
    Write-Host "Please install Ollama from https://ollama.ai/" -ForegroundColor $YELLOW
    Write-Host "Continuing with diagnostics, but report generation will fail without Ollama" -ForegroundColor $YELLOW
}

# Check if Ollama is running
Write-StepHeader "Checking if Ollama service is running"
try {
    $ollamaRunning = $false
    $testConnection = Invoke-WebRequest -Uri "http://localhost:11434/api/version" -Method HEAD -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($testConnection.StatusCode -eq 200) {
        $ollamaRunning = $true
        Write-Success "Ollama service is running at http://localhost:11434"
    }
} catch {
    Write-Error "Ollama service is not running"
    
    if ($FixIssues) {
        Write-Host "Attempting to start Ollama service..." -ForegroundColor $YELLOW
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden
        Write-Host "Waiting for Ollama to start (10 seconds)..." -ForegroundColor $YELLOW
        Start-Sleep -Seconds 10
        
        try {
            $testConnection = Invoke-WebRequest -Uri "http://localhost:11434/api/version" -Method HEAD -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($testConnection.StatusCode -eq 200) {
                $ollamaRunning = $true
                Write-Success "Successfully started Ollama service"
            } else {
                Write-Error "Failed to start Ollama service"
            }
        } catch {
            Write-Error "Failed to start Ollama service"
        }
    } else {
        Write-Warning "To start Ollama, run: ollama serve"
    }
}

# Run the Ollama connection test
Write-StepHeader "Running Ollama connection test"
if ($ollamaRunning) {
    $verboseArg = if ($Verbose) { "-Verbose" } else { "" }
    & "$PSScriptRoot\test-ollama-connection.ps1" $verboseArg
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Ollama connection test failed with exit code $LASTEXITCODE"
    } else {
        Write-Success "Ollama connection test completed successfully"
    }
} else {
    Write-Warning "Skipping Ollama connection test since the service is not running"
}

# Check if backend is running
Write-StepHeader "Checking if backend API is running"
$backendRunning = $false
try {
    $testBackend = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -Method HEAD -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($testBackend.StatusCode -eq 200) {
        $backendRunning = $true
        Write-Success "Backend API is running at http://localhost:8000"
    }
} catch {
    Write-Error "Backend API is not running"
    
    if ($FixIssues) {
        Write-Host "Attempting to start the backend API..." -ForegroundColor $YELLOW
        Start-Process -FilePath "powershell.exe" -ArgumentList "-File $PSScriptRoot\start-backend.ps1" -WindowStyle Hidden
        Write-Host "Waiting for backend to start (15 seconds)..." -ForegroundColor $YELLOW
        Start-Sleep -Seconds 15
        
        try {
            $testBackend = Invoke-WebRequest -Uri "http://localhost:8000/api/v1/health" -Method HEAD -TimeoutSec 2 -ErrorAction SilentlyContinue
            if ($testBackend.StatusCode -eq 200) {
                $backendRunning = $true
                Write-Success "Successfully started backend API"
            } else {
                Write-Error "Failed to start backend API"
            }
        } catch {
            Write-Error "Failed to start backend API"
        }
    } else {
        Write-Warning "To start the backend, run: scripts\start-backend.ps1"
    }
}

# Check if frontend is running
Write-StepHeader "Checking if frontend is running"
$frontendRunning = $false
try {
    $testFrontend = Invoke-WebRequest -Uri "http://localhost:3000" -Method HEAD -TimeoutSec 2 -ErrorAction SilentlyContinue
    if ($testFrontend.StatusCode -eq 200) {
        $frontendRunning = $true
        Write-Success "Frontend is running at http://localhost:3000"
    }
} catch {
    Write-Warning "Frontend is not running"
    Write-Host "To start the frontend, run: scripts\start-frontend.ps1" -ForegroundColor $YELLOW
    Write-Host "Frontend status is not critical for the backend diagnostics" -ForegroundColor $YELLOW
}

# Test the report generation API if possible
if ($backendRunning -and $ollamaRunning) {
    Write-StepHeader "Testing report generation API"
    $verboseArg = if ($Verbose) { "-Verbose" } else { "" }
    & "$PSScriptRoot\test-report-generation.ps1" $verboseArg
    
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Report generation API test failed with exit code $LASTEXITCODE"
    } else {
        Write-Success "Report generation API test completed successfully"
    }
} else {
    Write-Warning "Skipping report generation API test since backend or Ollama is not running"
}

# Provide a summary and recommendations
Write-Header "Diagnostic Summary"

$issues = 0
$recommendations = @()

if (-not $ollamaRunning) {
    $issues++
    $recommendations += "Start Ollama with 'ollama serve'"
}

# Check if llama2 model is available if Ollama is running
if ($ollamaRunning) {
    try {
        $modelsResponse = Invoke-RestMethod -Uri "http://localhost:11434/api/tags" -Method Get -TimeoutSec 5
        $llama2Available = $modelsResponse.models | Where-Object { $_.name -like "*llama2*" }
        
        if (-not $llama2Available) {
            $issues++
            Write-Error "Llama2 model is not available in Ollama"
            $recommendations += "Pull the Llama2 model with 'ollama pull llama2'"
        } else {
            Write-Success "Llama2 model is available"
        }
    } catch {
        Write-Error "Failed to check available models"
        $issues++
    }
}

if (-not $backendRunning) {
    $issues++
    $recommendations += "Start the backend with 'scripts\start-backend.ps1'"
}

if (-not $frontendRunning) {
    $issues++
    $recommendations += "Start the frontend with 'scripts\start-frontend.ps1'"
}

# Check diagnostics endpoint if backend is running
if ($backendRunning) {
    try {
        $diagnosticsResponse = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/diagnostics/ollama/status" -Method Get -TimeoutSec 10
        
        if (-not $diagnosticsResponse.available) {
            $issues++
            Write-Error "Backend cannot connect to Ollama: $($diagnosticsResponse.error)"
            $recommendations += "Verify Ollama is running on $($diagnosticsResponse.url)"
        } else {
            Write-Success "Backend can connect to Ollama"
            
            if (-not $diagnosticsResponse.simple_test.success) {
                $issues++
                Write-Error "Backend failed simple generation test: $($diagnosticsResponse.simple_test.error)"
                $recommendations += "Check Ollama logs for errors"
            } else {
                Write-Success "Backend successfully generated text with Ollama"
            }
        }
    } catch {
        Write-Error "Failed to access diagnostics endpoint: $_"
        $issues++
        $recommendations += "Check if backend has the diagnostics route enabled"
    }
}

Write-Host "`nFound $issues issue(s) to fix." -ForegroundColor $(if ($issues -eq 0) { $GREEN } else { $YELLOW })

if ($issues -gt 0) {
    Write-Host "`nRecommendations:" -ForegroundColor $CYAN
    foreach ($rec in $recommendations) {
        Write-Host "- $rec" -ForegroundColor $YELLOW
    }
    
    Write-Host "`nPlease refer to README-REPORT-FIX.md for detailed troubleshooting guide." -ForegroundColor $CYAN
} else {
    Write-Success "All systems are operational! Report generation should work correctly."
}

Write-Host "`nTo test the report generation feature in the application:`n" -ForegroundColor $CYAN
Write-Host "1. Navigate to http://localhost:3000/reports"
Write-Host "2. Create a new report with a suitable title and type"
Write-Host "3. Monitor the console for errors (F12 > Console)"
Write-Host "4. Check the network requests during report generation (F12 > Network)`n" 