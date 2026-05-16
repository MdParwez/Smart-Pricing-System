# 🚀 COMPLETE SETUP & RUN GUIDE

## Quick Start (5 Minutes)

### 1️⃣ Backend Setup

```bash
# Navigate to backend
cd Flight-Fare-Dashboard/backend

# Create virtual environment
python -m venv venv

# Activate (Windows)
venv\Scripts\activate
# OR (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
playwright install chromium

# Run server
python main.py
```

✅ Backend running at: `http://localhost:8000`  
✅ API docs at: `http://localhost:8000/docs`

### 2️⃣ Frontend Setup

```bash
# Navigate to frontend
cd Flight-Fare-Dashboard/frontend

# Install dependencies
npm install

# Start development server
npm start
```

✅ Frontend running at: `http://localhost:3000`

---

## 📋 API Integration Guide

### How Frontend Communicates with Backend

#### 1. Service Layer (`scraperService.js`)

```javascript
// scraperService.js
import axios from 'axios';

const API_BASE_URL = 'http://localhost:8000/api';

export const scraperService = {
  startScrape: async (formData) => {
    // Sends form data to backend
    // Returns: task_id, status, timestamp
  },
  
  scheduleScrape: async (formData) => {
    // Schedules scrape for later
    // Returns: job_id, scheduled_time
  },
  
  getScrapingStatus: async (taskId) => {
    // Poll for task progress
  },
  
  downloadExcel: async (fileName) => {
    // Download results as Excel
  }
};
```

#### 2. Dashboard Component Flow

```
User fills form
    ↓
Clicks "Save" button
    ↓
Opens ScheduleDialog
    ↓
Chooses "Scrape Now" or "Schedule"
    ↓
Calls scraperService.startScrape() or scheduleScrape()
    ↓
Backend receives request
    ↓
Response: task_id (for tracking)
    ↓
Frontend shows success notification
    ↓
Form resets, ready for next scrape
```

---

## 🔌 API Workflow Explained

### Scrape Now Flow

```
Frontend                          Backend
   |                                |
   |-- POST /api/start-scrape ---→  |
   |   {formData}                   |
   |                                |
   |  ← {task_id, status}  ---------|
   |                                |
   | (Show success snackbar)         |
   |                                |  (Background task)
   |                                |  PlaywrightScraper.scrape()
   |                                |    ↓
   |                                |  Extract prices
   |                                |    ↓
   |                                |  Save to Excel
   |                                |    ↓
   |                                |  Update task status
   |                                |
   | (Optionally poll for status)   |
   |-- GET /api/scraping-status/task_id -→ |
   |                                |
   | ← {status, progress, records} ---|
```

### Schedule for Later Flow

```
Frontend                          Backend
   |                                |
   |-- POST /api/schedule-scrape → |
   |   {formData + date/time}       |
   |                                |
   |  ← {job_id, scheduled_for}  -| |
   |                                |
   | (Show scheduled notification)  |
   |                                |  APScheduler waits for time
   |                                |    ↓ (at scheduled time)
   |                                |  Trigger scrape job
   |                                |    ↓
   |                                |  Run PlaywrightScraper
   |                                |    ↓
   |                                |  Export Excel
```

---

## 🔧 Configuration

### Backend (.env)
```
PLAYWRIGHT_HEADLESS=True        # Run browser headless
SCRAPER_TIMEOUT=30000           # 30 second timeout per page
CONCURRENT_PAGES=10             # 10 parallel scraping sessions
SCHEDULER_TIMEZONE=Asia/Kolkata  # For scheduled jobs
LOG_LEVEL=INFO                  # Logging level
```

### Frontend (.env)
```
REACT_APP_API_URL=http://localhost:8000/api
REACT_APP_ENV=development
```

---

## 📊 Data Flow Example

### User Scenario: Scrape IndiGo prices DEL-BOM

1. **Fill Form**
   ```
   Report Name: "IndiGo DEL-BOM Competition"
   Origin: DEL
   Destination: BOM
   Airline: 6E (IndiGo)
   Journey Type: One Way
   Date Range: 15 days from today
   Channel: Playwright
   ```

2. **Frontend Validation**
   - Check required fields
   - Validate date ranges
   - Ensure origin ≠ destination

3. **Send to Backend**
   ```javascript
   const formData = {
     reportName: "IndiGo DEL-BOM Competition",
     origin: "DEL",
     destination: "BOM",
     airline: "6E",
     // ... other fields
   };
   
   const response = await scraperService.startScrape(formData);
   // Returns: { task_id: "abc-123", status: "running" }
   ```

