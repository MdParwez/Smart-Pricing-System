from fastapi import APIRouter, BackgroundTasks, HTTPException, Depends
from fastapi.responses import FileResponse
import os
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
import pandas as pd
import math
import json
from sqlalchemy.orm import Session
from app.utils.models import ScrapeRequest, ScheduleRequest, MultiAirlineScrapeRequest
from app.scraper.playwright_scraper import PlaywrightScraper
from app.scraper.ryanair_scraper import RyanairScraper
from app.scraper.lufthansa_scraper import LufthansaScraper
from app.scheduler.job_scheduler import add_scrape_job
from app.utils.logger import logger
from app.utils.airline_models import get_airline_config, get_competitors, get_airline_routes
from app.database import get_db, ScrapingTask, Flight, PriceHistory, init_db

router = APIRouter()
BACKEND_ROOT = Path(__file__).resolve().parents[2]
OUTPUTS_DIR = BACKEND_ROOT / "outputs"
DEBUG_DIR = OUTPUTS_DIR / "debug"

# Initialize database on startup
init_db()

# In-memory task storage (for quick reference, real data in database)
scraping_tasks = {}

def _numeric_price(value):
    """Return a float price or None when scraper output is not numeric."""
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if math.isnan(value) or math.isinf(value):
            return None
        return float(value)
    try:
        return float(str(value).replace(",", "").strip())
    except (TypeError, ValueError):
        return None

def _excel_flight_row(flight_data: dict, task_id: str, scrape_status: str = "scraped") -> dict:
    """Normalize any scraper output into an Excel-friendly row."""
    return {
        "task_id": task_id,
        "scrape_status": scrape_status,
        "airline": flight_data.get("airline"),
        "origin": flight_data.get("origin"),
        "destination": flight_data.get("destination"),
        "date": flight_data.get("date"),
        "departure_time": flight_data.get("departure_time"),
        "arrival_time": flight_data.get("arrival_time"),
        "duration": flight_data.get("duration"),
        "price": flight_data.get("price"),
        "currency": flight_data.get("currency", "EUR"),
        "stops": flight_data.get("stops"),
        "flight_number": flight_data.get("flight_number"),
        "booking_url": flight_data.get("booking_url"),
        "page_title": flight_data.get("page_title"),
        "flight_card_count": flight_data.get("flight_card_count"),
        "debug_screenshot": flight_data.get("debug_screenshot"),
        "debug_html": flight_data.get("debug_html"),
        "scraped_at": flight_data.get("scraped_at") or datetime.now().isoformat(),
    }

def _empty_excel_row(request: MultiAirlineScrapeRequest, task_id: str, airline: str, status: str) -> dict:
    """Create a trace row when an airline produced no usable flight records."""
    return _excel_flight_row(
        {
            "airline": airline,
            "origin": request.origin,
            "destination": request.destination,
            "date": f"{request.startDate} to {request.endDate or request.startDate}",
        },
        task_id,
        status,
    )

def _export_multi_airline_excel(rows: list, request: MultiAirlineScrapeRequest, task_id: str):
    """Always write an Excel workbook, even when every scraper returned zero flights."""
    filename = f"{request.reportName}_{task_id}"
    os.makedirs(OUTPUTS_DIR, exist_ok=True)
    filepath = OUTPUTS_DIR / f"{filename}.xlsx"
    df = pd.DataFrame(rows)
    df.to_excel(filepath, index=False)
    return filepath, f"{filename}.xlsx"

def _debug_artifacts_from_rows(rows: list) -> list:
    artifacts = []
    seen = set()
    for row in rows:
        for key in ("debug_screenshot", "debug_html"):
            value = row.get(key)
            if not value:
                continue
            name = Path(value).name
            if name in seen:
                continue
            seen.add(name)
            artifacts.append({
                "type": "screenshot" if key == "debug_screenshot" else "html",
                "filename": name,
                "url": f"/api/debug-artifact/{name}",
            })
    return artifacts

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

@router.get("/debug-artifact/{filename}")
async def get_debug_artifact(filename: str):
    """Download or view a captured scraper debug artifact."""
    try:
        safe_name = Path(filename).name
        filepath = DEBUG_DIR / safe_name
        if not filepath.exists() or filepath.suffix.lower() not in {".png", ".html"}:
            raise HTTPException(status_code=404, detail="Debug artifact not found")
        media_type = "image/png" if filepath.suffix.lower() == ".png" else "text/html"
        return FileResponse(str(filepath), filename=safe_name, media_type=media_type)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error reading debug artifact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/scraping-history")
