#!/bin/bash

# Urban Mobility Scenario Explorer - Pipeline Runner
# This script runs different pipeline options

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Urban Mobility Pipeline Runner${NC}\n"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Error: Python 3 is not installed${NC}"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies if needed
if ! python -c "import prefect" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    pip install -q --upgrade pip
    pip install -q -r requirements.txt
fi

# Show menu
echo -e "${BLUE}Available pipelines:${NC}"
echo "  1) Simple Pipeline (sample data, no external downloads)"
echo "  2) Basic Pipeline (real OSM + GTFS data)"
echo "  3) Enhanced Pipeline (full ETL with OSM + GTFS + Census)"
echo ""
read -p "Select pipeline (1-3): " choice

case $choice in
    1)
        echo -e "${GREEN}Running Simple Pipeline...${NC}"
        python src/simple_pipeline.py
        ;;
    2)
        echo -e "${GREEN}Running Basic Pipeline...${NC}"
        python src/pipeline.py
        ;;
    3)
        echo -e "${GREEN}Running Enhanced Pipeline...${NC}"
        echo -e "${YELLOW}Note: This may take longer and requires external data sources${NC}"
        python src/enhanced_pipeline.py
        ;;
    *)
        echo -e "${RED}Invalid choice${NC}"
        exit 1
        ;;
esac

echo -e "${GREEN}✅ Pipeline completed!${NC}"
