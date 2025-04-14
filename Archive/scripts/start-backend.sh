#!/bin/bash
# Script to start the EverRaise backend server

# Colors for terminal output
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
CYAN='\033[36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Starting EverRaise Backend Server...${NC}"

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed or not in PATH!${NC}"
    echo -e "${RED}Please install Python 3.8 or later.${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo -e "${GREEN}Found Python $PYTHON_VERSION${NC}"

PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}Python version $PYTHON_VERSION is too old. Please upgrade to Python 3.8 or later.${NC}"
    exit 1
fi

# Check if pip is installed
if ! command -v pip3 &> /dev/null; then
    echo -e "${RED}pip3 is not available. Please make sure it's installed with Python.${NC}"
    echo -e "${YELLOW}Try: python3 -m ensurepip --upgrade${NC}"
    exit 1
fi

# Check version of pip
PIP_VERSION=$(pip3 --version | awk '{print $2}')
echo -e "${GREEN}Found pip $PIP_VERSION${NC}"

# Navigate to the backend directory
cd "$(dirname "$0")/backend" || { 
    echo -e "${RED}Failed to navigate to backend directory. Does it exist?${NC}" 
    exit 1
}

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo -e "${RED}requirements.txt not found in backend directory!${NC}"
    exit 1
fi

# Check if .env file exists, if not copy from .env.example
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo -e "${YELLOW}No .env file found. Creating from .env.example...${NC}"
        cp .env.example .env
        echo -e "${YELLOW}Created .env file. Please update it with your configuration values.${NC}"
    else
        echo -e "${YELLOW}Neither .env nor .env.example found. Creating default .env file...${NC}"
        cat > .env << EOF
# EverRaise Backend Environment Variables
DATABASE_URL=sqlite:///./everraise.db
SECRET_KEY=changethissecretkey
DEBUG=True
EOF
        echo -e "${YELLOW}Created default .env file. Please update it with your configuration values.${NC}"
    fi
fi

# Try to activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    echo -e "${CYAN}Activating virtual environment...${NC}"
    source venv/bin/activate
else
    echo -e "${YELLOW}No virtual environment found.${NC}"
    read -p "Would you like to create a virtual environment? (y/n) " CREATE_VENV
    if [[ $CREATE_VENV == "y" ]]; then
        echo -e "${CYAN}Creating virtual environment...${NC}"
        python3 -m venv venv
        if [ $? -ne 0 ]; then
            echo -e "${YELLOW}Failed to create virtual environment. Continuing with system Python.${NC}"
        else
            source venv/bin/activate
        fi
    else
        echo -e "${YELLOW}Continuing with system Python.${NC}"
    fi
fi

# Check if requirements are installed
echo -e "${CYAN}Checking dependencies...${NC}"
MISSING_PACKAGES=0

# Define required packages
REQUIRED_PACKAGES=("fastapi" "uvicorn" "sqlalchemy" "pydantic")

for package in "${REQUIRED_PACKAGES[@]}"; do
    python3 -c "import $package" 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${YELLOW}Package $package not found.${NC}"
        MISSING_PACKAGES=1
    fi
done

if [ $MISSING_PACKAGES -eq 1 ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip3 install -r requirements.txt
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install dependencies. Exiting.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Dependencies installed successfully.${NC}"
else
    echo -e "${GREEN}All required packages are installed.${NC}"
fi

# Check if port 8000 is already in use
PORT_CHECK=0
if command -v nc &> /dev/null; then
    nc -z localhost 8000 &>/dev/null && PORT_CHECK=1
elif command -v lsof &> /dev/null; then
    lsof -i :8000 &>/dev/null && PORT_CHECK=1
fi

if [ $PORT_CHECK -eq 1 ]; then
    echo -e "${YELLOW}Warning: Port 8000 is already in use by another process.${NC}"
    echo -e "${YELLOW}You may need to close that process or change the port.${NC}"
fi

# Start the backend server
echo -e "${GREEN}Starting backend server with uvicorn...${NC}"
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Navigate back to the original directory (this will only execute if uvicorn is stopped)
cd - > /dev/null 