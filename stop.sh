#!/bin/bash

# Urban Mobility Scenario Explorer - Stop Script
# This script stops the Streamlit dashboard and Prefect server

set -e

# Colors for output
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Stopping Urban Mobility Scenario Explorer Services...${NC}\n"

# Check if Docker container is running
if command -v docker >/dev/null 2>&1; then
    if docker ps | grep -q urban-mobility-explorer; then
        echo -e "${YELLOW}Stopping Docker container...${NC}"
        docker stop urban-mobility-explorer
        docker rm urban-mobility-explorer
        echo -e "${GREEN}✅ Docker container stopped and removed${NC}"
    fi
fi

# Stop processes using PID files
if [ -f streamlit.pid ]; then
    PID=$(cat streamlit.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping Streamlit (PID: $PID)...${NC}"
        kill $PID
        echo -e "${GREEN}✅ Streamlit stopped${NC}"
    fi
    rm streamlit.pid
fi

if [ -f prefect.pid ]; then
    PID=$(cat prefect.pid)
    if ps -p $PID > /dev/null 2>&1; then
        echo -e "${YELLOW}Stopping Prefect (PID: $PID)...${NC}"
        kill $PID
        echo -e "${GREEN}✅ Prefect stopped${NC}"
    fi
    rm prefect.pid
fi

# Kill any remaining processes on the ports
if command -v lsof >/dev/null 2>&1; then
    # Kill process on port 8501 (Streamlit)
    lsof -ti:8501 | xargs kill -9 2>/dev/null && echo -e "${GREEN}✅ Port 8501 cleared${NC}" || true
    
    # Kill process on port 4200 (Prefect)
    lsof -ti:4200 | xargs kill -9 2>/dev/null && echo -e "${GREEN}✅ Port 4200 cleared${NC}" || true
fi

# Clean up log files
[ -f streamlit.log ] && rm streamlit.log
[ -f prefect.log ] && rm prefect.log

echo -e "${GREEN}✅ All services stopped successfully!${NC}"
echo ""
