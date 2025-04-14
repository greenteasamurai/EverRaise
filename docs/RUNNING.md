# Running EverRaise Application

This document explains how to run the EverRaise application in different ways, handling common issues.

## Common Issues

1. **Port 8000 Already In Use**
   - The most common error is when port 8000 is already in use by another application
   - This will show as `[Errno 10048] error while attempting to bind on address ('0.0.0.0', 8000): only one usage of each socket address...`
   - Use our new `fix-issues.ps1` script to handle this automatically (see below)

2. **PowerShell Command Syntax**
   - Don't use `&&` in PowerShell - it's not a valid command separator
   - Use semicolons (`;`) instead, or run our helper scripts
   - Example: `cd .\backend; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000`

3. **Database Relationship Errors**
   - If you see errors about missing tables or foreign key relationships, the database may need to be reset
   - Our new `fix-issues.ps1` script can help with database issues

## Option 1: Using the Issue Fixer Script (RECOMMENDED)

We've created a new script to diagnose and fix common issues:

```powershell
.\fix-issues.ps1
```

This interactive menu-driven script can:
- Check for and fix port 8000 conflicts
- Back up or reset the database
- Start both servers correctly in separate windows
- Fix everything in one go

## Option 2: Using the Menu Script

For general management of the application:

```powershell
.\run-commands.ps1
```

This will show a menu with options to:
- Start backend server
- Start frontend server
- Start both servers
- Check port status
- Kill processes using port 8000

## Option 3: Using the Automated Script

Run the automated script to start both backend and frontend:

```powershell
.\run-everraise.ps1
```

This script will:
- Check if port 8000 is already in use and offer options
- Start the backend server
- Start the frontend server
- Monitor both processes

## Option 4: Starting Servers Manually

To start the backend server:

```powershell
cd .\backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

To start the frontend server (in a separate terminal):

```powershell
cd .\frontend
npm run dev
```

## Fixing Port Usage Issues

### Check if port 8000 is already in use:

```powershell
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
```

### Kill the process using port 8000:

```powershell
$conn = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($conn) {
    $process = Get-Process -Id $conn.OwningProcess -ErrorAction SilentlyContinue
    Stop-Process -Id $process.Id -Force
}
```

## Fixing Database Issues

If you encounter database relationship errors:

```powershell
# Back up existing database
cd .\backend
Copy-Item everraise.db everraise.db.backup -Force

# Remove database to start fresh
Rename-Item everraise.db everraise.db.old -Force
```

Then restart the application. A new database will be created automatically.

## Troubleshooting

If you continue to have issues:

1. **Backend fails to start**
   - Run `.\fix-issues.ps1` and select option 1 to kill processes using port 8000
   - Try running the backend directly with: `cd .\backend; python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --log-level debug`

2. **Frontend fails to connect to backend**
   - Make sure the backend is running first and not showing errors
   - The frontend should show a red warning indicator if the backend is offline

3. **Database errors**
   - Run `.\fix-issues.ps1` and select option 2 to fix database issues
   - If you see errors about missing tables, select "Remove" to start with a fresh database 