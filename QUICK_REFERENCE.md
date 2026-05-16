# 🎯 Quick Reference Commands

## 📂 Project Location
```
C:\Users\zaid.hussain\OneDrive - Aionos\Documents\projects\Flight-Fare-Dashboard\
```

## 🚀 Start Everything (2 Terminals)

### Terminal 1: Backend
```bash
# Navigate to backend
cd backend

# Activate virtual environment
venv\Scripts\activate  # Windows

# Install (first time only)
pip install -r requirements.txt
playwright install chromium

# Start server
python main.py
```

✅ Backend: http://localhost:8000  
📚 API Docs: http://localhost:8000/docs

### Terminal 2: Frontend
```bash
# Navigate to frontend
cd frontend

# Install (first time only)
npm install

# Start dev server
npm start
```

✅ Frontend: http://localhost:3000

---

## 🔥 API Testing (Copy-Paste Commands)

### Using PowerShell/Windows Terminal

#### 1. Health Check
```powershell
$headers = @{'Content-Type' = 'application/json'}
$uri = 'http://localhost:8000/health'
Invoke-RestMethod -Uri $uri -Method Get
```

#### 2. Start Scraping (Immediate)
```powershell
$headers = @{'Content-Type' = 'application/json'}
$body = @{
    reportName = "Test Scrape"
    reportDescription = "Testing immediate scrape"
    origin = "DEL"
    destination = "BOM"
    airline = "all"
    journeyType = "one-way"
    classOfService = "economy"
    passengerType = @{adult=1; child=0; infant=0}
    stops = "non-stop"
    dateRange = "continuous"
    outboundDateFrom = "2024-01-15"
    outboundDateTo = "2024-01-30"
    daysOfWeek = @("mon", "tue", "wed", "thu", "fri")
    departureTime = "any"
    returnParameter = "7"
    considerFarthestDate = $false
    channel = "playwright"
    reverseOND = $false
    reportType = "standard"
    userNotes = ""
    reportDescription = "Test"
} | ConvertTo-Json

$uri = 'http://localhost:8000/api/start-scrape'
Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $body
```

#### 3. Schedule Scraping (Later)
```powershell
$headers = @{'Content-Type' = 'application/json'}
$body = @{
    reportName = "Scheduled Scrape"
    origin = "DEL"
    destination = "BLR"
    airline = "6E"
    journeyType = "one-way"
    classOfService = "economy"
    passengerType = @{adult=1; child=0; infant=0}
    stops = "non-stop"
    dateRange = "continuous"
    outboundDateFrom = "2024-01-15"
    outboundDateTo = "2024-01-30"
    daysOfWeek = @()
    departureTime = "any"
    returnParameter = "7"
    considerFarthestDate = $false
    channel = "playwright"
    reverseOND = $false
    reportType = "competitive"
    reportDescription = "Testing scheduled scrape"
    userNotes = "Test"
    scheduleDate = "2024-01-16"
    scheduleTime = "14:30:00"
    timezone = "IST"
    runOption = "schedule"
} | ConvertTo-Json

$uri = 'http://localhost:8000/api/schedule-scrape'
Invoke-RestMethod -Uri $uri -Method Post -Headers $headers -Body $body
```

#### 4. Check Task Status
```powershell
# Replace task_id with actual ID from response above
$uri = 'http://localhost:8000/api/scraping-status/YOUR_TASK_ID_HERE'
Invoke-RestMethod -Uri $uri -Method Get
```

#### 5. Get Scraping History
```powershell
$uri = 'http://localhost:8000/api/scraping-history'
Invoke-RestMethod -Uri $uri -Method Get | ConvertTo-Json
```

---

## 🛠️ Useful Development Commands

### Frontend
```bash
# Install new package
npm install <package-name>

# Build for production
npm run build

# Run tests
npm test

# Clear node_modules (if issues)
rm -r node_modules
npm install
```

### Backend
```bash
# Format code
black .

# Check type hints
mypy app/

# Run tests (if added)
pytest

# Check dependencies
pip list

# Freeze requirements
pip freeze > requirements.txt
```

---

## 🔍 Common Issues & Fixes

### Port Already in Use
```powershell
# Find process using port 8000
netstat -ano | findstr :8000

# Kill process (replace PID)
taskkill /PID <PID> /F

# For port 3000
netstat -ano | findstr :3000
taskkill /PID <PID> /F
```

