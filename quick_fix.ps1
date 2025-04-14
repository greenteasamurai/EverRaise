Write-Host "Quick Fix for Login Issues" -ForegroundColor Cyan
Write-Host "========================" -ForegroundColor Cyan
Write-Host ""

# First, let's stop any running processes
$frontendProcesses = Get-Process -Name "npm" -ErrorAction SilentlyContinue
$backendProcesses = Get-Process -Name "python" -ErrorAction SilentlyContinue

if ($frontendProcesses) {
    Write-Host "Stopping frontend processes..." -ForegroundColor Yellow
    $frontendProcesses | Stop-Process -Force
}

if ($backendProcesses) {
    Write-Host "Stopping backend processes..." -ForegroundColor Yellow
    $backendProcesses | Stop-Process -Force
}

# Small delay to ensure processes are stopped
Start-Sleep -Seconds 2

# Install required packages
Write-Host "Installing required packages..." -ForegroundColor Blue
pip install aiosqlite
pip install httpx
pip install sqlalchemy
Write-Host "Packages installed." -ForegroundColor Green

# Directly create a SQLite database file with proper permissions
Write-Host "Creating SQLite database file..." -ForegroundColor Green
$dbPath = ".\backend\everraise.db"

if (Test-Path $dbPath) {
    Write-Host "Removing existing database..." -ForegroundColor Yellow
    Remove-Item $dbPath -Force
}

# Creating an empty database file with write permissions
New-Item -Path $dbPath -ItemType File -Force
$acl = Get-Acl $dbPath
$permission = "Everyone","FullControl","Allow"
$accessRule = New-Object System.Security.AccessControl.FileSystemAccessRule $permission
$acl.SetAccessRule($accessRule)
Set-Acl $dbPath $acl

Write-Host "Created new database file with proper permissions" -ForegroundColor Green

# Create a simple schema initialization script
$initSchemaPath = ".\backend\init_schema.py"
Write-Host "Creating temporary schema initialization script..." -ForegroundColor Blue
$schemaScript = @"
import asyncio
import sqlite3
from pathlib import Path

db_path = Path(__file__).parent / "everraise.db"

async def init_schema():
    print(f"Initializing database at {db_path}")
    
    # Simple schema for SQLite
    schema = [
        '''
        CREATE TABLE IF NOT EXISTS organization (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            slug TEXT UNIQUE NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1,
            plan_tier TEXT DEFAULT 'free',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS user (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            hashed_password TEXT NOT NULL,
            first_name TEXT,
            last_name TEXT,
            is_active INTEGER DEFAULT 1,
            is_superuser INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        ''',
        '''
        CREATE TABLE IF NOT EXISTS user_organization (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            organization_id INTEGER NOT NULL,
            is_owner INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES user (id),
            FOREIGN KEY (organization_id) REFERENCES organization (id)
        )
        '''
    ]
    
    # Create admin user
    admin_user = '''
    INSERT OR IGNORE INTO organization (name, slug, description, is_active, plan_tier)
    VALUES ('Admin Organization', 'admin-org', 'Default organization for admin users', 1, 'premium');
    
    INSERT OR IGNORE INTO user (email, hashed_password, first_name, last_name, is_active, is_superuser)
    VALUES ('admin@example.com', '\$2b\$12\$T7bS2DzMXSCcCIALZGAJJeFM7hVLB0Z7SLxnT9nUtQMrne3.jqyj2', 'Admin', 'User', 1, 1);
    
    INSERT OR IGNORE INTO user_organization (user_id, organization_id, is_owner)
    SELECT u.id, o.id, 1
    FROM user u, organization o
    WHERE u.email = 'admin@example.com' AND o.slug = 'admin-org';
    '''
    
    conn = None
    try:
        conn = sqlite3.connect(str(db_path))
        cursor = conn.cursor()
        
        # Create tables
        for table_sql in schema:
            cursor.execute(table_sql)
            
        # Create admin user
        cursor.executescript(admin_user)
        
        conn.commit()
        print("Database schema created successfully!")
        return True
    except Exception as e:
        print(f"Error creating database schema: {e}")
        return False
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    asyncio.run(init_schema())
"@

Set-Content -Path $initSchemaPath -Value $schemaScript

# Run the schema initialization script
Write-Host "Initializing database schema..." -ForegroundColor Green
Set-Location -Path ".\backend"
python init_schema.py
Set-Location -Path ".."

# Start backend server with environment variable to specify database URL
Write-Host "Starting backend server..." -ForegroundColor Green
$env:DATABASE_URL = "sqlite+aiosqlite:///./everraise.db"
$backendWindow = Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "cd backend; $env:DATABASE_URL='sqlite+aiosqlite:///./everraise.db'; python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000" -PassThru

# Start frontend server
Write-Host "Starting frontend server..." -ForegroundColor Green
$frontendWindow = Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "cd frontend; npm run dev" -PassThru

# Wait a moment for servers to start
Start-Sleep -Seconds 5

# Open the login page
Write-Host "Opening login page..." -ForegroundColor Cyan
Start-Process "http://localhost:5173/login"

Write-Host "Fix script complete!" -ForegroundColor Green
Write-Host "Use these credentials to log in:" -ForegroundColor Green
Write-Host "Email: admin@example.com" -ForegroundColor Yellow
Write-Host "Password: adminpassword" -ForegroundColor Yellow
Write-Host "Note: If regular login doesn't work, use the 'Debug: Skip Login' button." -ForegroundColor Magenta
Write-Host "To stop the servers, close the terminal windows or press Ctrl+C in each one." -ForegroundColor Magenta 