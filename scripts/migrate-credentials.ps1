# Script to migrate credentials to a secure location
# Usage: .\scripts\migrate-credentials.ps1 -SecureRoot C:\EverRaise-Secure

param(
    [string]$SecureRoot = "C:\EverRaise-Secure",
    [switch]$Force = $false,
    [switch]$Encrypt = $true
)

$ErrorActionPreference = "Stop"

# Banner
Write-Host "===== EverRaise Credential Migration =====" -ForegroundColor Cyan
Write-Host "Migrating credentials to secure location: $SecureRoot" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Create secure directories if they don't exist
$dirs = @(
    "$SecureRoot",
    "$SecureRoot\tokens",
    "$SecureRoot\credentials"
)

foreach ($dir in $dirs) {
    if (-not (Test-Path $dir)) {
        Write-Host "Creating directory: $dir" -ForegroundColor Yellow
        New-Item -Path $dir -ItemType Directory -Force | Out-Null
    }
}

# Define source and destination paths
$credentialPairs = @{
    # Gmail API credentials
    "backend\credentials.json" = "$SecureRoot\credentials\gmail_credentials.json"
    "backend\token.json" = "$SecureRoot\tokens\gmail_token.json"
    
    # Check app directory too
    "backend\app\credentials.json" = "$SecureRoot\credentials\gmail_credentials.json"
    "backend\app\token.json" = "$SecureRoot\tokens\gmail_token.json"
}

# Migrate each file
$migratedCount = 0
foreach ($source in $credentialPairs.Keys) {
    $destination = $credentialPairs[$source]
    
    if (Test-Path $source) {
        # Check if destination exists
        if ((Test-Path $destination) -and -not $Force) {
            $overwrite = Read-Host "Destination file already exists: $destination. Overwrite? (y/n)"
            if ($overwrite -ne "y") {
                Write-Host "Skipping $source..." -ForegroundColor Yellow
                continue
            }
        }
        
        # Ensure destination directory exists
        $destDir = Split-Path -Parent $destination
        if (-not (Test-Path $destDir)) {
            New-Item -Path $destDir -ItemType Directory -Force | Out-Null
        }
        
        # Copy file
        Copy-Item -Path $source -Destination $destination -Force
        Write-Host "Copied: $source -> $destination" -ForegroundColor Green
        
        # Create backup of original
        $backupPath = "$source.bak"
        Copy-Item -Path $source -Destination $backupPath -Force
        Write-Host "Created backup: $backupPath" -ForegroundColor Yellow
        
        # Encrypt file if requested
        if ($Encrypt) {
            # Check if we have Python encryption utilities
            Push-Location backend
            $canEncrypt = $false
            try {
                $pythonTest = python -c "import sys; sys.path.insert(0, '.'); from app.core.security import encrypt_file, decrypt_file; print('ok')" 2>&1
                if ($pythonTest -eq "ok") {
                    $canEncrypt = $true
                }
            } catch {
                $canEncrypt = $false
            }
            Pop-Location
            
            if ($canEncrypt) {
                Write-Host "Encrypting file: $destination" -ForegroundColor Yellow
                
                # Use our Python encryption module
                Push-Location backend
                $encryptCode = @"
import sys
import json
sys.path.insert(0, '.')
try:
    from app.core.security import encrypt_file
    
    # Read the source file
    with open('$($destination -replace '\\', '\\\\')') as f:
        data = json.load(f)
    
    # Encrypt and write to same file
    encrypt_file('$($destination -replace '\\', '\\\\'))', data)
    print('File encrypted successfully')
except Exception as e:
    print(f'Error encrypting file: {str(e)}')
    import traceback
    traceback.print_exc()
"@
                # Save to temp file and run
                $tempFile = "temp_encrypt.py"
                Set-Content -Path $tempFile -Value $encryptCode
                python $tempFile
                Remove-Item $tempFile -Force
                Pop-Location
                
                Write-Host "Encryption complete" -ForegroundColor Green
            } else {
                Write-Host "Skipping encryption - Python encryption utilities not available" -ForegroundColor Yellow
                Write-Host "Run scripts\setup-encryption.ps1 first to set up encryption" -ForegroundColor Yellow
            }
        }
        
        $migratedCount++
    }
}

# Update .env file to point to new locations
$envFile = "backend\.env"
if (Test-Path $envFile) {
    Write-Host "`nUpdating .env file with new credential paths..." -ForegroundColor Yellow
    
    $envContent = Get-Content $envFile -Raw
    if (-not $envContent) { $envContent = "" }
    
    # Define paths to update in .env file
    $pathUpdates = @{
        "GMAIL_API_TOKEN_FILE" = "$($SecureRoot -replace '\\', '/')/tokens/gmail_token.json"
        "GMAIL_API_CREDENTIALS_FILE" = "$($SecureRoot -replace '\\', '/')/credentials/gmail_credentials.json"
    }
    
    # Update .env file
    foreach ($key in $pathUpdates.Keys) {
        $value = $pathUpdates[$key]
        $pattern = "^$key=.*$"
        
        if ($envContent -match $pattern) {
            $envContent = $envContent -replace $pattern, "$key=$value"
        } else {
            $envContent += "`n$key=$value"
        }
    }
    
    # Save updated .env file
    Set-Content -Path $envFile -Value $envContent
    Write-Host "Updated .env file with secure paths" -ForegroundColor Green
}

# Summary
Write-Host "`n===== Migration Summary =====" -ForegroundColor Cyan
if ($migratedCount -gt 0) {
    Write-Host "$migratedCount credential files migrated to secure location" -ForegroundColor Green
    Write-Host "Secure location: $SecureRoot" -ForegroundColor Green
    
    # Provide next steps
    Write-Host "`nNext steps:" -ForegroundColor Yellow
    Write-Host "1. Update your application to use the new secure locations" -ForegroundColor White
    Write-Host "2. Once confirmed working, delete the original credential files" -ForegroundColor White
    Write-Host "   (Backups with .bak extension were created for safety)" -ForegroundColor White
} else {
    Write-Host "No credential files found to migrate" -ForegroundColor Yellow
    Write-Host "Check that the credential files exist in the expected locations:" -ForegroundColor Yellow
    foreach ($source in $credentialPairs.Keys) {
        Write-Host "- $source" -ForegroundColor White
    }
}
Write-Host "=========================" -ForegroundColor Cyan 