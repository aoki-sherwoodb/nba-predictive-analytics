#!/bin/bash
# Local development startup script
# Run this to start the NBA Analytics platform locally

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}NBA Analytics Platform - Local Setup${NC}"
echo -e "${GREEN}========================================${NC}"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}Python 3 is not installed. Please install Python 3.10+${NC}"
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo -e "${GREEN}Python version: ${PYTHON_VERSION}${NC}"

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
echo -e "${GREEN}Activating virtual environment...${NC}"
source venv/bin/activate

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -r requirements.txt

# Check if PostgreSQL is running
if ! pg_isready -h localhost -p 5432 &> /dev/null; then
    echo -e "${YELLOW}PostgreSQL doesn't seem to be running on localhost:5432${NC}"
    echo -e "${YELLOW}Make sure PostgreSQL is running or use Docker:${NC}"
    echo -e "${YELLOW}  docker-compose up postgres redis -d${NC}"
fi

# Check if Redis is running
if ! redis-cli ping &> /dev/null; then
    echo -e "${YELLOW}Redis doesn't seem to be running on localhost:6379${NC}"
    echo -e "${YELLOW}Make sure Redis is running or use Docker:${NC}"
    echo -e "${YELLOW}  docker-compose up postgres redis -d${NC}"
fi

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}Setup complete!${NC}"
echo -e "${GREEN}========================================${NC}"
echo ""
echo -e "To start the services, run these in separate terminals:"
echo ""
echo -e "${YELLOW}1. Start the API server:${NC}"
echo "   cd $(pwd) && source venv/bin/activate"
echo "   python -m uvicorn api.main:app --reload --port 8000"
echo ""
echo -e "${YELLOW}2. Start the dashboard:${NC}"
echo "   cd $(pwd) && source venv/bin/activate"
echo "   streamlit run dashboard/app.py"
echo ""
echo -e "${YELLOW}3. Run initial data ingestion:${NC}"
echo "   cd $(pwd) && source venv/bin/activate"
echo "   python scripts/run_ingestion.py"
echo ""
echo -e "${GREEN}Or use Docker Compose for everything:${NC}"
echo "   docker-compose up -d"
echo "   docker-compose --profile ingestion run ingestion"
