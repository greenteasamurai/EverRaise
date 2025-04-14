Write-Host "EverRaise Database Fix Script" -ForegroundColor Green
Write-Host "----------------------------" -ForegroundColor Green
Write-Host ""

# Step 1: Install required dependencies
Write-Host "Installing required packages..." -ForegroundColor Blue
pip install aiosqlite
pip install sqlalchemy
pip install alembic

# Step 2: Check for database file
$dbPath = ".\backend\everraise.db"
if (Test-Path $dbPath) {
    Write-Host "Found existing database at $dbPath" -ForegroundColor Yellow
    Write-Host "Would you like to reset the database? (y/n)" -ForegroundColor Yellow
    $response = Read-Host
    if ($response -eq "y") {
        Write-Host "Removing existing database..." -ForegroundColor Red
        Remove-Item $dbPath -Force
        Write-Host "Database removed." -ForegroundColor Green
    }
}

# Step 3: Create database
Write-Host "Creating database and tables..." -ForegroundColor Blue
Set-Location -Path ".\backend"

# Run the new standalone database initialization script
try {
    Write-Host "Running database initialization..." -ForegroundColor Cyan
    python initialize_db.py
    
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Database and tables created successfully!" -ForegroundColor Green
    } else {
        Write-Host "Failed to create database and tables." -ForegroundColor Red
    }
} catch {
    Write-Host "Error initializing database: $_" -ForegroundColor Red
    Write-Host "Trying alternative initialization method..." -ForegroundColor Yellow
    
    # Backup approach - run Python inline command
    python -c "from app.db.init_db import init_db; import asyncio; asyncio.run(init_db())"
}

# Step 4: Create admin user
Write-Host "Creating admin user..." -ForegroundColor Blue
python create_admin.py

if ($LASTEXITCODE -eq 0) {
    Write-Host "Admin user created successfully!" -ForegroundColor Green
} else {
    Write-Host "Failed to create admin user." -ForegroundColor Red
}

# Go back to root directory
Set-Location -Path ".."

# Step 5: Start services
Write-Host ""
Write-Host "Database setup complete!" -ForegroundColor Green
Write-Host "You can now start the servers with the 'fix_login.ps1' script" -ForegroundColor Cyan
Write-Host "Or use these credentials to log in:" -ForegroundColor Green
Write-Host "Email: admin@example.com" -ForegroundColor Yellow
Write-Host "Password: adminpassword" -ForegroundColor Yellow 