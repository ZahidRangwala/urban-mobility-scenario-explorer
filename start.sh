#!/bin/bash

# Urban Mobility Scenario Explorer - Start Script
# This script starts the Streamlit dashboard using Docker Compose (recommended) or Python

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

# Check if Docker Compose is available
USE_COMPOSE=false
if command_exists docker && command_exists docker-compose; then
    USE_COMPOSE=true
fi

if [ "$USE_COMPOSE" = true ]; then
    echo -e "${BLUE}🐳 Starting services with Docker Compose...${NC}"
    
    # Check if docker-compose.yml exists
    if [ -f "docker-compose.yml" ]; then
        docker-compose up -d --build
        
        echo -e "${GREEN}✅ Services started with Docker Compose!${NC}"
        echo -e "${BLUE}📊 Dashboard: http://localhost:8501${NC}"
        echo -e "${YELLOW}To view logs: docker-compose logs -f${NC}"
        echo -e "${YELLOW}To stop: ./stop.sh or docker-compose down${NC}"
        echo -e "${YELLOW}To restart: docker-compose restart${NC}"
    else
        echo -e "${YELLOW}docker-compose.yml not found, falling back to regular Docker...${NC}"
        USE_COMPOSE=false
    fi
fi

if [ "$USE_COMPOSE" = false ]; then
    # Fallback to regular Docker
    if command_exists docker; then
        echo -e "${BLUE}🐳 Starting services with Docker...${NC}"
        
        # Check if container already exists
        if docker ps -a --format '{{.Names}}' | grep -q "^urban-mobility-dashboard$"; then
            echo -e "${YELLOW}Container exists, starting it...${NC}"
            docker start urban-mobility-dashboard
        else
            echo -e "${YELLOW}Building Docker image...${NC}"
            docker build -t urban-mobility-explorer .
            
            echo -e "${GREEN}Starting container...${NC}"
            docker run -d \
                --name urban-mobility-dashboard \
                -p 8501:8501 \
                -v "$(pwd)/data:/app/data" \
                -v "$(pwd)/cache:/app/cache" \
                --restart unless-stopped \
                urban-mobility-explorer
        fi
        
        echo -e "${GREEN}✅ Services started in Docker container!${NC}"
        echo -e "${BLUE}📊 Dashboard: http://localhost:8501${NC}"
        echo -e "${YELLOW}To view logs: docker logs -f urban-mobility-dashboard${NC}"
        echo -e "${YELLOW}To stop: ./stop.sh or docker stop urban-mobility-dashboard${NC}"
    else
        # Fallback to Python
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
        
        # Start Streamlit dashboard
        echo -e "${GREEN}Starting Streamlit dashboard...${NC}"
        nohup streamlit run dashboard/app.py --server.port=8501 > streamlit.log 2>&1 &
        echo $! > streamlit.pid
        
        echo -e "${GREEN}✅ Services started!${NC}"
        echo -e "${BLUE}📊 Dashboard: http://localhost:8501${NC}"
        echo -e "${YELLOW}To stop: ./stop.sh${NC}"
    fi
fi

echo ""
