# Multi-Airline Scraping Implementation Guide

## Overview

This document describes the new multi-airline scraping system for the Flight Fare Dashboard. The system currently supports **Ryanair** with plans to add other European airlines and competitors.

## Architecture

### File Structure

```
backend/
├── app/
│   ├── scraper/
│   │   ├── playwright_scraper.py      (Original - for MakeMyTrip India)
│   │   └── ryanair_scraper.py         (NEW - Ryanair specific)
│   ├── routes/
│   │   └── scraper_routes.py          (UPDATED - new multi-airline endpoints)
│   ├── utils/
│   │   ├── models.py                  (UPDATED - new request models)
│   │   └── airline_models.py          (NEW - airline configurations)
│   └── scheduler/
│       └── job_scheduler.py           (unchanged)
└── test_ryanair.py                    (NEW - test script)
```

### Airline Configurations

Supported airlines and their competitors are defined in [backend/app/utils/airline_models.py](airline_models.py):

#### **Ryanair**
- **Competitors**: Wizz Air, Easyjet
- **Routes**:
  - Dublin (DUB) ↔ London Stansted (STN)
  - Cork (ORK) ↔ London Stansted (STN)
- **Website Type**: React-based SPA
- **Base URL**: https://www.ryanair.com

#### **Lufthansa** (Coming Soon)
- **Competitors**: BA, Turkish, Air France
- **Routes**:
  - Frankfurt (FRA) ↔ London (LHR)
  - Munich (MUC) ↔ San Diego (SAN)
- **Website Type**: API-based
- **Base URL**: https://www.lufthansa.com

## API Endpoints

### 1. Start Multi-Airline Scraping
```
POST /api/start-multi-airline-scrape
```

**Request Body:**
```json
{
  "reportName": "Ryanair_Jun2026",
  "reportDescription": "Ryanair and competitors",
  "userNotes": "Monitoring Dublin-London route",
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

### 2. Get Scraping Status
```
GET /api/scraping-status/{task_id}
```

**Response:**
```json
{
  "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
  "status": "running|completed|failed",
  "progress": 50,
  "report_name": "Ryanair_Jun2026",
  "airline": "Ryanair",
  "origin": "DUB",
  "destination": "STN",
  "start_date": "2026-06-01",
  "end_date": "2026-06-15",
  "include_competitors": true,
  "records_count": 450,
  "airlines_scraped": ["Ryanair", "Easyjet"],
  "started_at": "2026-05-18T10:30:45.123456",
  "completed_at": "2026-05-18T11:45:30.654321",
  "output_file": "/path/to/outputs/Ryanair_Jun2026_task123.xlsx"
}
```

### 3. List Available Airlines
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

### 4. Get Airline Configuration
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
  "routes": [
    {
      "origin": "DUB",
      "destination": "STN",
      "origin_name": "Dublin",
      "destination_name": "London Stansted"
    },
    {
      "origin": "ORK",
      "destination": "STN",
      "origin_name": "Cork",
      "destination_name": "London Stansted"
    }
  ],
  "competitors": ["Wizz Air", "Easyjet"],
  "airport_codes": {
    "DUB": "Dublin",
    "STN": "London Stansted",
    "ORK": "Cork"
  }
}
```

### 5. Download Scraping Results
```
GET /api/download/{filename}
```

**Example:** `GET /api/download/Ryanair_Jun2026_task123`

Returns an Excel file with the scraped data.

## Ryanair Scraper Details

### How It Works

1. **Initialization**: Creates a headless Chrome browser instance with Playwright
2. **Navigation**: Constructs URLs and navigates to Ryanair search pages
3. **Waiting**: Waits for React components to load and render
4. **Extraction**: Uses CSS selectors and JavaScript injection to extract flight data
5. **Parsing**: Converts HTML/JavaScript data into structured JSON
6. **Fallback**: If primary extraction fails, uses JavaScript evaluation

### Selectors Used

```python
selectors = {
    "flight_card": '[data-testid="flight-card"]',      # Container for each flight
    "price": '[data-testid="price"]',                   # Price element
    "departure_time": '[data-testid="departure-time"]', # Departure time
    "arrival_time": '[data-testid="arrival-time"]',     # Arrival time
    "duration": '[data-testid="duration"]',             # Flight duration
    "stops": '[data-testid="stops"]'                    # Number of stops
}
```

### Output Fields

Each flight record contains:

