#!/bin/bash
# Script to start both the backend and frontend servers for EverRaise

# Colors for terminal output
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
CYAN='\033[36m'
MAGENTA='\033[35m'
NC='\033[0m' # No Color

echo -e "${GREEN}Starting EverRaise Application...${NC}"
echo -e "${GREEN}=====================================${NC}"

# Set script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" &>/dev/null && pwd)"

# Check if necessary scripts exist
if [ ! -f "$SCRIPT_DIR/start-backend.sh" ]; then
    echo -e "${RED}Error: start-backend.sh not found!${NC}"
    exit 1
fi

if [ ! -f "$SCRIPT_DIR/start-frontend.sh" ]; then
    echo -e "${RED}Error: start-frontend.sh not found!${NC}"
    exit 1
fi

# Make sure scripts are executable
chmod +x "$SCRIPT_DIR/start-backend.sh" "$SCRIPT_DIR/start-frontend.sh"

# Check if backend and frontend directories exist
if [ ! -d "$SCRIPT_DIR/backend" ]; then
    echo -e "${RED}Error: Backend directory not found!${NC}"
    exit 1
fi

if [ ! -d "$SCRIPT_DIR/frontend" ]; then
    echo -e "${RED}Error: Frontend directory not found!${NC}"
    exit 1
fi

# Function to check if a port is in use
check_port() {
    local port=$1
    local in_use=0
    
    if command -v nc >/dev/null 2>&1; then
        nc -z localhost "$port" >/dev/null 2>&1 && in_use=1
    elif command -v lsof >/dev/null 2>&1; then
        lsof -i :"$port" >/dev/null 2>&1 && in_use=1
    else
        # Fallback to a simple check using /dev/tcp (works on many Linux systems)
        (echo > /dev/tcp/localhost/"$port") >/dev/null 2>&1 && in_use=1
    fi
    
    return $in_use
}

# Check if backend port is already in use
if check_port 8000; then
    echo -e "${YELLOW}Warning: Port 8000 is already in use. Backend may already be running.${NC}"
    read -p "Do you want to continue anyway? (y/n) " CONTINUE
    if [[ $CONTINUE != "y" ]]; then
        echo -e "${RED}Exiting...${NC}"
        exit 0
    fi
fi

# Check if frontend port is already in use
if check_port 5173; then
    echo -e "${YELLOW}Note: Default frontend port 5173 is already in use.${NC}"
    echo -e "${YELLOW}Vite will automatically select another port.${NC}"
fi

# Start the backend in a new terminal window
echo -e "${CYAN}Starting backend server...${NC}"

# Different terminal launching commands based on OS
BACKEND_PID=0
BACKEND_STARTED=0

if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    osascript -e 'tell app "Terminal" to do script "'"cd '$SCRIPT_DIR' && ./start-backend.sh"'"'
    BACKEND_STARTED=1
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux - check for common terminal emulators
    if command -v gnome-terminal >/dev/null 2>&1; then
        gnome-terminal -- bash -c "$SCRIPT_DIR/start-backend.sh; exec bash"
        BACKEND_STARTED=1
    elif command -v xterm >/dev/null 2>&1; then
        xterm -e "bash -c '$SCRIPT_DIR/start-backend.sh; exec bash'" &
        BACKEND_STARTED=1
    elif command -v konsole >/dev/null 2>&1; then
        konsole -e "bash -c '$SCRIPT_DIR/start-backend.sh; exec bash'" &
        BACKEND_STARTED=1
    else
        # Fallback - start in background
        echo -e "${YELLOW}No terminal emulator found. Starting backend in background...${NC}"
        "$SCRIPT_DIR/start-backend.sh" &
        BACKEND_PID=$!
        BACKEND_STARTED=1
    fi
else
    # Unknown OS - start in background
    echo -e "${YELLOW}Unknown OS. Starting backend in background...${NC}"
    "$SCRIPT_DIR/start-backend.sh" &
    BACKEND_PID=$!
    BACKEND_STARTED=1
fi

if [ $BACKEND_STARTED -eq 0 ]; then
    echo -e "${RED}Failed to start backend. Trying to start in background...${NC}"
    "$SCRIPT_DIR/start-backend.sh" &
    BACKEND_PID=$!
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to start backend. Exiting.${NC}"
        exit 1
    fi
fi

# Wait for the backend to initialize
echo -e "${CYAN}Waiting for backend to initialize (5 seconds)...${NC}"
sleep 5

# Check if backend is actually running
if ! check_port 8000; then
    echo -e "${YELLOW}Warning: Backend may not have started properly. Port 8000 is not in use.${NC}"
    read -p "Do you want to continue with starting the frontend? (y/n) " CONTINUE
    if [[ $CONTINUE != "y" ]]; then
        echo -e "${RED}Exiting...${NC}"
        # Kill the background process if it exists
        if [ $BACKEND_PID -ne 0 ]; then
            kill $BACKEND_PID 2>/dev/null
        fi
        exit 1
    fi
fi

# Start the frontend
echo -e "\n${MAGENTA}Starting frontend server...${NC}"
"$SCRIPT_DIR/start-frontend.sh"

# This will only execute if the frontend server stops
echo -e "${YELLOW}Frontend server stopped.${NC}"

# Check if we had started a background process
if [ $BACKEND_PID -ne 0 ]; then
    echo -e "${YELLOW}Cleaning up backend process...${NC}"
    kill $BACKEND_PID 2>/dev/null
else
    echo -e "${YELLOW}If the backend is still running in a separate terminal, you may need to close it manually.${NC}" 