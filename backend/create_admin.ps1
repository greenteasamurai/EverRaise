# PowerShell script to create admin user
Write-Host "Creating admin user for EverRaise..." -ForegroundColor Green

# Activate virtual environment if it exists
if (Test-Path "venv\Scripts\Activate.ps1") {
    . .\venv\Scripts\Activate.ps1
    Write-Host "Activated virtual environment" -ForegroundColor Cyan
}

# Run the Python script
python create_admin.py

# Check if the script ran successfully
if ($LASTEXITCODE -eq 0) {
    Write-Host "Admin user created successfully!" -ForegroundColor Green
    Write-Host "You can now log in with:"
    Write-Host "  Email: admin@example.com"
    Write-Host "  Password: adminpassword"
} else {
    Write-Host "Failed to create admin user. Check the error messages above." -ForegroundColor Red
}

# Pause to keep the window open
Write-Host "Press any key to continue..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") 