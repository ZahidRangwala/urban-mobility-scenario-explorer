#!/bin/bash

# Urban Mobility Scenario Explorer - Start Script
# This script starts the Streamlit dashboard using Docker Compose

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting Urban Mobility Scenario Explorer Services...${NC}\n"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Error: Docker is not installed${NC}"
    echo -e "${YELLOW}Please install Docker: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Error: docker-compose is not installed${NC}"
    echo -e "${YELLOW}Please install docker-compose: https://docs.docker.com/compose/install/${NC}"
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.yml not found${NC}"
    exit 1
fi

# Check if Docker daemon is running
if ! docker info &> /dev/null; then
    echo -e "${RED}❌ Error: Docker daemon is not running${NC}"
    echo -e "${YELLOW}Please start Docker and try again${NC}"
    exit 1
fi

# Start services with Docker Compose
echo -e "${BLUE}🐳 Starting services with Docker Compose...${NC}"
if docker-compose up -d --build; then
    echo -e "${GREEN}✅ Services started successfully!${NC}"
    echo -e "${BLUE}📊 Dashboard: http://localhost:8501${NC}"
    echo -e "${YELLOW}To view logs: docker-compose logs -f${NC}"
    echo -e "${YELLOW}To stop: ./stop.sh or docker-compose down${NC}"
    echo -e "${YELLOW}To restart: ./restart.sh or docker-compose restart${NC}"
else
    echo -e "${RED}❌ Error: Failed to start services${NC}"
    exit 1
fi

echo ""
