#!/bin/bash

# Urban Mobility Scenario Explorer - Start Script
# This script starts the Streamlit dashboard and Prefect server

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Urban Mobility Scenario Explorer Services...${NC}\n"

# Function to check if a command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check if Docker is available and being used
USE_DOCKER=false
if [ -f "Dockerfile" ]; then
    if command_exists docker; then
        echo -e "${YELLOW}Docker detected. Use Docker? (y/n)${NC}"
        read -r response
        if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
            USE_DOCKER=true
        fi
    fi
fi

if [ "$USE_DOCKER" = true ]; then
    echo -e "${BLUE}🐳 Starting services with Docker...${NC}"
    
    # Build the Docker image if it doesn't exist
    echo -e "${YELLOW}Building Docker image...${NC}"
    docker build -t urban-mobility-explorer .
    
    # Start the services in a container
    echo -e "${GREEN}Starting container...${NC}"
    docker run -d \
        --name urban-mobility-explorer \
        -p 8501:8501 \
        -v "$(pwd)/data:/app/data" \
        urban-mobility-explorer \
        streamlit run dashboard/app.py --server.port=8501 --server.address=0.0.0.0
    
    echo -e "${GREEN}✅ Services started in Docker container!${NC}"
    echo -e "${BLUE}📊 Dashboard: http://localhost:8501${NC}"
    echo -e "${YELLOW}To view logs: docker logs -f urban-mobility-explorer${NC}"
    echo -e "${YELLOW}To stop: ./stop.sh${NC}"
else
    # Start services without Docker
    echo -e "${BLUE}🐍 Starting services with Python...${NC}"
    
    # Check if virtual environment exists
    if [ ! -d "venv" ]; then
        echo -e "${YELLOW}Creating virtual environment...${NC}"
        python3 -m venv venv
    fi
    
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
    
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
    
    # Start Prefect server in background (optional)
    echo -e "${GREEN}Starting Prefect server...${NC}"
    prefect server start > prefect.log 2>&1 &
    echo $! > prefect.pid
    
    # Wait a moment for Prefect to start
    sleep 2
    
    # Start Streamlit dashboard
    echo -e "${GREEN}Starting Streamlit dashboard...${NC}"
    streamlit run dashboard/app.py --server.port=8501 > streamlit.log 2>&1 &
    echo $! > streamlit.pid
    
    echo -e "${GREEN}✅ Services started!${NC}"
    echo -e "${BLUE}📊 Dashboard: http://localhost:8501${NC}"
    echo -e "${BLUE}🔧 Prefect UI: http://localhost:4200${NC}"
    echo -e "${YELLOW}To stop: ./stop.sh${NC}"
fi

echo ""
