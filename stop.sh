#!/bin/bash

# Urban Mobility Scenario Explorer - Stop Script
# This script stops the Streamlit dashboard and Prefect server

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${YELLOW}🛑 Stopping Urban Mobility Scenario Explorer Services...${NC}\n"

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ Error: docker-compose is not installed${NC}"
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}❌ Error: docker-compose.yml not found${NC}"
    exit 1
fi

# Stop services with Docker Compose
echo -e "${YELLOW}Stopping Docker Compose services...${NC}"
if docker-compose down; then
    echo -e "${GREEN}✅ Services stopped successfully!${NC}"
else
    echo -e "${RED}❌ Error: Failed to stop services${NC}"
    exit 1
fi

echo ""
