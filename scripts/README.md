# EverRaise Scripts

This directory contains utility scripts to help manage the EverRaise application.

## Available Scripts

| Script | Description |
|--------|-------------|
| `start-everraise.ps1` | Master script to start both backend and frontend |
| `start-backend.ps1` | Starts the backend service only |
| `start-frontend.ps1` | Starts the frontend service only |
| `check-connection.ps1` | Checks connectivity between frontend and backend |
| `find-frontend-port.ps1` | Locates which port the Vite frontend is running on |
| `cleanup-frontend.ps1` | Kills stray Node.js processes and frees up ports |

## Common Issues & Solutions

### "Backend Offline" Warning

If you see a "Backend Offline" warning even though the backend is running:

1. The frontend might be running on a non-standard port (not port 3000)
2. There might be CORS issues preventing proper communication
3. The backend might be returning a 500 error due to database connection issues

**Solution:**
```powershell
# 1. Find which port the frontend is running on
.\scripts\find-frontend-port.ps1

# 2. Check connection with the correct port
.\scripts\check-connection.ps1 -FrontendUrl "http://localhost:XXXX"  # Replace XXXX with the port number

# 3. If needed, clean up and restart everything
.\scripts\cleanup-frontend.ps1
.\scripts\start-everraise.ps1 -CleanStart
```

### Port Conflicts

If Vite (frontend) or Uvicorn (backend) can't start due to port conflicts:

**Solution:**
```powershell
# Clean up all Node.js processes
.\scripts\cleanup-frontend.ps1
```

## Using the Master Script

The `start-everraise.ps1` script provides the most convenient way to start the application:

```powershell
# Start both backend and frontend with a clean slate
.\scripts\start-everraise.ps1 -CleanStart

# Start only the backend
.\scripts\start-everraise.ps1 -SkipFrontend

# Start only the frontend
.\scripts\start-everraise.ps1 -SkipBackend
```

## Troubleshooting

If you're having persistent issues:

1. Check that both backend and frontend dependencies are installed
2. Verify that the `.env.local` file exists in the frontend directory
3. Look for errors in the backend and frontend terminal windows
4. Try rebooting your system if port conflicts persist
5. Clear your browser cache

## Getting Help

If you continue to experience issues, run the diagnostics:

```powershell
.\scripts\check-connection.ps1 > connection-diagnostic.log
.\scripts\find-frontend-port.ps1 > port-diagnostic.log
```

Then share these log files to get help troubleshooting the issue. 