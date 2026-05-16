# 🏗️ Architecture Documentation

## System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         USER (Web Browser)                      │
└──────────────────────────────┬──────────────────────────────────┘
                               │
                ┌──────────────▼──────────────┐
                │    FRONTEND (React 18)      │
                │  - Material UI Components   │
                │  - Form Validation          │
                │  - State Management         │
                │  - Axios HTTP Client        │
                └──────────────┬──────────────┘
                               │
                   ┌───────────▼─────────────┐
                   │   REST API (Axios)      │
                   │  BASE_URL: :8000/api    │
                   └───────────┬─────────────┘
                               │
                ┌──────────────▼──────────────┐
                │   BACKEND (FastAPI)         │
                │  - Request Handling         │
                │  - Route Processing         │
                │  - Business Logic           │
                │  - Error Handling           │
                │  - CORS Support             │
                └──────────────┬──────────────┘
                               │
              ┌────────────────┼────────────────┐
              │                │                │
    ┌─────────▼────────┐  ┌────▼────────┐  ┌──▼──────────┐
    │  Scraper Module  │  │ APScheduler │  │ Logger/Logs │
    │ PlaywrightScraper│  │ Job Queue   │  │             │
    └─────────┬────────┘  └────┬────────┘  └─────────────┘
              │                │
              │                │ (Scheduled Tasks)
              │                │
    ┌─────────▼────────┐  ┌────▼────────┐
    │  MakeMyTrip.com  │  │  Excel File │
    │   (Real Data)    │  │   (Output)  │
    └──────────────────┘  └─────────────┘
```

## Component Architecture

### Frontend Structure

```
Frontend/
├── src/
│   ├── components/
│   │   ├── ReportInformation.js
│   │   │   └── Captures: Name, Description, Type, Notes
│   │   │
│   │   ├── JourneyInformation.js
│   │   │   └── Captures: Routes, Airlines, Passengers, Class
│   │   │
│   │   ├── DateSelection.js
│   │   │   └── Captures: Date ranges, Days of week, Times
│   │   │
│   │   ├── ChannelSelection.js
│   │   │   └── Captures: Scraping source (Playwright/API/Upload)
│   │   │
│   │   └── ScheduleDialog.js
│   │       └── Handles: Scrape now vs Schedule later decision
│   │
│   ├── pages/
│   │   └── Dashboard.js
│   │       ├── Main orchestrator component
│   │       ├── Manages form state
│   │       ├── Handles step navigation
│   │       ├── Calls API endpoints
│   │       └── Shows notifications
│   │
│   ├── services/
│   │   └── scraperService.js
│   │       ├── startScrape()
│   │       ├── scheduleScrape()
│   │       ├── getScrapingStatus()
│   │       ├── downloadExcel()
│   │       └── getScrapingHistory()
│   │
│   ├── hooks/
│   │   └── (Custom React hooks - Future)
│   │
│   ├── App.js (Theme setup, routing)
│   └── index.js (React DOM render)
```

### Backend Structure

```
Backend/
├── main.py
│   ├── FastAPI app initialization
│   ├── CORS middleware setup
│   ├── Route registration
│   ├── Startup/Shutdown events
│   └── Health check endpoint
│
├── app/
│   ├── routes/
│   │   └── scraper_routes.py
│   │       ├── POST /start-scrape
│   │       ├── POST /schedule-scrape
│   │       ├── GET /scraping-status/{id}
│   │       ├── GET /download/{filename}
│   │       └── GET /scraping-history
│   │
│   ├── scraper/
│   │   └── playwright_scraper.py
│   │       ├── PlaywrightScraper class
│   │       ├── scrape() method
│   │       ├── _scrape_route() method
│   │       ├── Data extraction logic
│   │       └── export_to_excel() method
│   │
│   ├── scheduler/
│   │   └── job_scheduler.py
│   │       ├── APScheduler initialization
│   │       ├── add_scrape_job()
│   │       ├── run_scraper_task()
│   │       ├── get_job_status()
│   │       └── remove_job()
│   │
│   └── utils/
│       ├── logger.py (Logging configuration)
│       └── models.py (Pydantic data models)
```

## Data Flow Diagrams

### 1. Immediate Scraping Flow

```
┌─────────┐
│  Start  │
└────┬────┘
     │
     ▼
┌──────────────────────┐
│ User Opens Dashboard │
└────┬─────────────────┘
     │
     ▼