4. **Backend Processing**
   - Receive request in `/api/start-scrape`
   - Validate Pydantic model
   - Create background task
   - Start PlaywrightScraper
   - Initialize browser → Load MakeMyTrip → Extract data

5. **Export Result**
   - Gather all flight records
   - Create DataFrame
   - Export to Excel (outputs/IndiGo_DEL-BOM_Competition_task_id.xlsx)
   - Update task status to "completed"

6. **Frontend Notification**
   - Show: "Scraping completed! 342 records found"
   - Provide download button
   - Reset form

---

## ✨ Key Features Explained

### 1. Multi-Step Form (Stepper)
- Step 0: Report Information
- Step 1: Journey Information  
- Step 2: Dates
- Step 3: Channel
- Click "Next" to progress, "Back" to return

### 2. Schedule Dialog
- Opens when user clicks "Save" on step 3
- Asks: "Scrape now or schedule?"
- If schedule: provide date picker, time picker, timezone

### 3. Background Tasks
```python
# Backend runs scraper in background
background_tasks.add_task(run_scraper, task_id, request)

# Task executes asynchronously
# Frontend continues to respond
# User can close browser, job still runs
```

### 4. Async Scraping
```python
# 10 browser windows in parallel
tasks = [
    scrape_route(page_1, "DEL", "BOM", "15-May"),
    scrape_route(page_2, "DEL", "BOM", "16-May"),
    scrape_route(page_3, "DEL", "BOM", "17-May"),
    ...
    scrape_route(page_10, "DEL", "BOM", "24-May"),
]
await asyncio.gather(*tasks)  # All 10 run simultaneously
```

---

## 🐛 Troubleshooting

### Backend won't start
```bash
# Check Python version
python --version  # Should be 3.8+

# Check installed packages
pip list

# Reinstall requirements
pip install -r requirements.txt --force-reinstall
```

### Playwright issues
```bash
# Reinstall browsers
playwright install chromium

# Check browser path
playwright install --with-deps
```

### Frontend API errors
```javascript
// Check CORS
// Backend has: CORSMiddleware(allow_origins=["*"])

// Check URL in .env
REACT_APP_API_URL=http://localhost:8000/api

// Test API directly
curl http://localhost:8000/health
```

### Port already in use
```bash
# Backend (8000)
lsof -i :8000
kill -9 <PID>

# Frontend (3000)
lsof -i :3000
kill -9 <PID>
```

---

## 📈 Performance Tips

1. **Increase Concurrent Pages**
   ```python
   CONCURRENT_PAGES=20  # For faster scraping
   ```

2. **Reduce Timeout**
   ```python
   SCRAPER_TIMEOUT=20000  # 20 sec instead of 30
   ```

3. **Run Background Task with Celery** (Advanced)
   - Use Redis for job queue
   - Run multiple worker processes
   - Scale to multiple servers

---

## 🚀 Production Deployment

### Using Docker Compose
```bash
docker-compose up -d
# Starts: Frontend (3000), Backend (8000), PostgreSQL (5432)
```

### Using Cloud (AWS/GCP/Azure)
1. Push to GitHub
2. Connect to cloud CI/CD (GitHub Actions)
3. Deploy on: Heroku, Railway, Render, DigitalOcean

### Environment Setup
```bash
# Production
API_URL=https://api.mysite.com
REACT_APP_API_URL=https://api.mysite.com/api
DATABASE_URL=postgresql://user:pass@host:5432/db
```

---

## 📝 Common Use Cases

### 1. Daily Competitor Monitoring
```bash
# Schedule scrape every day at 6 AM IST
POST /api/schedule-scrape
{
  "reportName": "Daily Competitor Check",
  "origin": "DEL",
  "destination": "BOM",
  "airline": "all",
  "scheduleDate": "2024-01-16",
  "scheduleTime": "06:00:00",
  "timezone": "IST"
}
```

### 2. Quick Ad-Hoc Analysis
```bash
# Scrape immediately
POST /api/start-scrape
{
  "reportName": "Quick Analysis",
  "origin": "DEL",
  "destination": "HYD",
  "airline": "6E",
  "channel": "playwright"
}
```

### 3. Weekly Report Generation
- Schedule scrape every Monday
- Export to Excel
- Email to managers
- Archive results

---

## 🎓 Learning Path

1. **Frontend**: Understand React components → Material UI → Form handling → Axios API calls
2. **Backend**: FastAPI basics → Async/await → Playwright → APScheduler
3. **Integration**: How frontend calls backend → Request/Response cycle
4. **Deployment**: Docker → Docker Compose → Cloud platforms

---

## 📞 Support & Questions

Check the main `README.md` for:
- Full API endpoint documentation
- Database migration guide
- Security best practices
- Scaling recommendations

Good luck! 🚀
