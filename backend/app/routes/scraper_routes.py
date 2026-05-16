from fastapi import APIRouter, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd
import math
from app.utils.models import ScrapeRequest, ScheduleRequest
from app.scraper.playwright_scraper import PlaywrightScraper
from app.scheduler.job_scheduler import add_scrape_job
from app.utils.logger import logger

router = APIRouter()
BACKEND_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = BACKEND_ROOT / "outputs"

# In-memory task storage (replace with database in production)
scraping_tasks = {}

@router.post("/start-scrape")
async def start_scrape(request: ScrapeRequest, background_tasks: BackgroundTasks):
    """
    Start immediate scraping
    
    Args:
        request: Scraping request with all parameters
        background_tasks: FastAPI background tasks
        
    Returns:
        Task information with ID for tracking
    """
    try:
        task_id = str(uuid.uuid4())
        
        logger.info(f"Starting scrape task {task_id}: {request.reportName}")
        
        # Add background task
        background_tasks.add_task(
            run_scraper,
            task_id,
            request
        )
        
        # Store task info
        scraping_tasks[task_id] = {
            "id": task_id,
            "status": "running",
            "progress": 0,
            "report_name": request.reportName,
            "started_at": datetime.now(),
            "completed_at": None,
            "records_count": 0,
            "error": None
        }
        
        return {
            "task_id": task_id,
            "status": "running",
            "message": f"Scraping started for {request.reportName}",
            "started_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting scrape: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/schedule-scrape")
async def schedule_scrape(request: ScheduleRequest):
    """
    Schedule scraping for later
    
    Args:
        request: Scraping request with schedule information
        
    Returns:
        Scheduled task information
    """
    try:
        job_id = str(uuid.uuid4())
        
        # Parse datetime from request
        from datetime import datetime
        scheduled_date = datetime.fromisoformat(request.scheduleDate)
        scheduled_time = datetime.fromisoformat(request.scheduleTime)
        
        # Add job to scheduler
        success = add_scrape_job(
            job_id=job_id,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            timezone=request.timezone,
            task_data=request.dict()
        )
        
        if not success:
            raise HTTPException(status_code=500, detail="Failed to schedule job")
        
        logger.info(f"Scraping scheduled: {job_id} for {request.reportName}")
        
        return {
            "job_id": job_id,
            "status": "scheduled",
            "report_name": request.reportName,
            "scheduled_for": f"{request.scheduleDate} {request.scheduleTime} {request.timezone}",
            "message": "Scraping scheduled successfully"
        }
        
    except Exception as e:
        logger.error(f"Error scheduling scrape: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scraping-status/{task_id}")
async def get_scraping_status(task_id: str):
    """Get status of a scraping task"""
    if task_id not in scraping_tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return scraping_tasks[task_id]

@router.get("/download/{filename}")
async def download_file(filename: str):
    """Download generated Excel file"""
    try:
        safe_name = Path(filename).name
        filepath = OUTPUTS_DIR / f"{safe_name}.xlsx"
        
        if not filepath.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            str(filepath),
            filename=f"{safe_name}.xlsx",
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scraping-history")
async def get_scraping_history():
    """Get history of all scraping tasks"""
    return list(scraping_tasks.values())

@router.get("/fare-data/latest")
async def get_latest_fare_data():
    """Return rows from the newest completed scraper Excel output."""
    try:
        files = [
            path for path in OUTPUTS_DIR.glob("*.xlsx")
            if path.is_file() and not path.name.startswith("~$")
        ]
        if not files:
            raise HTTPException(status_code=404, detail="No scraper output files found")

        latest = max(files, key=lambda path: path.stat().st_mtime)
        return _read_fare_excel(latest)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading latest fare data: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/fare-data/{filename}")
