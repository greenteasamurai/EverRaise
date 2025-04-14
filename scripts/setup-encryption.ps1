# Setup encryption utilities for secure credential management
# Usage: .\scripts\setup-encryption.ps1 -SecureRoot C:\EverRaise-Secure

param(
    [string]$SecureRoot = "C:\EverRaise-Secure",
    [switch]$Force = $false,
    [switch]$AddToPython = $true
)

$ErrorActionPreference = "Stop"

# Banner
Write-Host "===== EverRaise Encryption Setup =====" -ForegroundColor Cyan
Write-Host "Setting up encryption for secure credential management" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan

# Create encryption directory
$encryptionDir = "$SecureRoot\encryption"
if (-not (Test-Path $encryptionDir)) {
    Write-Host "Creating encryption directory: $encryptionDir" -ForegroundColor Yellow
    New-Item -Path $encryptionDir -ItemType Directory -Force | Out-Null
}

# Generate master encryption key if it doesn't exist
$keyPath = "$encryptionDir\master.key"
if (-not (Test-Path $keyPath) -or $Force) {
    Write-Host "Generating new master encryption key..." -ForegroundColor Yellow
    $key = [Convert]::ToBase64String([System.Security.Cryptography.RandomNumberGenerator]::GetBytes(32))
    Set-Content -Path $keyPath -Value $key -Force
    Write-Host "✅ Created encryption key at: $keyPath" -ForegroundColor Green
} else {
    Write-Host "✅ Encryption key already exists at: $keyPath" -ForegroundColor Green
}

# Check for Python cryptography package
Write-Host "Checking for Python cryptography package..." -ForegroundColor Yellow
$pythonResult = $null
try {
    $pythonResult = python -c "import cryptography; print('Cryptography package installed')" 2>&1
    Write-Host "✅ $pythonResult" -ForegroundColor Green
} catch {
    Write-Host "❌ Python cryptography package not found" -ForegroundColor Red
    $installPackage = Read-Host "Do you want to install the cryptography package? (y/n)"
    if ($installPackage -eq "y") {
        Write-Host "Installing cryptography package..." -ForegroundColor Yellow
        python -m pip install cryptography
        if ($LASTEXITCODE -eq 0) {
            Write-Host "✅ Cryptography package installed successfully" -ForegroundColor Green
        } else {
            Write-Host "❌ Failed to install cryptography package" -ForegroundColor Red
        }
    }
}

# Create security utility file if AddToPython is set
if ($AddToPython) {
    $securityUtilPath = "backend\app\core\security.py"
    
    # Check if file exists already
    $createNewFile = $true
    if (Test-Path $securityUtilPath) {
        $overwrite = Read-Host "Security utility file already exists. Overwrite? (y/n)"
        $createNewFile = ($overwrite -eq "y")
    }
    
    if ($createNewFile) {
        Write-Host "Creating security utility file: $securityUtilPath" -ForegroundColor Yellow
        $securityUtil = @"
"""
Encryption utilities for secure credential management.
This file provides methods to encrypt and decrypt sensitive data like API tokens.
"""
import os
import json
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from app.core.config import settings

def get_encryption_key():
    """Get or create an encryption key for sensitive data."""
    key_path = os.getenv("ENCRYPTION_KEY_PATH", "$($SecureRoot -replace '\\', '/')/encryption/master.key")
    
    try:
        with open(key_path, "r") as f:
            key = f.read().strip()
            return key.encode()
    except:
        # Generate a key if no key exists (first run)
        salt = os.urandom(16)
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(os.urandom(32)))
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(key_path), exist_ok=True)
        
        # Save key and salt
        with open(key_path, "wb") as f:
            f.write(key)
        with open(f"{os.path.dirname(key_path)}/salt.bin", "wb") as f:
            f.write(salt)
            
        return key

def encrypt_file(file_path, data):
    """Encrypt data and save to file."""
    key = get_encryption_key()
    f = Fernet(key)
    encrypted_data = f.encrypt(json.dumps(data).encode())
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    with open(file_path, "wb") as file:
        file.write(encrypted_data)

