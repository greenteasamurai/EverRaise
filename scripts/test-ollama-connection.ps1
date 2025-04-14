# Script to test Ollama API connection
param(
    [string]$OllamaUrl = "http://localhost:11434",
    [string]$Model = "llama2",
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Stop"

# Output banner
Write-Host "===== Ollama Connection Test =====" -ForegroundColor Cyan
Write-Host "URL: $OllamaUrl" -ForegroundColor Cyan
Write-Host "Model: $Model" -ForegroundColor Cyan
Write-Host "=================================" -ForegroundColor Cyan

# Test 1: Check if Ollama API is accessible
Write-Host "`nTest 1: Checking Ollama API accessibility..." -ForegroundColor Green
try {
    $response = Invoke-RestMethod -Uri "$OllamaUrl/api/tags" -Method Get -TimeoutSec 5
    if ($Verbose) {
        Write-Host "Response: $($response | ConvertTo-Json -Depth 3)" -ForegroundColor Gray
    }
    
    $modelCount = $response.models.Count
    Write-Host "✅ Success! Ollama API is accessible. Found $modelCount models." -ForegroundColor Green
    
    # Check if requested model is available
    $availableModels = $response.models | ForEach-Object { $_.name }
    if ($availableModels -contains $Model) {
        Write-Host "✅ Success! Model '$Model' is available." -ForegroundColor Green
    } else {
        Write-Host "❌ Error: Model '$Model' is not available." -ForegroundColor Red
        Write-Host "Available models:" -ForegroundColor Yellow
        $availableModels | ForEach-Object { Write-Host " - $_" -ForegroundColor Yellow }
        
        # Ask if user wants to pull the model
        $pullModel = Read-Host "Do you want to pull the '$Model' model now? (y/n)"
        if ($pullModel -eq "y") {
            Write-Host "Pulling model '$Model' (this may take several minutes)..." -ForegroundColor Yellow
            try {
                $pullResponse = Invoke-RestMethod -Uri "$OllamaUrl/api/pull" -Method Post -Body (@{name=$Model} | ConvertTo-Json) -ContentType "application/json"
                Write-Host "Model pull started. Check Ollama logs for progress." -ForegroundColor Green
            } catch {
                Write-Host "❌ Error pulling model: $_" -ForegroundColor Red
            }
        } else {
            Write-Host "Continuing tests with available models..." -ForegroundColor Yellow
            # Try to use an available model for test 2
            if ($availableModels.Count -gt 0) {
                $Model = $availableModels[0]
                Write-Host "Using '$Model' for generation test." -ForegroundColor Yellow
            } else {
                Write-Host "No models available for testing." -ForegroundColor Red
                exit 1
            }
        }
    }
} catch {
    Write-Host "❌ Error: Cannot connect to Ollama API at $OllamaUrl" -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    
    # Check if Ollama is installed
    try {
        $ollamaPath = Get-Command ollama -ErrorAction SilentlyContinue
        if ($ollamaPath) {
            Write-Host "Ollama is installed but not running. Try starting it with: ollama serve" -ForegroundColor Yellow
        } else {
            Write-Host "Ollama might not be installed. Visit https://ollama.ai/download to install." -ForegroundColor Yellow
        }
    } catch {
        Write-Host "Ollama might not be installed. Visit https://ollama.ai/download to install." -ForegroundColor Yellow
    }
    
    exit 1
}

# Test 2: Send a simple prompt to test generation
Write-Host "`nTest 2: Testing model generation..." -ForegroundColor Green
$prompt = "Say hello in one word."
$body = @{
    model = $Model
    prompt = $prompt
    stream = $false
} | ConvertTo-Json

Write-Host "Sending prompt: '$prompt'" -ForegroundColor Cyan
try {
    $startTime = Get-Date
    $genResponse = Invoke-RestMethod -Uri "$OllamaUrl/api/generate" -Method Post -Body $body -ContentType "application/json" -TimeoutSec 30
    $endTime = Get-Date
    $duration = ($endTime - $startTime).TotalMilliseconds
    
    if ($Verbose) {
        Write-Host "Response: $($genResponse | ConvertTo-Json)" -ForegroundColor Gray
    }
    
    Write-Host "✅ Success! Model responded in $($duration.ToString("0.00"))ms" -ForegroundColor Green
    Write-Host "Response: '$($genResponse.response.Trim())'" -ForegroundColor Green
} catch {
    Write-Host "❌ Error: Failed to generate text with model $Model" -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    exit 1
}

# Test 3: Test application diagnostics endpoint
Write-Host "`nTest 3: Testing application diagnostics..." -ForegroundColor Green
try {
    $backendUrl = "http://localhost:8000"  # Default backend URL
    $diagnosticsUrl = "$backendUrl/api/v1/diagnostics/ollama/status"
    
    Write-Host "Checking backend diagnostic endpoint at $diagnosticsUrl" -ForegroundColor Cyan
    $diagResponse = Invoke-RestMethod -Uri $diagnosticsUrl -Method Get -TimeoutSec 10
    
    if ($Verbose) {
        Write-Host "Response: $($diagResponse | ConvertTo-Json -Depth 3)" -ForegroundColor Gray
    }
    
    if ($diagResponse.available) {
        Write-Host "✅ Success! Backend can connect to Ollama." -ForegroundColor Green
        Write-Host "Available models: $($diagResponse.models -join ', ')" -ForegroundColor Green
        
        if ($diagResponse.simple_test.success) {
            Write-Host "✅ Simple test passed: '$($diagResponse.simple_test.response)'" -ForegroundColor Green
            Write-Host "Response time: $($diagResponse.simple_test.time_ms)ms" -ForegroundColor Green
        } else {
            Write-Host "❌ Simple test failed: $($diagResponse.simple_test.error)" -ForegroundColor Red
        }
    } else {
        Write-Host "❌ Error: Backend cannot connect to Ollama" -ForegroundColor Red
        Write-Host "Error details: $($diagResponse.error)" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error: Cannot connect to backend diagnostics" -ForegroundColor Red
    Write-Host "Error details: $_" -ForegroundColor Red
    
    # Try to start the backend server if it's not running
    Write-Host "Attempting to check if backend is running..." -ForegroundColor Yellow
    try {
        $healthResponse = Invoke-WebRequest -Uri "$backendUrl/api/v1/health" -Method Get -TimeoutSec 2
        Write-Host "Backend is running but diagnostics endpoint failed." -ForegroundColor Yellow
    } catch {
        Write-Host "Backend might not be running. Try starting it first with:" -ForegroundColor Yellow
        Write-Host "scripts\start-backend.ps1" -ForegroundColor Yellow
        
        # Ask if user wants to start the backend now
        $startBackend = Read-Host "Do you want to try starting the backend now? (y/n)"
        if ($startBackend -eq "y") {
            Write-Host "Attempting to start backend..." -ForegroundColor Yellow
            try {
                Start-Process -FilePath "powershell.exe" -ArgumentList "-File scripts\start-backend.ps1" -NoNewWindow
                Write-Host "Backend starting, please wait..." -ForegroundColor Yellow
                Start-Sleep -Seconds 5  # Give it some time to start
                try {
                    $healthResponse = Invoke-WebRequest -Uri "$backendUrl/api/v1/health" -Method Get -TimeoutSec 2
                    Write-Host "✅ Backend started successfully!" -ForegroundColor Green
                } catch {
                    Write-Host "❌ Backend failed to start or is not responding." -ForegroundColor Red
                }
            } catch {
                Write-Host "❌ Failed to start backend: $_" -ForegroundColor Red
            }
        }
    }
}

# Test 4: Check report generation diagnostic endpoint
Write-Host "`nTest 4: Testing report generation diagnostics..." -ForegroundColor Green
try {
    $reportDiagUrl = "http://localhost:8000/api/v1/diagnostics/report/test"
    Write-Host "Checking report generation diagnostic endpoint at $reportDiagUrl" -ForegroundColor Cyan
    
    try {
        $reportDiagResponse = Invoke-RestMethod -Uri $reportDiagUrl -Method Get -TimeoutSec 15
        
        if ($Verbose) {
            Write-Host "Response: $($reportDiagResponse | ConvertTo-Json -Depth 3)" -ForegroundColor Gray
        }
        
        if ($reportDiagResponse.status -eq "operational") {
            Write-Host "✅ Success! Report generation system is operational." -ForegroundColor Green
            Write-Host "Vector store test: $($reportDiagResponse.vectorstore_test.success)" -ForegroundColor Green
            Write-Host "Generation test: $($reportDiagResponse.generation_test.success)" -ForegroundColor Green
        } elseif ($reportDiagResponse.status -eq "degraded") {
            Write-Host "⚠️ Warning: Report generation system is degraded." -ForegroundColor Yellow
            if ($reportDiagResponse.vectorstore_test.success) {
                Write-Host "Vector store test: $($reportDiagResponse.vectorstore_test.success)" -ForegroundColor Green
            } else {
                Write-Host "Vector store test: $($reportDiagResponse.vectorstore_test.success)" -ForegroundColor Red
            }
            
            if ($reportDiagResponse.generation_test.success) {
                Write-Host "Generation test: $($reportDiagResponse.generation_test.success)" -ForegroundColor Green
            } else {
                Write-Host "Generation test: $($reportDiagResponse.generation_test.success)" -ForegroundColor Red
            }
        } else {
            Write-Host "❌ Error: Report generation system is failing." -ForegroundColor Red
            Write-Host "Status: $($reportDiagResponse.status)" -ForegroundColor Red
            Write-Host "Error: $($reportDiagResponse.error)" -ForegroundColor Red
        }
    } catch {
        Write-Host "❌ Error: Cannot access report diagnostics" -ForegroundColor Red
        Write-Host "Error details: $_" -ForegroundColor Red
    }
} catch {
    Write-Host "❌ Error accessing report diagnostics: $_" -ForegroundColor Red
}

# Summary
Write-Host "`n===== Summary =====" -ForegroundColor Cyan
Write-Host "Ollama API is accessible: ✅" -ForegroundColor Green
Write-Host "Model '$Model' is available: ✅" -ForegroundColor Green
Write-Host "Simple generation test: ✅" -ForegroundColor Green
Write-Host "`nIf any of the above tests failed, please check the error messages." -ForegroundColor Cyan
Write-Host "If all tests passed but the application still has issues, the problem might be with the application itself." -ForegroundColor Cyan
Write-Host "=================`n" -ForegroundColor Cyan 