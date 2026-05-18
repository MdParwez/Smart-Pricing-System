# Complete Multi-Airline Scraper Implementation

## 🎯 Overview

This document provides a complete guide to the multi-airline flight scraper implementation, including:
- ✅ **Ryanair Scraper** - Fully implemented and tested
- ✅ **Lufthansa Scraper** - Fully implemented  
- ✅ **SQLite Database** - Stores all scraped flights and task history
- ✅ **Frontend UI Components** - Complete React components for the scraper interface
- ✅ **API Endpoints** - RESTful endpoints for scraping and data retrieval

---

## 📁 File Structure

### Backend Files

```
backend/
├── app/
│   ├── database.py                      # SQLAlchemy models & DB setup
│   ├── scraper/
│   │   ├── ryanair_scraper.py          # Ryanair implementation
│   │   ├── lufthansa_scraper.py        # Lufthansa implementation
│   │   └── playwright_scraper.py       # Original MakeMyTrip scraper
│   ├── routes/
│   │   └── scraper_routes.py           # Updated with new endpoints
│   └── utils/
│       └── airline_models.py           # Airline configurations
├── requirements.txt                     # Updated with SQLAlchemy
└── test_ryanair.py                     # Comprehensive test script
```

### Frontend Files

```
frontend/
├── src/
│   ├── components/
│   │   ├── AirlineSelection.js          # Step 1: Choose airline
│   │   ├── RouteSelection.js            # Step 2: Choose route
│   │   ├── FlightResults.js             # Step 4: Display results
│   │   └── MultiAirlineDashboard.js     # Main orchestrator component
│   └── index.js
└── package.json                         # Updated with recharts
```

---

## 🗄️ Database Schema

### Tables

#### `scraping_tasks`
Tracks all scraping operations:
```sql
id (STRING, PK)              -- Unique task ID
report_name (STRING)         -- User-provided report name
airline (STRING)             -- Primary airline
origin (STRING)              -- Departure airport code
destination (STRING)         -- Arrival airport code
start_date (STRING)          -- Search start date
end_date (STRING)            -- Search end date
status (STRING)              -- running, completed, failed
progress (INTEGER)           -- 0-100
records_count (INTEGER)      -- Number of flights found
airlines_scraped (STRING)    -- JSON array of airlines
error_message (STRING)       -- If failed
started_at (DATETIME)        -- Task start time
completed_at (DATETIME)      -- Task completion time
```

#### `flights`
Stores all scraped flight data:
```sql
id (INTEGER, PK)
task_id (STRING, FK)         -- Link to scraping task
airline (STRING)             -- Flight airline
origin (STRING)              -- Departure airport
destination (STRING)         -- Arrival airport
departure_date (STRING)      -- Travel date
departure_time (STRING)      -- Departure time (HH:MM)
arrival_time (STRING)        -- Arrival time (HH:MM)
duration (STRING)            -- Flight duration
price (FLOAT)                -- Price in currency
currency (STRING)            -- Currency code
stops (STRING)               -- Number of stops
scraped_at (DATETIME)        -- Scraping timestamp
```

#### `price_history`
For historical price analysis:
```sql
id (INTEGER, PK)
airline (STRING)
origin (STRING)
destination (STRING)
departure_date (STRING)
lowest_price (FLOAT)
average_price (FLOAT)
highest_price (FLOAT)
flight_count (INTEGER)
recorded_at (DATETIME)
```

---

## 🚀 Quick Start

### 1. Install Dependencies

#### Backend
```bash
cd backend
pip install -r requirements.txt
python -m playwright install chromium
```

#### Frontend
```bash
cd frontend
npm install
```

### 2. Initialize Database

```bash
cd backend
python
>>> from app.database import init_db
>>> init_db()
```

### 3. Run Tests

```bash
cd backend
python test_ryanair.py
```

### 4. Start Services

#### Terminal 1: Backend
```bash
cd backend
python main.py
# Backend runs on http://localhost:8000
```

#### Terminal 2: Frontend
```bash
cd frontend
npm start
# Frontend runs on http://localhost:3000
```

---

## 🎨 Frontend Components

### 1. MultiAirlineDashboard (Main Component)

**File:** `frontend/src/components/MultiAirlineDashboard.js`

The orchestrator component that manages the entire scraping workflow.

**Features:**
- 4-step wizard interface
- Form validation
- Task status polling
- Error handling
- Result display

**Usage:**
```javascript
import MultiAirlineDashboard from './components/MultiAirlineDashboard';

export default function App() {
  return <MultiAirlineDashboard />;
}
```

**Props:** None (manages own state)

