# PowerShell setup script for multi-airline scraping
# Run: .\setup_multi_airline.ps1

Write-Host "=====================================================" -ForegroundColor Cyan
Write-Host "Flight Fare Dashboard - Multi-Airline Setup" -ForegroundColor Cyan
Write-Host "=====================================================" -ForegroundColor Cyan

# Navigate to backend
Set-Location -Path "backend"

# Check if virtual environment exists
if (-Not (Test-Path -Path "venv")) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv venv
}

# Activate virtual environment
Write-Host "Activating virtual environment..." -ForegroundColor Yellow
& .\venv\Scripts\Activate.ps1

Write-Host "Virtual environment activated" -ForegroundColor Green

# Install requirements
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt

# Ensure Playwright browsers are installed
Write-Host "Installing Playwright browsers..." -ForegroundColor Yellow
python -m playwright install chromium

Write-Host ""
Write-Host "=====================================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "=====================================================" -ForegroundColor Green
Write-Host ""

Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Test the Ryanair scraper:" -ForegroundColor White
Write-Host "     python test_ryanair.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  2. Start the backend server:" -ForegroundColor White
Write-Host "     python main.py" -ForegroundColor Gray
Write-Host ""
Write-Host "  3. Use multi-airline scraping:" -ForegroundColor White
Write-Host "     POST http://localhost:8000/api/start-multi-airline-scrape" -ForegroundColor Gray
Write-Host ""
Write-Host "For more details, see: MULTI_AIRLINE_README.md" -ForegroundColor Cyan