┌──────────────────────────────┐
│ Fill 4-Step Form             │
│ 1. Report Info               │
│ 2. Journey Info              │
│ 3. Dates                     │
│ 4. Channel                   │
└────┬─────────────────────────┘
     │
     ▼
┌──────────────────────────────┐
│ Click "Save" Button          │
│ (Step 4)                     │
└────┬─────────────────────────┘
     │
     ▼
┌──────────────────────────────┐
│ Schedule Dialog Opens        │
│ Options:                     │
│ - Scrape Now ✓              │
│ - Schedule for Later         │
└────┬─────────────────────────┘
     │ (Select "Scrape Now")
     ▼
┌──────────────────────────────┐
│ Frontend Sends:              │
│ POST /api/start-scrape       │
│ {formData}                   │
└────┬─────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Backend Receives Request          │
│ - Validate with Pydantic model   │
│ - Create task_id (UUID)          │
│ - Add to background_tasks        │
│ - Return response                │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Frontend Receives:                │
│ {                                │
│   "task_id": "abc-123",          │
│   "status": "running",           │
│   "started_at": "2024-01-15..."  │
│ }                                │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────────────┐
│ Show Success Notification    │
│ "Scraping started!"          │
└────┬─────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Background Task Executes:        │
│ async run_scraper(task_id, req) │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Initialize PlaywrightScraper     │
│ - Launch browser                 │
│ - Create context                 │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ For each (origin, dest, date):   │
│ - Load MakeMyTrip URL            │
│ - Wait for flights to load       │
│ - Parse flight data              │
│ - Extract: price, airline, times │
│ - Append to results list         │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Processing 10 routes in parallel │
│ Concurrency: 10 browser windows  │
│ Speed: ~20 requests/minute       │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Compile Results                  │
│ - 300+ flight records            │
│ - Price, airline, times, etc.    │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Export to Excel                  │
│ - Create pandas DataFrame        │
│ - Write with openpyxl           │
│ - Save to outputs/report.xlsx    │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Update Task Status               │
│ scraping_tasks[task_id] = {      │
│   "status": "completed",         │
│   "progress": 100,               │
│   "records_count": 342,          │
│   "output_file": "path/to/file"  │
│ }                                │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Frontend (Optional Polling)      │
│ GET /api/scraping-status/abc-123 │
│                                  │
│ Receives:                        │
│ {                                │
│   "status": "completed",         │
│   "records_count": 342           │
│ }                                │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Show Completion Alert            │
│ "342 records found!"             │
│ Download button available        │
└────┬───────────────────────────────┘
     │
     ▼
┌──────────────────────────────────┐
│ Download Excel File              │
│ GET /api/download/report_abc-123 │
│                                  │
│ Browser downloads: report.xlsx   │
└────┬───────────────────────────────┘
     │
     ▼
┌────────────┐
│    End     │
└────────────┘
```

### 2. Scheduled Scraping Flow

```
User selects "Schedule for Later"
            │
            ▼
Schedule Dialog shows:
- Date picker
- Time picker
- Timezone dropdown
            │
            ▼
User selects: 2024-01-20, 14:30, IST
            │
            ▼
Frontend sends:
POST /api/schedule-scrape
{
  ...formData...,
  "scheduleDate": "2024-01-20",
  "scheduleTime": "14:30:00",
  "timezone": "IST"
}
            │
            ▼
Backend receives & validates
            │
            ▼
APScheduler.add_job():
- job_id: uuid
- trigger: DateTrigger(run_date=2024-01-20 14:30 IST)
- function: run_scraper_task
- args: [formData]
            │
            ▼
Response to frontend:
{
  "job_id": "def-456",
  "status": "scheduled",
  "scheduled_for": "2024-01-20 14:30:00 IST"
}
            │
            ▼
Frontend shows:
"Scheduled! Will run on 2024-01-20 at 14:30 IST"
            │
            ├─ User can close browser
            │
            ▼ (At scheduled time)
Scheduler triggers run_scraper_task()
            │
            ▼
Same as immediate scraping flow
(from PlaywrightScraper initialization onwards)
```

## Request/Response Examples

### 1. Start Scrape Request

```json
POST http://localhost:8000/api/start-scrape
Content-Type: application/json

