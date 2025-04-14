# EverRaise Quick Start Guide

This guide will help you quickly start the EverRaise application using the provided startup scripts.

## Prerequisites

Before running the application, ensure you have the following installed:

- **Backend**:
  - Python 3.8 or later
  - pip (Python package manager)
  
- **Frontend**:
  - Node.js 16+ and npm

## Starting the Application

### For Windows Users

Three PowerShell scripts are provided for easy startup:

1. **Start Backend Only**:
   ```powershell
   .\start-backend.ps1
   ```

2. **Start Frontend Only**:
   ```powershell
   .\start-frontend.ps1
   ```

3. **Start Both (Complete Application)**:
   ```powershell
   .\start-everraise.ps1
   ```

### For macOS/Linux Users

Three shell scripts are provided for easy startup:

1. First, make the scripts executable:
   ```bash
   chmod +x start-backend.sh start-frontend.sh start-everraise.sh
   ```

2. **Start Backend Only**:
   ```bash
   ./start-backend.sh
   ```

3. **Start Frontend Only**:
   ```bash
   ./start-frontend.sh
   ```

4. **Start Both (Complete Application)**:
   ```bash
   ./start-everraise.sh
   ```

## What the Scripts Do

### Backend Script
- Checks for Python and required dependencies
- Creates a virtual environment if not present (optional)
- Installs required Python dependencies
- Creates a `.env` file from `.env.example` if not present
- Starts the FastAPI backend with hot-reloading enabled

### Frontend Script
- Checks for Node.js and npm
- Installs npm dependencies if not already installed
- Checks for outdated packages
- Starts the Vite development server for the React frontend

### Combined Script
- Checks if key components and directories exist
- Verifies port availability
- Starts the backend server in a separate window/terminal
- Waits for the backend to initialize (5 seconds)
- Verifies the backend is actually running
- Starts the frontend in the current terminal
- Handles cleanup when the frontend stops

## Accessing the Application

Once started, you can access:

- **Backend API** at: http://localhost:8000
- **API Documentation** at: http://localhost:8000/api/docs
- **Frontend** at: http://localhost:5173 (or alternate port if 5173 is in use)

## Troubleshooting

### Common Issues & Solutions

- **"Python is not installed or not in PATH"**:
  - Install Python 3.8+ from [python.org](https://www.python.org/downloads/)
  - Make sure to check "Add Python to PATH" during installation

- **"Node.js is not installed or not in PATH"**:
  - Install Node.js 16+ from [nodejs.org](https://nodejs.org/)
  - Most installers add Node.js to PATH automatically

- **Port conflicts**:
  - Backend port 8000 conflict: Check if another application is using port 8000
  - Frontend port 5173 conflict: Vite will automatically use another port (e.g., 5174)

- **Permission issues (Unix)**: 
  - If you get permission errors, ensure the scripts are executable with `chmod +x *.sh`

- **PowerShell script execution policy**:
  - If scripts won't run, try: `Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy Bypass`

- **Missing dependencies**:
  - The scripts will attempt to install missing dependencies automatically
  - If manual installation is needed: 
    - Backend: `pip install -r backend/requirements.txt`
    - Frontend: `cd frontend && npm install`

## Configuration

For custom configuration:

- Backend: Edit the `.env` file in the `backend` directory
  - Database settings
  - Secret key and security settings
  - Debug mode toggle

- Frontend: Edit environment variables
  - `.env.local` for local overrides
  - Proxy configuration in `vite.config.js`

Happy coding! 