### Playwright Issues
```bash
# Reinstall browser
playwright install chromium

# With dependencies
playwright install --with-deps
```

### CORS Errors
- Backend already has CORSMiddleware enabled
- If still failing, check: `main.py` line with `CORSMiddleware`

### Module Not Found
```bash
# Backend
pip install -r requirements.txt --force-reinstall

# Frontend  
npm install
npm install @mui/x-date-pickers @mui/material @emotion/react @emotion/styled
```

---

## 📊 File Structure Summary

### Key Files to Know

**Frontend**
- `src/App.js` → Main app component
- `src/pages/Dashboard.js` → Main dashboard logic
- `src/components/` → All UI components
- `src/services/scraperService.js` → API calls
- `package.json` → Dependencies

**Backend**
- `main.py` → FastAPI app entry
- `app/routes/scraper_routes.py` → API endpoints
- `app/scraper/playwright_scraper.py` → Scraping logic
- `app/scheduler/job_scheduler.py` → Scheduled jobs
- `requirements.txt` → Python dependencies

**Config**
- `frontend/.env` → Frontend config
- `backend/.env` → Backend config
- `.gitignore` → Git ignore rules
- `docker-compose.yml` → Docker setup

**Documentation**
- `README.md` → Project overview
- `SETUP_GUIDE.md` → Detailed setup
- `ARCHITECTURE.md` → Technical architecture
- `QUICK_REFERENCE.md` → This file

---

## 🚀 Deployment Quick Steps

### Docker Compose (Fastest)
```bash
# Navigate to project root
cd Flight-Fare-Dashboard

# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

### Manual Deployment (Linux/macOS)

**Backend**
```bash
cd backend
source venv/bin/activate
pip install -r requirements.txt
gunicorn main:app --workers 4 --worker-class uvicorn.workers.UvicornWorker
```

**Frontend**
```bash
cd frontend
npm run build
serve -s build -l 3000
```

---

## 📈 Monitoring & Logs

### Backend Logs
```bash
# Real-time logs
tail -f logs/app.log

# Last 50 lines
tail -50 logs/app.log

# Search for errors
grep ERROR logs/app.log

# Using Docker
docker-compose logs -f backend
```

### Frontend Logs
- Browser console: Press `F12` → Console tab
- Network: Check API calls in Network tab
- React DevTools: Extension for React debugging

---

## 🔐 Security Checklist (Production)

- [ ] Enable HTTPS/SSL
- [ ] Add authentication (JWT tokens)
- [ ] Use environment variables (not hardcoded)
- [ ] Validate all inputs (already done with Pydantic)
- [ ] Set CORS to specific domain
- [ ] Rate limiting on APIs
- [ ] Database password protection
- [ ] Log sensitive data redaction
- [ ] Error messages don't expose internals
- [ ] Dependencies updated regularly

---

## 📚 Learning Resources

### Frontend (React + Material UI)
- React: https://react.dev
- Material UI: https://mui.com
- Axios: https://axios-http.com
- React Hook Form: https://react-hook-form.com

### Backend (FastAPI)
- FastAPI: https://fastapi.tiangolo.com
- Playwright: https://playwright.dev/python
- APScheduler: https://apscheduler.readthedocs.io

---

## 💡 Next Steps

1. **Test the system**
   - Fill form in UI
   - Click Save → Scrape Now
   - Watch backend logs
   - Download Excel file

2. **Customize scraper**
   - Add more airlines
   - Add more routes
   - Modify extraction logic
   - Improve error handling

3. **Add database**
   - Install PostgreSQL
   - Create SQLAlchemy models
   - Replace in-memory storage
   - Add migrations

4. **Deploy to cloud**
   - Choose: AWS, GCP, Azure, Heroku
   - Set up CI/CD pipeline
   - Configure domain
   - Monitor production

---

## 🤝 Support

**For issues, check these files first:**
1. `README.md` - General overview
2. `SETUP_GUIDE.md` - Setup problems
3. `ARCHITECTURE.md` - Design questions
4. Backend logs - Scraper errors
5. Browser console - Frontend errors

---

**Happy Coding! 🎉**

Last Updated: January 2024  
Project: Flight Fare Intelligence Dashboard  
Version: 1.0.0