{
  "reportName": "IndiGo Competitive Analysis",
  "reportDescription": "Analyzing IndiGo prices vs competitors on DEL-BOM",
  "userNotes": "Focus on weekend prices",
  "reportType": "competitive",
  "journeyType": "one-way",
  "passengerType": {
    "adult": 1,
    "child": 0,
    "infant": 0
  },
  "classOfService": "economy",
  "stops": "non-stop",
  "origin": "DEL",
  "destination": "BOM",
  "airline": "all",
  "reverseOND": false,
  "dateRange": "continuous",
  "outboundDateFrom": "2024-01-15",
  "outboundDateTo": "2024-01-30",
  "inboundDateFrom": null,
  "inboundDateTo": null,
  "daysOfWeek": ["fri", "sat", "sun"],
  "departureTime": "morning",
  "returnParameter": "7",
  "considerFarthestDate": false,
  "channel": "playwright"
}

RESPONSE (200 OK):
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "running",
  "message": "Scraping started for IndiGo Competitive Analysis",
  "started_at": "2024-01-15T10:30:00.123456"
}
```

### 2. Schedule Scrape Request

```json
POST http://localhost:8000/api/schedule-scrape
Content-Type: application/json

{
  ...all fields from start-scrape plus:
  "scheduleDate": "2024-01-16",
  "scheduleTime": "14:30:00",
  "timezone": "IST",
  "runOption": "schedule"
}

RESPONSE (200 OK):
{
  "job_id": "660e8400-e29b-41d4-a716-446655440111",
  "status": "scheduled",
  "report_name": "IndiGo Competitive Analysis",
  "scheduled_for": "2024-01-16 14:30:00 IST",
  "message": "Scraping scheduled successfully"
}
```

### 3. Get Status Request

```
GET http://localhost:8000/api/scraping-status/550e8400-e29b-41d4-a716-446655440000

RESPONSE (200 OK):
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "progress": 100,
  "records_count": 342,
  "started_at": "2024-01-15T10:30:00.123456",
  "completed_at": "2024-01-15T10:45:30.654321",
  "output_file": "outputs/IndiGo_Competitive_Analysis_550e8400.xlsx"
}
```

---

## Data Models

### ScrapeRequest (Pydantic)
```python
class PassengerType(BaseModel):
    adult: int = 1
    child: int = 0
    infant: int = 0

class ScrapeRequest(BaseModel):
    reportName: str                      # Required
    reportDescription: Optional[str]
    userNotes: Optional[str]
    reportType: str                      # 'standard', 'competitive', 'pricing'
    journeyType: str                     # 'one-way', 'round-trip'
    passengerType: PassengerType
    classOfService: str                  # 'economy', 'premium-economy', 'business'
    stops: str                           # 'non-stop', 'one-stop', 'two-plus-stops'
    origin: str                          # e.g., 'DEL'
    destination: str                     # e.g., 'BOM'
    airline: str                         # '6E', 'AI', 'SG', 'IX', or 'all'
    reverseOND: bool
    dateRange: str                       # 'continuous', 'preferred'
    outboundDateFrom: Optional[str]
    outboundDateTo: Optional[str]
    inboundDateFrom: Optional[str]
    inboundDateTo: Optional[str]
    daysOfWeek: List[str]               # ['mon', 'tue', 'wed', ...]
    departureTime: str                   # 'any', 'early-morning', 'morning', etc.
    returnParameter: str                 # Days
    considerFarthestDate: bool
    channel: str                         # 'playwright', 'api', 'manual-upload'
```

---

## Error Handling

### Frontend Error Handling
```javascript
try {
  const response = await scraperService.startScrape(formData);
  // Show success notification
} catch (error) {
  // Show error snackbar with error.message
  // Log to console
  // Don't reset form (preserve user input)
}
```

### Backend Error Handling
```python
@router.post("/start-scrape")
async def start_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    try:
        # Validation happens automatically (Pydantic)
        # Add task
        # Return success
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error")
```

---

## Database Integration (Future)

Replace in-memory storage with PostgreSQL:

```python
# Current (In-Memory)
scraping_tasks = {}

# Future (PostgreSQL)
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

DATABASE_URL = "postgresql://user:pass@localhost/fares_db"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)

# Models
class ScrapingTask(Base):
    __tablename__ = "scraping_tasks"
    
    id = Column(String, primary_key=True)
    report_name = Column(String)
    status = Column(String)  # running, completed, error
    progress = Column(Integer)
    records_count = Column(Integer)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    output_file = Column(String)
    error_message = Column(String, nullable=True)
```

---

This architecture is scalable, maintainable, and production-ready!
