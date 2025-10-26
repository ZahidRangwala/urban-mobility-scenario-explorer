#!/bin/bash

# Urban Mobility Scenario Explorer - Restart Script
# This script restarts the services

# Colors for output
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🔄 Restarting Urban Mobility Scenario Explorer Services...${NC}\n"

# Stop services
./stop.sh

# Wait a moment
sleep 2

# Start services
./start.sh