async def get_scraping_history():
    """Get history of all scraping tasks"""
    return list(scraping_tasks.values())

@router.post("/start-multi-airline-scrape")
async def start_multi_airline_scrape(request: MultiAirlineScrapeRequest, background_tasks: BackgroundTasks):
    """
    Start multi-airline scraping (main airline + competitors)
    
    Args:
        request: Multi-airline scraping request
        background_tasks: FastAPI background tasks
        
    Returns:
        Task information with ID for tracking
    """
    try:
        task_id = str(uuid.uuid4())
        
        logger.info(f"Starting multi-airline scrape task {task_id}: {request.reportName} ({request.airline})")
        
        # Add background task
        background_tasks.add_task(
            run_multi_airline_scraper,
            task_id,
            request
        )
        
        # Store task info
        scraping_tasks[task_id] = {
            "id": task_id,
            "status": "running",
            "progress": 0,
            "report_name": request.reportName,
            "airline": request.airline,
            "origin": request.origin,
            "destination": request.destination,
            "start_date": request.startDate,
            "end_date": request.endDate or request.startDate,
            "include_competitors": request.includeCompetitors,
            "started_at": datetime.now().isoformat(),
            "completed_at": None,
            "records_count": 0,
            "airlines_scraped": [],
            "error": None,
            "output_file": None
        }
        
        return {
            "task_id": task_id,
            "status": "running",
            "message": f"Multi-airline scraping started for {request.airline}",
            "started_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error starting multi-airline scrape: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/airlines/config/{airline_name}")