async def get_fare_data(filename: str):
    """Return rows from a specific scraper Excel output."""
    try:
        safe_name = Path(filename).name
        if not safe_name.endswith(".xlsx"):
            safe_name = f"{safe_name}.xlsx"
        filepath = OUTPUTS_DIR / safe_name
        if not filepath.exists() or filepath.name.startswith("~$"):
            raise HTTPException(status_code=404, detail="File not found")

        return _read_fare_excel(filepath)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading fare data file: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

def _json_value(value):
    """Convert pandas/openpyxl values into API-safe JSON primitives."""
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if pd.isna(value):
        return None
    if isinstance(value, (pd.Timestamp, datetime)):
        return value.isoformat()
    return value

def _read_fare_excel(filepath: Path):
    df = pd.read_excel(filepath)
    rows = [
        {column: _json_value(value) for column, value in row.items()}
        for row in df.to_dict(orient="records")
    ]
    stat = filepath.stat()
    return {
        "filename": filepath.name,
        "record_count": len(rows),
        "updated_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "rows": rows,
    }

# Background task function
async def run_scraper(task_id: str, request: ScrapeRequest):
    """Execute scraper in background"""
    try:
        logger.info(f"Executing scrape task {task_id}")
        
        # Initialize scraper
        scraper = PlaywrightScraper()
        
        # Prepare routes
        routes = [(request.origin, request.destination)]
        
        # Determine airlines to scrape
        airlines = None
        if request.airline != "all":
            airlines = [request.airline]

        travel_dates = _build_travel_dates(request)
        logger.info(
            "Scrape task %s selected travel dates: %s",
            task_id,
            ", ".join(date.strftime("%d/%m/%Y") for date in travel_dates),
        )
        
        # Run scraper
        result = await scraper.scrape(
            routes=routes,
            airlines=airlines,
            dates=travel_dates
        )
        
        # Export to Excel
        filename = f"{request.reportName}_{task_id}"
        filepath = scraper.export_to_excel(result, filename)
        
        # Update task status
        scraping_tasks[task_id] = {
            **scraping_tasks[task_id],
            "status": "completed",
            "progress": 100,
            "records_count": len(result),
            "completed_at": datetime.now(),
            "output_file": filepath,
            "output_filename": f"{filename}.xlsx"
        }
        
        logger.info(f"Scrape task {task_id} completed with {len(result)} records")
        
    except Exception as e:
        logger.error(f"Error in scraping task {task_id}: {str(e)}")
        scraping_tasks[task_id] = {
            **scraping_tasks[task_id],
            "status": "error",
            "error": str(e),
            "completed_at": datetime.now()
        }

def _parse_request_date(value: str):
    """Parse UI date values from Dayjs/JSON into a local date."""
    if not value:
        return None
    text = str(value).strip()
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
        if parsed.tzinfo:
            ist = timezone(timedelta(hours=5, minutes=30))
            return parsed.astimezone(ist).date()
        return parsed.date()
    except ValueError:
        pass
    for fmt in ("%d/%m/%Y", "%Y-%m-%d"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    raise ValueError(f"Invalid date value: {value}")

def _build_travel_dates(request: ScrapeRequest):
    """Return the exact outbound dates selected in the dashboard."""
    start_date = _parse_request_date(request.outboundDateFrom)
    end_date = _parse_request_date(request.outboundDateTo) or start_date
    if not start_date:
        raise ValueError("Please select an outbound From date before starting a scrape")
    if end_date < start_date:
        start_date, end_date = end_date, start_date

    selected_weekdays = set(request.daysOfWeek or [])
    weekday_codes = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
    dates = []
    current = start_date
    while current <= end_date:
        weekday_code = weekday_codes[current.weekday()]
        if request.dateRange != "preferred" or not selected_weekdays or weekday_code in selected_weekdays:
            dates.append(datetime.combine(current, datetime.min.time()))
        current += timedelta(days=1)

    if not dates:
        raise ValueError("No travel dates matched the selected date range and weekdays")
    return dates