def decrypt_file(file_path):
    """Decrypt data from file."""
    key = get_encryption_key()
    f = Fernet(key)
    
    with open(file_path, "rb") as file:
        encrypted_data = file.read()
    
    decrypted_data = f.decrypt(encrypted_data)
    return json.loads(decrypted_data.decode())

def encrypt_text(text):
    """Encrypt a text string."""
    key = get_encryption_key()
    f = Fernet(key)
    return f.encrypt(text.encode()).decode()

def decrypt_text(encrypted_text):
    """Decrypt a text string."""
    key = get_encryption_key()
    f = Fernet(key)
    return f.decrypt(encrypted_text.encode()).decode()
"@
        # Ensure directory exists
        $securityDir = Split-Path -Parent $securityUtilPath
        if (-not (Test-Path $securityDir)) {
            New-Item -Path $securityDir -ItemType Directory -Force | Out-Null
        }
        
        Set-Content -Path $securityUtilPath -Value $securityUtil
        Write-Host "✅ Created security utility file: $securityUtilPath" -ForegroundColor Green
    } else {
        Write-Host "Skipped creating security utility file" -ForegroundColor Yellow
    }
}

# Create encryption test script
$testScriptPath = "scripts\test-encryption.ps1"
Write-Host "Creating encryption test script: $testScriptPath" -ForegroundColor Yellow
$testScript = @"
# Test the encryption utilities
# Usage: .\scripts\test-encryption.ps1

param(
    [string]`$MessageToEncrypt = "This is a test message",
    [string]`$TestFilePath = "encryption_test.json",
    [switch]`$Cleanup = `$true
)

`$ErrorActionPreference = "Stop"

# Banner
Write-Host "===== EverRaise Encryption Test =====" -ForegroundColor Cyan
Write-Host "Testing encryption utilities" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan

# Change to backend directory
Push-Location backend

# Activate virtual environment if exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "Activating virtual environment..." -ForegroundColor Yellow
    . .\venv\Scripts\Activate.ps1
}

# Run Python encryption test
Write-Host "`nRunning encryption test..." -ForegroundColor Yellow
`$pythonCode = @"
import os
import sys
import json
import traceback

# Add project directory to path
sys.path.insert(0, os.path.abspath(os.curdir))

try:
    from app.core.security import encrypt_file, decrypt_file, encrypt_text, decrypt_text
    
    # Test text encryption
    message = '$MessageToEncrypt'
    print(f"Original message: {message}")
    
    encrypted = encrypt_text(message)
    print(f"Encrypted: {encrypted}")
    
    decrypted = decrypt_text(encrypted)
    print(f"Decrypted: {decrypted}")
    
    if message == decrypted:
        print("✅ Text encryption test passed!")
    else:
        print("❌ Text encryption test failed!")
    
    # Test file encryption
    test_data = {
        "test_key": "test_value",
        "nested": {
            "key": "value"
        },
        "array": [1, 2, 3]
    }
    
    # Encrypt and save to file
    encrypt_file('$TestFilePath', test_data)
    print(f"Data encrypted and saved to {os.path.abspath('$TestFilePath')}")
    
    # Decrypt from file
    decrypted_data = decrypt_file('$TestFilePath')
    print(f"Decrypted data: {json.dumps(decrypted_data, indent=2)}")
    
    if test_data == decrypted_data:
        print("✅ File encryption test passed!")
    else:
        print("❌ File encryption test failed!")
        
except Exception as e:
    print(f"❌ Error: {str(e)}")
    traceback.print_exc()
"@

# Save Python code to temporary file
`$tempFile = "temp_test.py"
Set-Content -Path `$tempFile -Value `$pythonCode

# Run Python script
python `$tempFile

# Clean up
if (`$Cleanup) {
    Write-Host "`nCleaning up test files..." -ForegroundColor Yellow
    if (Test-Path `$tempFile) { Remove-Item `$tempFile }
    if (Test-Path `$TestFilePath) { Remove-Item `$TestFilePath }
}

# Return to original directory
Pop-Location

Write-Host "`n===== Test Complete =====" -ForegroundColor Cyan
"@

Set-Content -Path $testScriptPath -Value $testScript
Write-Host "✅ Created encryption test script: $testScriptPath" -ForegroundColor Green