**State Management:**
- `step` - Current step (1-4)
- `selectedAirline` - Selected airline config
- `selectedRoute` - Origin & destination
- `taskId` - Current scraping task ID
- `taskStatus` - Real-time task status

---

### 2. AirlineSelection

**File:** `frontend/src/components/AirlineSelection.js`

Displays available airlines and their competitors.

**Features:**
- Fetches airlines from API
- Displays competitor airlines
- Competitor toggle switch
- Shows configured routes

**Props:**
```javascript
{
  onAirlineSelect: (airline) => void,    // Called when airline selected
  onCompetitorsChange: (enabled) => void  // Called when competitors toggled
}
```

**Example:**
```javascript
<AirlineSelection
  onAirlineSelect={(airline) => {
    setSelectedAirline(airline);
  }}
  onCompetitorsChange={(enabled) => {
    setIncludeCompetitors(enabled);
  }}
/>
```

---

### 3. RouteSelection

**File:** `frontend/src/components/RouteSelection.js`

Allows selecting pre-configured or custom routes.

**Features:**
- Pre-configured routes from airline config
- Custom airport code input
- IATA code reference table
- Auto-selection of first route

**Props:**
```javascript
{
  airline: {                      // Airline config object
    airport_codes: {},
    routes: [],
    ...
  },
  onRouteSelect: (route) => void  // Called with {origin, destination}
}
```

**Example:**
```javascript
<RouteSelection
  airline={selectedAirline}
  onRouteSelect={(route) => {
    setSelectedRoute(route);
  }}
/>
```

---

### 4. FlightResults

**File:** `frontend/src/components/FlightResults.js`

Displays scraped flights with statistics and charts.

**Features:**
- Real-time statistics cards
- Price comparison chart (Bar)
- Flight count by airline (Pie)
- Sortable flights table
- Responsive design

**Props:**
```javascript
{
  taskId: string,      // Task ID to fetch results from
  origin: string,      // Departure airport code
  destination: string  // Arrival airport code
}
```

**Example:**
```javascript
<FlightResults
  taskId="a1b2c3d4-..."
  origin="DUB"
  destination="LHR"
/>
```

**Charts Used:**
- **recharts.BarChart** - Price comparison
- **recharts.PieChart** - Flight distribution
- **recharts.LineChart** - Price trends (expandable)

---

## 📡 API Endpoints

### Airline Information

#### List Available Airlines
```
GET /api/airlines/list
```
**Response:**
```json
{
  "airlines": ["Ryanair", "Lufthansa", "Wizz Air", "Easyjet"],
  "total": 4
}
```

#### Get Airline Configuration
```
GET /api/airlines/config/{airline_name}
```
**Example:** `GET /api/airlines/config/Ryanair`

**Response:**
```json
{
  "airline": "Ryanair",
  "base_url": "https://www.ryanair.com",
  "website_type": "react",
  "routes": [...],
  "competitors": ["Wizz Air", "Easyjet"],
  "airport_codes": {...}
}
```

### Scraping Operations

#### Start Multi-Airline Scraping
```
POST /api/start-multi-airline-scrape
```
**Request:**
```json
{
  "reportName": "Ryanair_Dublin_June",
  "airline": "Ryanair",
  "origin": "DUB",
  "destination": "STN",
  "startDate": "2026-06-01",
  "endDate": "2026-06-15",
  "numPassengers": 1,
  "includeCompetitors": true,
  "currency": "EUR",
  "channel": "playwright"
}
```

**Response:**
```json
{
  "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "running",
  "message": "Multi-airline scraping started for Ryanair",
  "started_at": "2026-05-18T10:30:45.123456"
}
```

#### Check Task Status
```
GET /api/scraping-status/{task_id}
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "running|completed|failed",
  "progress": 50,
  "records_count": 450,
  "airlines_scraped": ["Ryanair", "Easyjet"],
  "started_at": "2026-05-18T10:30:45.123456",
  "completed_at": null
}
```

### Flight Data

#### Search Flights
```
GET /api/flights/search?origin=DUB&destination=STN&min_price=20&max_price=100
```

**Response:**
```json
{
  "flights": [
    {
      "id": 1,
      "airline": "Ryanair",
      "departure_time": "14:00",
      "arrival_time": "15:30",
      "price": 29.99,
      "currency": "EUR",
      "duration": "1h 30m",
      "date": "2026-06-01",
      "scraped_at": "2026-05-18T11:45:30"
    }
  ],
  "total": 42
}
```

#### Get Flight Statistics
```
GET /api/flights/stats/{origin}/{destination}
```

