# Script to check connection between frontend and backend
param (
    [string]$BackendUrl = "http://localhost:8000",
    [string]$FrontendUrl = "http://localhost:3000", # Default, but we'll try to detect the actual port
    [switch]$Verbose = $false
)

$ErrorActionPreference = "Continue"

# Colors for output
$GREEN = [ConsoleColor]::Green
$RED = [ConsoleColor]::Red
$YELLOW = [ConsoleColor]::Yellow
$CYAN = [ConsoleColor]::Cyan

Write-Host "`n===== Connection Test =====" -ForegroundColor $CYAN

# Try to detect Vite frontend port
Write-Host "Detecting frontend port..." -ForegroundColor $CYAN
$detectedPort = $null

# Common Vite ports to check
$possiblePorts = @(3000, 5173, 5174, 5175, 5176, 5177, 5178, 5179, 5180, 5181, 5182, 5183, 5184, 5185)

foreach ($port in $possiblePorts) {
    try {
        $testUrl = "http://localhost:$port"
        $response = Invoke-WebRequest -Uri $testUrl -Method HEAD -TimeoutSec 1 -ErrorAction Stop
        
        # If we get here, the port is responsive
        $detectedPort = $port
        $FrontendUrl = $testUrl
        Write-Host "✅ Frontend detected on port $port!" -ForegroundColor $GREEN
        break
    } catch {
        # Port not responding, try the next one
        continue
    }
}

if (-not $detectedPort) {
    Write-Host "⚠️ Could not auto-detect frontend port. Will use provided: $FrontendUrl" -ForegroundColor $YELLOW
}

Write-Host "Backend URL: $BackendUrl" -ForegroundColor $CYAN
Write-Host "Frontend URL: $FrontendUrl" -ForegroundColor $CYAN
Write-Host "==========================" -ForegroundColor $CYAN

# Test 1: Check if backend is accessible
Write-Host "`nTest 1: Checking if backend is accessible..." -ForegroundColor $CYAN
try {
    $response = Invoke-WebRequest -Uri "$BackendUrl/api/v1/health" -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Success! Backend responded with status code $($response.StatusCode)" -ForegroundColor $GREEN
    
    if ($Verbose) {
        Write-Host "Response headers:" -ForegroundColor $CYAN
        $response.Headers | Format-Table -AutoSize
        
        Write-Host "Response content:" -ForegroundColor $CYAN
        Write-Host $response.Content
    }
    
    # Parse the JSON response
    try {
        $content = $response.Content | ConvertFrom-Json
        if ($content.database -eq "connected") {
            Write-Host "✅ Database connection: OK" -ForegroundColor $GREEN
        } else {
            Write-Host "⚠️ Database connection: Failed - $($content.error)" -ForegroundColor $YELLOW
            Write-Host "   This may not affect the application if it's not trying to access the database." -ForegroundColor $YELLOW
        }
    } catch {
        Write-Host "⚠️ Could not parse JSON response: $_" -ForegroundColor $YELLOW
    }
} catch {
    Write-Host "❌ Failed to connect to backend: $_" -ForegroundColor $RED
    Write-Host "   Check if the backend is running with 'scripts\start-backend.ps1'" -ForegroundColor $YELLOW
}

# Test 2: Check if frontend is accessible
Write-Host "`nTest 2: Checking if frontend is accessible..." -ForegroundColor $CYAN
try {
    $response = Invoke-WebRequest -Uri $FrontendUrl -Method GET -TimeoutSec 5 -ErrorAction Stop
    Write-Host "✅ Success! Frontend responded with status code $($response.StatusCode)" -ForegroundColor $GREEN
    
    if ($Verbose) {
        Write-Host "Response headers:" -ForegroundColor $CYAN
        $response.Headers | Format-Table -AutoSize
    }
} catch {
    Write-Host "❌ Failed to connect to frontend: $_" -ForegroundColor $RED
    Write-Host "   Check if the frontend is running with 'scripts\start-frontend.ps1'" -ForegroundColor $YELLOW
    
    # Provide hint about checking other ports
    Write-Host "   Hint: The frontend might be running on a different port. Check your terminal output." -ForegroundColor $YELLOW
    Write-Host "   Common Vite ports: 5173, 5174, 5175, etc." -ForegroundColor $YELLOW
}

