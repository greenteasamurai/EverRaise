#!/bin/bash
# Script to start the EverRaise frontend server

# Colors for terminal output
RED='\033[31m'
GREEN='\033[32m'
YELLOW='\033[33m'
MAGENTA='\033[35m'
NC='\033[0m' # No Color

echo -e "${MAGENTA}Starting EverRaise Frontend Server...${NC}"

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo -e "${RED}Node.js is not installed or not in PATH!${NC}"
    echo -e "${RED}Please install Node.js 16 or later from https://nodejs.org/${NC}"
    exit 1
fi

# Check Node.js version
NODE_VERSION=$(node --version | cut -c 2-)
echo -e "${GREEN}Found Node.js $NODE_VERSION${NC}"

NODE_MAJOR=$(echo $NODE_VERSION | cut -d. -f1)
if [ "$NODE_MAJOR" -lt 16 ]; then
    echo -e "${RED}Node.js version $NODE_VERSION is too old. Please upgrade to Node.js 16 or later.${NC}"
    exit 1
fi

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo -e "${RED}npm is not available. Please make sure it's installed with Node.js.${NC}"
    exit 1
fi

# Check npm version
NPM_VERSION=$(npm --version)
echo -e "${GREEN}Found npm $NPM_VERSION${NC}"

# Navigate to the frontend directory
cd "$(dirname "$0")/frontend" || { 
    echo -e "${RED}Failed to navigate to frontend directory. Does it exist?${NC}" 
    exit 1
}

# Check if package.json exists
if [ ! -f "package.json" ]; then
    echo -e "${RED}package.json not found in frontend directory!${NC}"
    exit 1
fi

# Check for 'dev' script in package.json
if ! grep -q '"dev"' package.json; then
    echo -e "${RED}No 'dev' script found in package.json. Please check your configuration.${NC}"
    exit 1
fi

# Check if node_modules exists, if not run npm install
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Node modules not found. Installing dependencies...${NC}"
    npm install
    if [ $? -ne 0 ]; then
        echo -e "${RED}Failed to install dependencies. Exiting.${NC}"
        exit 1
    fi
    echo -e "${GREEN}Dependencies installed successfully.${NC}"
else
    # Check for outdated packages
    echo -e "${YELLOW}Checking for outdated packages...${NC}"
    OUTDATED=$(npm outdated --json 2>/dev/null)
    if [ -n "$OUTDATED" ] && [ "$OUTDATED" != "{}" ]; then
        echo -e "${YELLOW}Some packages are outdated. Consider running 'npm update'.${NC}"
    fi
fi

# Check if default port is already in use
DEFAULT_PORT=5173
PORT_CHECK=0
if command -v nc &> /dev/null; then
    nc -z localhost $DEFAULT_PORT &>/dev/null && PORT_CHECK=1
elif command -v lsof &> /dev/null; then
    lsof -i :$DEFAULT_PORT &>/dev/null && PORT_CHECK=1
fi

if [ $PORT_CHECK -eq 1 ]; then
    echo -e "${YELLOW}Note: Default port $DEFAULT_PORT is already in use. Vite will automatically use another port.${NC}"
fi

# Start the frontend development server
echo -e "${GREEN}Starting frontend development server...${NC}"
npm run dev

# This will only execute if the dev server is stopped
echo -e "${YELLOW}Frontend server stopped.${NC}"

# Navigate back to the original directory (this will only execute if the dev server is stopped)
cd - > /dev/null 