| Field | Type | Example |
|-------|------|---------|
| `airline` | string | "Ryanair" |
| `origin` | string | "DUB" |
| `destination` | string | "STN" |
| `date` | string | "2026-06-01" |
| `departure_time` | string | "14:00" |
| `arrival_time` | string | "15:30" |
| `duration` | string | "1h 30m" |
| `price` | float | 29.99 |
| `currency` | string | "EUR" |
| `stops` | string | "Non-stop" |
| `scraped_at` | string | "2026-05-18T11:45:30.654321" |

## Testing

### Run the Test Script

```bash
cd backend
python test_ryanair.py
```

**Expected Output:**
```
============================================================
AIRLINE CONFIGURATION TEST
============================================================

Ryanair Configuration:
  Base URL: https://www.ryanair.com
  Website Type: react
  Routes: 2
    - DUB -> STN
    - ORK -> STN
  Competitors: Wizz Air, Easyjet

============================================================
RYANAIR SCRAPER TEST
============================================================

Test Configuration:
  Routes: [{'origin': 'DUB', 'destination': 'STN'}]
  Date: 2026-05-19
  Passengers: 1

Starting scraper...
------------------------------------------------------------

✅ Scraping completed successfully!
📊 Found 15 flights

Sample Flight Data:
------------------------------------------------------------

Flight 1:
  airline              : Ryanair
  origin              : DUB
  destination         : STN
  date                : 2026-05-19
  departure_time      : 06:00
  arrival_time        : 07:30
  duration            : 1h 30m
  price               : 29.99
  currency            : EUR
  ...
```

## Error Handling

### Common Issues

1. **Selector Not Found**
   - Ryanair frequently updates their website
   - Selectors may need to be updated
   - Check browser DevTools to find current selectors

2. **Timeout Errors**
   - Website loading takes longer than expected
   - Increase `wait_until` timeout in scraper
   - Check internet connection

3. **Rate Limiting**
   - Ryanair may block requests if too many in quick succession
   - Add delays between requests (currently 2 seconds)
   - Use rotating proxies for large-scale scraping

4. **JavaScript Rendering Issues**
   - Some flights rendered via JavaScript
   - Fallback extraction method uses JavaScript evaluation
   - May need to wait longer for React to hydrate

### Logging

All scraping activities are logged to `backend/logs/`:
- Set log level in `backend/app/utils/logger.py`
- Check logs for detailed error messages

## Adding New Airlines

### Steps to Add a New Airline:

1. **Update airline_models.py**
   ```python
   AIRLINE_CONFIGS["NewAirline"] = {
       "base_url": "https://www.newairline.com",
       "website_type": "react|api_based",
       "routes": [...],
       "competitors": [...],
       "selectors": {...}
   }
   ```

2. **Create Scraper Class**
   ```python
   # backend/app/scraper/newairline_scraper.py
   class NewAirlineScraper:
       async def scrape(self, routes, start_date, end_date, num_passengers):
           # Implementation
           pass
   ```

3. **Update Routes**
   ```python
   # backend/app/routes/scraper_routes.py
   elif airline == "NewAirline":
       scraper = NewAirlineScraper()
       flights = await scraper.scrape(...)
   ```

4. **Test**
   ```bash
   python test_newairline.py
   ```

## Performance Considerations

### Optimization Tips

1. **Batch Processing**: Process multiple routes in parallel
2. **Caching**: Store airport codes and route info
3. **Date Ranges**: Limit date range to reduce API calls
4. **Connection Pooling**: Reuse browser connections
5. **Headless Mode**: Always use `headless=True` for production

### Resource Usage

- **Memory**: ~150-200MB per browser instance
- **CPU**: Minimal (delegated to browser)
- **Network**: ~1-5MB per scrape depending on flights
- **Time**: ~5-10 seconds per route/date

## Security Notes

⚠️ **Important**: Only use this scraper respectfully:

- ✅ Follow website's `robots.txt`
- ✅ Use appropriate delays between requests
- ✅ Respect rate limits
- ❌ Don't bypass CAPTCHA or anti-scraping measures
- ❌ Don't overload servers with excessive requests
- ✅ Use rotating user agents and IPs for large-scale scraping

## Future Enhancements

- [ ] Lufthansa scraper implementation
- [ ] Wizz Air scraper implementation
- [ ] Easyjet scraper implementation
- [ ] BA, Turkish, Air France scrapers
- [ ] Proxy rotation support
- [ ] CAPTCHA handling
- [ ] Database integration
- [ ] Real-time price alerts
- [ ] Historical data analysis
- [ ] ML-based price prediction

## Support

For issues or questions:
1. Check logs in `backend/logs/`
2. Run test script to verify setup
3. Check if website selectors have changed
4. Update selectors in `airline_models.py`

