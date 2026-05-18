#!/bin/bash
# Quick setup guide for multi-airline scraping

echo "====================================================="
echo "Flight Fare Dashboard - Multi-Airline Setup"
echo "====================================================="

# Navigate to backend
cd backend

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python -m venv venv
fi

# Activate virtual environment (Linux/Mac)
source venv/bin/activate

# Or on Windows:
# venv\Scripts\activate

echo "Virtual environment activated"

# Install requirements
echo "Installing dependencies..."
pip install -r requirements.txt

# Ensure Playwright browsers are installed
echo "Installing Playwright browsers..."
python -m playwright install chromium

echo ""
echo "====================================================="
echo "Setup Complete!"
echo "====================================================="
echo ""
echo "To test the Ryanair scraper:"
echo "  python test_ryanair.py"
echo ""
echo "To start the backend server:"
echo "  python main.py"
echo ""
echo "To use multi-airline scraping:"
echo "  POST http://localhost:8000/api/start-multi-airline-scrape"
echo ""
echo "For more details, see: MULTI_AIRLINE_README.md"