async def get_airline_configuration(airline_name: str):
    """Get configuration and routes for a specific airline"""
    try:
        config = get_airline_config(airline_name)
        if not config:
            raise HTTPException(status_code=404, detail=f"Airline {airline_name} not configured")
        
        return {
            "airline": airline_name,
            "base_url": config.get("base_url"),
            "website_type": config.get("website_type"),
            "routes": config.get("routes", []),
            "competitors": config.get("competitors", []),
            "airport_codes": config.get("airport_codes", {})
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting airline config: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/airlines/list")
async def list_available_airlines():
    """List all configured airlines"""
    from app.utils.airline_models import AIRLINE_CONFIGS
    return {
        "airlines": list(AIRLINE_CONFIGS.keys()),
        "total": len(AIRLINE_CONFIGS)
    }

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

async def run_multi_airline_scraper(task_id: str, request: MultiAirlineScrapeRequest):
    """Execute multi-airline scraping in background with database integration"""
    db = next(get_db())
    excel_rows = []
    
    try:
        logger.info(f"Executing multi-airline scrape task {task_id}")
        
        all_flights = []
        airlines_to_scrape = [request.airline]
        
        # Add competitors if requested
        if request.includeCompetitors:
            competitors = get_competitors(request.airline)
            airlines_to_scrape.extend(competitors)
        
        logger.info(f"Scraping airlines: {airlines_to_scrape}")
        
        # Create database record
        db_task = ScrapingTask(
            id=task_id,
            report_name=request.reportName,
            report_description=request.reportDescription,
            user_notes=request.userNotes,
            airline=request.airline,
            origin=request.origin,
            destination=request.destination,
            start_date=request.startDate,
            end_date=request.endDate or request.startDate,
            num_passengers=request.numPassengers,
            include_competitors=request.includeCompetitors,
            status="running",
            progress=0,
            airlines_scraped=json.dumps([])
        )
        db.add(db_task)
        db.commit()
        
        # Scrape each airline
        scraped_airlines = []
        for idx, airline in enumerate(airlines_to_scrape):
            try:
                logger.info(f"Starting scrape for {airline}")
                
                # Route specification
                route = {
                    "origin": request.origin,
                    "destination": request.destination
                }
                
                flights = []
                scraper = None
                
                if airline == "Ryanair":
                    scraper = RyanairScraper(task_id=task_id, debug_dir=DEBUG_DIR)
                    flights = await scraper.scrape(
                        routes=[route],
                        start_date=request.startDate,
                        end_date=request.endDate or request.startDate,
                        num_passengers=request.numPassengers
                    )
                elif airline == "Lufthansa":
                    scraper = LufthansaScraper(task_id=task_id, debug_dir=DEBUG_DIR)
                    flights = await scraper.scrape(
                        routes=[route],
                        start_date=request.startDate,
                        end_date=request.endDate or request.startDate,
                        num_passengers=request.numPassengers
                    )
                else:
                    logger.info(f"Scraper for {airline} not yet implemented")
                    flights = []

                if flights:
                    excel_rows.extend([
                        _excel_flight_row(flight_data, task_id)
                        for flight_data in flights
                    ])
                else:
                    debug_records = getattr(scraper, "debug_records", []) if scraper else []
                    if debug_records:
                        excel_rows.extend([
                            _excel_flight_row(record, task_id, record.get("scrape_status", "no_flights_found"))
                            for record in debug_records
                        ])
                    else:
                        excel_rows.append(_empty_excel_row(request, task_id, airline, "no_flights_found"))
                
                # Save flights to database
                for flight_data in flights:
                    price = _numeric_price(flight_data.get("price"))
                    if price is None:
                        logger.debug("Skipping flight without numeric price: %s", flight_data)
                        continue

                    flight = Flight(
                        task_id=task_id,
                        airline=flight_data.get("airline"),
                        origin=flight_data.get("origin"),
                        destination=flight_data.get("destination"),
                        departure_date=flight_data.get("date"),
                        departure_time=flight_data.get("departure_time"),
                        arrival_time=flight_data.get("arrival_time"),
                        duration=flight_data.get("duration"),
                        price=price,
                        currency=flight_data.get("currency", "EUR"),
                        stops=flight_data.get("stops"),
                        flight_number=flight_data.get("flight_number"),
                        booking_url=flight_data.get("booking_url"),
                        scraped_at=datetime.now()
                    )
                    db.add(flight)
                
                all_flights.extend([
                    _excel_flight_row({**flight_data, "price": _numeric_price(flight_data.get("price"))}, task_id)
                    for flight_data in flights
                    if _numeric_price(flight_data.get("price")) is not None
                ])
                scraped_airlines.append(airline)
                
                # Update progress
                progress = int((idx + 1) / len(airlines_to_scrape) * 100)
                db_task.progress = progress
                db_task.records_count = len(all_flights)
                db_task.airlines_scraped = json.dumps(scraped_airlines)
                db.commit()
                
                logger.info(f"Completed scrape for {airline}: {len(flights)} flights found")
                
            except Exception as e:
                logger.error(f"Error scraping {airline}: {str(e)}")
                excel_rows.append(_empty_excel_row(request, task_id, airline, f"scrape_error: {str(e)}"))
                continue
        
        # Export to Excel. Keep raw scraper rows here, including rows without numeric prices.
        filepath, output_filename = _export_multi_airline_excel(excel_rows, request, task_id)
        debug_artifacts = _debug_artifacts_from_rows(excel_rows)
        logger.info(f"Exported {len(excel_rows)} raw scrape rows to {filepath}")

        # Update task status in database
        db_task.status = "completed"
        db_task.progress = 100
        db_task.records_count = len(all_flights)
        db_task.completed_at = datetime.utcnow()
        db_task.output_file = str(filepath)
        db_task.airlines_scraped = json.dumps(scraped_airlines)
        if not all_flights:
            db_task.error_message = "No numeric fare records found; raw scrape status was exported to Excel."
        db.commit()

        # Update in-memory tracking
        scraping_tasks[task_id] = {
            **scraping_tasks[task_id],
            "status": "completed",
            "progress": 100,
            "records_count": len(all_flights),
            "raw_records_count": len(excel_rows),
            "completed_at": datetime.now().isoformat(),
            "output_file": str(filepath),
            "output_filename": output_filename,
            "debug_artifacts": debug_artifacts,
            "airlines_scraped": scraped_airlines,
            "message": None if all_flights else "No numeric fares found; raw scrape status was saved to Excel."
        }
        
        logger.info(f"Multi-airline scrape task {task_id} completed with {len(all_flights)} total records")
        
    except Exception as e:
        logger.error(f"Error in multi-airline scraping task {task_id}: {str(e)}")

        output_file = None
        output_filename = None
        if excel_rows:
            try:
                output_file, output_filename = _export_multi_airline_excel(excel_rows, request, task_id)
                debug_artifacts = _debug_artifacts_from_rows(excel_rows)
                logger.info(f"Exported {len(excel_rows)} partial rows after failure to {output_file}")
            except Exception as export_error:
                logger.error(f"Could not export partial scrape rows: {export_error}")
                debug_artifacts = []
        else:
            debug_artifacts = []
        
        # Update database with error
        try:
            db_task = db.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
            if db_task:
                db_task.status = "failed"
                db_task.error_message = str(e)
                db_task.completed_at = datetime.utcnow()
                if output_file:
                    db_task.output_file = str(output_file)
                db.commit()
        except Exception as db_error:
            logger.error(f"Error updating task status in DB: {db_error}")
        
        # Update in-memory tracking
        scraping_tasks[task_id] = {
            **scraping_tasks[task_id],
            "status": "failed",
            "error": str(e),
            "completed_at": datetime.now().isoformat(),
            "raw_records_count": len(excel_rows),
            "output_file": str(output_file) if output_file else None,
            "output_filename": output_filename,
            "debug_artifacts": debug_artifacts
        }
    finally:
        db.close()

@router.get("/flights/search")
async def search_flights(
    origin: str,
    destination: str,
    min_price: float = 0,
    max_price: float = 10000,
    db: Session = Depends(get_db)
):
    """Search for scraped flights by route and price"""
    try:
        flights = db.query(Flight).filter(
            Flight.origin == origin,
            Flight.destination == destination,
            Flight.price >= min_price,
            Flight.price <= max_price
        ).order_by(Flight.price.asc()).limit(100).all()
        
        return {
            "flights": [
                {
                    "id": f.id,
                    "airline": f.airline,
                    "departure_time": f.departure_time,
                    "arrival_time": f.arrival_time,
                    "price": f.price,
                    "currency": f.currency,
                    "duration": f.duration,
                    "date": f.departure_date,
                    "scraped_at": f.scraped_at.isoformat()
                }
                for f in flights
            ],
            "total": len(flights)
        }
    except Exception as e:
        logger.error(f"Error searching flights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/flights/stats/{origin}/{destination}")
async def get_flight_statistics(
    origin: str,
    destination: str,
    db: Session = Depends(get_db)
):
    """Get price statistics for a route"""
    try:
        flights = db.query(Flight).filter(
            Flight.origin == origin,
            Flight.destination == destination
        ).all()
        
        if not flights:
            return {
                "origin": origin,
                "destination": destination,
                "message": "No flights found"
            }
        
        prices = [f.price for f in flights if _numeric_price(f.price) is not None]
        airlines = set([f.airline for f in flights])

        if not prices:
            return {
                "origin": origin,
                "destination": destination,
                "total_flights": len(flights),
                "message": "No numeric prices found"
            }

        by_airline = {}
        for airline in airlines:
            airline_flights = [f for f in flights if f.airline == airline]
            airline_prices = [f.price for f in airline_flights if _numeric_price(f.price) is not None]
            if not airline_prices:
                continue
            by_airline[airline] = {
                "count": len(airline_flights),
                "min_price": min(airline_prices),
                "avg_price": sum(airline_prices) / len(airline_prices)
            }
        
        return {
            "origin": origin,
            "destination": destination,
            "total_flights": len(flights),
            "airlines_count": len(airlines),
            "airlines": list(airlines),
            "price_stats": {
                "minimum": min(prices),
                "maximum": max(prices),
                "average": sum(prices) / len(prices),
                "median": sorted(prices)[len(prices)//2]
            },
            "by_airline": by_airline
        }
    except Exception as e:
        logger.error(f"Error getting flight statistics: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/flights/history/{task_id}")
async def get_task_flights(
    task_id: str,
    db: Session = Depends(get_db)
):
    """Get all flights for a specific scraping task"""
    try:
        task = db.query(ScrapingTask).filter(ScrapingTask.id == task_id).first()
        if not task:
            raise HTTPException(status_code=404, detail="Task not found")
        
        flights = db.query(Flight).filter(Flight.task_id == task_id).all()
        
        return {
            "task_id": task_id,
            "report_name": task.report_name,
            "airline": task.airline,
            "status": task.status,
            "records_count": len(flights),
            "flights": [
                {
                    "airline": f.airline,
                    "origin": f.origin,
                    "destination": f.destination,
                    "date": f.departure_date,
                    "flight_number": f.flight_number,
                    "departure_time": f.departure_time,
                    "arrival_time": f.arrival_time,
                    "duration": f.duration,
                    "price": f.price,
                    "currency": f.currency,
                    "stops": f.stops
                }
                for f in flights
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting task flights: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

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