**Response:**
```json
{
  "origin": "DUB",
  "destination": "STN",
  "total_flights": 150,
  "airlines_count": 3,
  "airlines": ["Ryanair", "Easyjet", "Wizz Air"],
  "price_stats": {
    "minimum": 19.99,
    "maximum": 199.99,
    "average": 49.99,
    "median": 39.99
  },
  "by_airline": {
    "Ryanair": {
      "count": 50,
      "min_price": 19.99,
      "avg_price": 39.99
    }
  }
}
```

#### Get Task Flights
```
GET /api/flights/history/{task_id}
```

**Response:**
```json
{
  "task_id": "a1b2c3d4-...",
  "report_name": "Ryanair_Dublin_June",
  "airline": "Ryanair",
  "status": "completed",
  "records_count": 450,
  "flights": [...]
}
```

---

## 🧪 Testing

### Run Full Test Suite

```bash
cd backend
python test_ryanair.py
```

**Tests Include:**
1. ✅ Airline configuration loading
2. ✅ Database initialization
3. ✅ Ryanair scraper
4. ✅ Lufthansa scraper
5. ✅ Statistics and data retrieval

### API Testing with cURL

```bash
# List airlines
curl http://localhost:8000/api/airlines/list

# Get Ryanair config
curl http://localhost:8000/api/airlines/config/Ryanair

# Start scraping
curl -X POST http://localhost:8000/api/start-multi-airline-scrape \
  -H "Content-Type: application/json" \
  -d '{
    "reportName": "Test",
    "airline": "Ryanair",
    "origin": "DUB",
    "destination": "STN",
    "startDate": "2026-06-01",
    "includeCompetitors": true
  }'
```

---

## 🔧 Configuration

### Airline Configuration

Edit `backend/app/utils/airline_models.py`:

```python
AIRLINE_CONFIGS = {
    "MyAirline": {
        "base_url": "https://www.myairline.com",
        "website_type": "react|api_based",  # Type of website
        "routes": [
            {
                "origin": "ABC",
                "destination": "XYZ",
                "origin_name": "City A",
                "destination_name": "City Z"
            }
        ],
        "competitors": ["Airline1", "Airline2"],
        "airport_codes": {
            "ABC": "City A Airport",
            "XYZ": "City Z Airport"
        },
        "selectors": {
            "flight_card": "[data-testid='flight-card']",
            # ... more CSS selectors
        }
    }
}
```

---

## 🛠️ Adding a New Airline

### Step 1: Update airline_models.py
Add configuration for the new airline

### Step 2: Create Scraper
```python
# backend/app/scraper/myairline_scraper.py
class MyAirlineScraper:
    async def scrape(self, routes, start_date, end_date, num_passengers):
        # Implementation
        pass
```

### Step 3: Update Routes
```python
# backend/app/routes/scraper_routes.py
elif airline == "MyAirline":
    scraper = MyAirlineScraper()
    flights = await scraper.scrape(...)
```

### Step 4: Test
```bash
python test_ryanair.py
```

---

## 📊 Data Analysis Features

### Statistics Available
- Minimum, maximum, average, and median prices
- Price comparison by airline
- Flight distribution by airline
- Total flights found

### Export Options
- Excel (.xlsx)
- CSV (ready to add)
- JSON API responses

---

## 🔒 Security Considerations

✅ **Implemented:**
- User agent rotation
- Request delays (2 seconds between requests)
- Headless browser mode
- Error logging

⚠️ **To Add:**
- Proxy rotation for large-scale scraping
- CAPTCHA handling
- Rate limiting compliance
- Authentication for API

---

## 📈 Performance Tips

1. **Batch Processing**: Scrape multiple dates efficiently
2. **Caching**: Recent results cached in database
3. **Async Operations**: All scraping is async/parallel
4. **Database Indexing**: Quick queries on origin/destination
5. **Browser Pooling**: Reuse browser connections

---

## 🐛 Troubleshooting

### Issue: Selectors Not Found
**Solution**: Update selectors in airline_models.py based on current website

### Issue: Timeout Errors
**Solution**: Increase wait_until timeout in scraper

### Issue: Database Locked
**Solution**: Close all connections, restart backend service

### Issue: Rate Limiting
**Solution**: Increase delays between requests in scraper

---

## 📝 Next Steps

1. ✅ Test Ryanair scraper against live website
2. ⏳ Implement Wizard Air scraper
3. ⏳ Implement Easyjet scraper
4. ⏳ Add proxy rotation for production
5. ⏳ Add real-time price alert notifications
6. ⏳ Implement machine learning for price prediction
7. ⏳ Add historical price trend analysis

---

## 📞 Support

For issues or questions:
1. Check [MULTI_AIRLINE_README.md](MULTI_AIRLINE_README.md)
2. Review logs in `backend/logs/`
3. Run test script: `python test_ryanair.py`
4. Check API docs: `http://localhost:8000/docs`

