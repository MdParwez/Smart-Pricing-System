# API Testing Examples for Multi-Airline Scraping
# Copy-paste these commands to test the endpoints

# ===== 1. List Available Airlines =====
# GET http://localhost:8000/api/airlines/list
curl -X GET "http://localhost:8000/api/airlines/list" \
  -H "Content-Type: application/json"


# ===== 2. Get Airline Configuration =====
# GET http://localhost:8000/api/airlines/config/Ryanair
curl -X GET "http://localhost:8000/api/airlines/config/Ryanair" \
  -H "Content-Type: application/json"


# ===== 3. Start Multi-Airline Scraping =====
# POST http://localhost:8000/api/start-multi-airline-scrape
curl -X POST "http://localhost:8000/api/start-multi-airline-scrape" \
  -H "Content-Type: application/json" \
  -d '{
    "reportName": "Ryanair_Dublin_London_June",
    "reportDescription": "Ryanair and competitors pricing",
    "userNotes": "Monitoring Dublin to London route",
    "airline": "Ryanair",
    "origin": "DUB",
    "destination": "STN",
    "startDate": "2026-06-01",
    "endDate": "2026-06-15",
    "numPassengers": 1,
    "includeCompetitors": true,
    "currency": "EUR",
    "channel": "playwright"
  }'

# RESPONSE EXAMPLE (save the task_id):
# {
#   "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
#   "status": "running",
#   "message": "Multi-airline scraping started for Ryanair",
#   "started_at": "2026-05-18T10:30:45.123456"
# }


# ===== 4. Check Scraping Status =====
# GET http://localhost:8000/api/scraping-status/{task_id}
# Replace {task_id} with the ID from step 3
curl -X GET "http://localhost:8000/api/scraping-status/a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -H "Content-Type: application/json"

# RESPONSE EXAMPLE:
# {
#   "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
#   "status": "running",
#   "progress": 50,
#   "report_name": "Ryanair_Dublin_London_June",
#   "records_count": 450,
#   "airlines_scraped": ["Ryanair"],
#   "started_at": "2026-05-18T10:30:45.123456"
# }


# ===== 5. Get Scraping History =====
# GET http://localhost:8000/api/scraping-history
curl -X GET "http://localhost:8000/api/scraping-history" \
  -H "Content-Type: application/json"


# ===== 6. Download Results =====
# GET http://localhost:8000/api/download/{filename}
# Replace {filename} with the output filename from status check
curl -X GET "http://localhost:8000/api/download/Ryanair_Dublin_London_June_a1b2c3d4-e5f6-7890-abcd-ef1234567890" \
  -H "Content-Type: application/json" \
  --output ryanair_results.xlsx


# ===== POWERSHELL VERSIONS =====

# 1. List Airlines
$headers = @{
    "Content-Type" = "application/json"
}
Invoke-RestMethod -Uri "http://localhost:8000/api/airlines/list" -Method Get -Headers $headers

# 2. Get Airline Config
Invoke-RestMethod -Uri "http://localhost:8000/api/airlines/config/Ryanair" -Method Get -Headers $headers

# 3. Start Multi-Airline Scraping
$body = @{
    reportName = "Ryanair_Dublin_London_June"
    reportDescription = "Ryanair and competitors pricing"
    userNotes = "Monitoring Dublin to London route"
    airline = "Ryanair"
    origin = "DUB"
    destination = "STN"
    startDate = "2026-06-01"
    endDate = "2026-06-15"
    numPassengers = 1
    includeCompetitors = $true
    currency = "EUR"
    channel = "playwright"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/start-multi-airline-scrape" `
    -Method Post -Headers $headers -Body $body

# 4. Check Status
$taskId = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"  # Replace with actual task ID
Invoke-RestMethod -Uri "http://localhost:8000/api/scraping-status/$taskId" -Method Get -Headers $headers

# 5. Download Results
$taskId = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
$filename = "Ryanair_Dublin_London_June_${taskId}"
Invoke-WebRequest -Uri "http://localhost:8000/api/download/$filename" `
    -OutFile "ryanair_results.xlsx"