# Create update-secure-paths script
$updatePathsScript = "scripts\update-secure-paths.ps1"
Write-Host "Creating update-secure-paths script: $updatePathsScript" -ForegroundColor Yellow
$updateScript = @"
# Update application configuration to use secure paths
# Usage: .\scripts\update-secure-paths.ps1

param(
    [string]`$SecureRoot = "C:\EverRaise-Secure",
    [string]`$EnvFile = "backend\.env"
)

`$ErrorActionPreference = "Stop"

# Banner
Write-Host "===== Update Secure Paths =====" -ForegroundColor Cyan
Write-Host "Updating application to use secure credential paths" -ForegroundColor Cyan
Write-Host "================================" -ForegroundColor Cyan

# Check if .env file exists
if (-not (Test-Path `$EnvFile)) {
    Write-Host "❌ Error: .env file not found at `$EnvFile" -ForegroundColor Red
    `$createEnv = Read-Host "Create new .env file? (y/n)"
    if (`$createEnv -eq "y") {
        # Create from example if available
        if (Test-Path "`$EnvFile.example") {
            Copy-Item "`$EnvFile.example" -Destination `$EnvFile
            Write-Host "Created .env from example file" -ForegroundColor Green
        } else {
            # Create empty .env file
            New-Item -Path `$EnvFile -ItemType File -Force | Out-Null
            Write-Host "Created empty .env file" -ForegroundColor Green
        }
    } else {
        Write-Host "Exiting script, please create .env file manually." -ForegroundColor Yellow
        exit 1
    }
}

# Read current .env file
`$envContent = Get-Content `$EnvFile -Raw
if (-not `$envContent) { `$envContent = "" }

# Update paths to use secure location
`$securePathUpdates = @{
    "ENCRYPTION_KEY_PATH" = "$(`$SecureRoot -replace '\\', '/')/encryption/master.key"
    "GMAIL_API_TOKEN_FILE" = "$(`$SecureRoot -replace '\\', '/')/tokens/gmail_token.json"
    "GMAIL_API_CREDENTIALS_FILE" = "$(`$SecureRoot -replace '\\', '/')/credentials/gmail_credentials.json"
}

foreach (`$key in `$securePathUpdates.Keys) {
    `$value = `$securePathUpdates[`$key]
    `$pattern = "^`$key=.*`$"
    
    if (`$envContent -match `$pattern) {
        Write-Host "Updating `$key in .env file" -ForegroundColor Yellow
        `$envContent = `$envContent -replace `$pattern, "`$key=`$value"
    } else {
        Write-Host "Adding `$key to .env file" -ForegroundColor Yellow
        `$envContent += "`n`$key=`$value"
    }
}

# Save updated .env file
Set-Content -Path `$EnvFile -Value `$envContent
Write-Host "✅ Updated .env file with secure paths" -ForegroundColor Green

# Verify paths exist
foreach (`$path in `$securePathUpdates.Values) {
    `$windowsPath = `$path -replace '/', '\'
    `$dirPath = Split-Path -Parent `$windowsPath
    
    if (-not (Test-Path `$dirPath)) {
        Write-Host "Creating directory: `$dirPath" -ForegroundColor Yellow
        New-Item -Path `$dirPath -ItemType Directory -Force | Out-Null
    }
}

Write-Host "`nPath updates complete!" -ForegroundColor Cyan
Write-Host "Secure root: `$SecureRoot" -ForegroundColor Cyan
"@

Set-Content -Path $updatePathsScript -Value $updateScript
Write-Host "✅ Created update-secure-paths script: $updatePathsScript" -ForegroundColor Green

# Final instructions
Write-Host "`n===== Setup Complete =====" -ForegroundColor Cyan
Write-Host "Next steps:" -ForegroundColor White
Write-Host "1. Run the update-secure-paths script to configure your application:" -ForegroundColor White
Write-Host "   .\scripts\update-secure-paths.ps1" -ForegroundColor Yellow
Write-Host "2. Test the encryption functionality:" -ForegroundColor White
Write-Host "   .\scripts\test-encryption.ps1" -ForegroundColor Yellow
Write-Host "3. Migrate any existing credentials:" -ForegroundColor White
Write-Host "   .\scripts\migrate-credentials.ps1" -ForegroundColor Yellow
Write-Host "=====================" -ForegroundColor Cyan 