# Test 3: Check CORS from frontend to backend
Write-Host "`nTest 3: Checking CORS configuration..." -ForegroundColor $CYAN
try {
    $response = Invoke-WebRequest -Uri "$BackendUrl/api" -Method OPTIONS -Headers @{
        "Origin" = $FrontendUrl
        "Access-Control-Request-Method" = "GET"
    } -TimeoutSec 5 -ErrorAction Stop
    
    $corsHeaders = $response.Headers | Where-Object { $_ -match "Access-Control" }
    if ($corsHeaders) {
        Write-Host "✅ Success! CORS is properly configured" -ForegroundColor $GREEN
        if ($Verbose) {
            Write-Host "CORS Headers:" -ForegroundColor $CYAN
            $corsHeaders | Format-Table -AutoSize
        }
    } else {
        Write-Host "⚠️ No CORS headers found in the response" -ForegroundColor $YELLOW
        Write-Host "   This might cause issues when frontend tries to access the backend" -ForegroundColor $YELLOW
    }
} catch {
    Write-Host "❌ Failed to check CORS configuration: $_" -ForegroundColor $RED
}

# Test 4: Check environment variable for API URL
Write-Host "`nTest 4: Checking frontend environment file..." -ForegroundColor $CYAN
$envPath = Join-Path (Split-Path -Parent $PSScriptRoot) "frontend\.env.local"
if (Test-Path $envPath) {
    $envContent = Get-Content $envPath -Raw
    Write-Host "Found .env.local file:" -ForegroundColor $CYAN
    Write-Host $envContent -ForegroundColor $GREEN
    
    if ($envContent -match "VITE_API_URL=(.*)") {
        $apiUrl = $matches[1].Trim()
        Write-Host "✅ API URL is set to: $apiUrl" -ForegroundColor $GREEN
        
        if ($apiUrl -ne $BackendUrl) {
            Write-Host "⚠️ WARNING: API URL in .env.local ($apiUrl) doesn't match expected backend URL ($BackendUrl)" -ForegroundColor $YELLOW
        }
    } else {
        Write-Host "❌ VITE_API_URL not found in .env.local" -ForegroundColor $RED
    }
} else {
    Write-Host "⚠️ No .env.local file found in frontend directory" -ForegroundColor $YELLOW
    
    # Check .env file
    $envPath = Join-Path (Split-Path -Parent $PSScriptRoot) "frontend\.env"
    if (Test-Path $envPath) {
        $envContent = Get-Content $envPath -Raw
        Write-Host "Found .env file:" -ForegroundColor $CYAN
        Write-Host $envContent -ForegroundColor $GREEN
        
        if ($envContent -match "VITE_API_URL=(.*)") {
            $apiUrl = $matches[1].Trim()
            Write-Host "✅ API URL is set to: $apiUrl" -ForegroundColor $GREEN
            
            if ($apiUrl -ne $BackendUrl) {
                Write-Host "⚠️ WARNING: API URL in .env ($apiUrl) doesn't match expected backend URL ($BackendUrl)" -ForegroundColor $YELLOW
            }
        } else {
            Write-Host "❌ VITE_API_URL not found in .env" -ForegroundColor $RED
        }
    } else {
        Write-Host "❌ No environment files found for frontend" -ForegroundColor $RED
    }
}

# Final summary
Write-Host "`n===== Summary =====" -ForegroundColor $CYAN
Write-Host "If all tests passed, the frontend should be able to connect to the backend." -ForegroundColor $CYAN
Write-Host "If you're still seeing 'Backend Offline' in the Integrations page:" -ForegroundColor $CYAN
Write-Host "1. IMPORTANT: Check that you're accessing the frontend on the correct port (currently: $(if ($detectedPort) { $detectedPort } else { 'unknown' }))" -ForegroundColor $CYAN
Write-Host "2. Try clearing your browser cache or opening in incognito mode" -ForegroundColor $CYAN
Write-Host "3. Check browser console (F12) for any errors" -ForegroundColor $CYAN
Write-Host "4. Verify that the frontend code correctly handles API responses" -ForegroundColor $CYAN
Write-Host "5. Restart both frontend and backend services" -ForegroundColor $CYAN
Write-Host "=================`n" -ForegroundColor $CYAN 