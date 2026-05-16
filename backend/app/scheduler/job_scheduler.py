from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.date import DateTrigger
from datetime import datetime
import pytz
from app.utils.logger import logger

scheduler = BackgroundScheduler()

def add_scrape_job(job_id: str, scheduled_date: datetime, scheduled_time: datetime, timezone: str, task_data: dict):
    """
    Add a scraping job to the scheduler
    
    Args:
        job_id: Unique job identifier
        scheduled_date: Date to run the job
        scheduled_time: Time to run the job
        timezone: Timezone string (e.g., 'IST', 'UTC')
        task_data: Data to pass to the scraping function
    """
    try:
        tz = pytz.timezone('Asia/Kolkata' if timezone == 'IST' else timezone)
        
        # Combine date and time
        combined_datetime = datetime.combine(
            scheduled_date.date() if hasattr(scheduled_date, 'date') else scheduled_date,
            scheduled_time.time() if hasattr(scheduled_time, 'time') else scheduled_time
        )
        combined_datetime = tz.localize(combined_datetime)
        
        # Add job to scheduler
        scheduler.add_job(
            run_scraper_task,
            DateTrigger(run_date=combined_datetime),
            id=job_id,
            args=[task_data],
            misfire_grace_time=300  # 5 minutes grace period
        )
        
        logger.info(f"Job {job_id} scheduled for {combined_datetime}")
        return True
        
    except Exception as e:
        logger.error(f"Error scheduling job: {str(e)}")
        return False

def run_scraper_task(task_data: dict):
    """Execute the scraper task"""
    from app.scraper.playwright_scraper import PlaywrightScraper
    from app.routes.scraper_routes import _build_travel_dates
    from app.utils.models import ScrapeRequest
    
    try:
        logger.info(f"Running scheduled scrape task: {task_data.get('reportName')}")
        
        scraper = PlaywrightScraper()
        request = ScrapeRequest(**task_data)
        result = asyncio.run(scraper.scrape(
            routes=[(request.origin, request.destination)],
            airlines=[request.airline] if request.airline != 'all' else None,
            dates=_build_travel_dates(request)
        ))
        
        logger.info(f"Scheduled scrape completed. Records: {len(result)}")
        
    except Exception as e:
        logger.error(f"Error in scheduled scrape task: {str(e)}")

def get_job_status(job_id: str):
    """Get the status of a scheduled job"""
    job = scheduler.get_job(job_id)
    if not job:
        return None
    return {
        "job_id": job.id,
        "next_run_time": job.next_run_time.isoformat() if job.next_run_time else None,
        "status": "pending"
    }

def remove_job(job_id: str):
    """Remove a scheduled job"""
    try:
        scheduler.remove_job(job_id)
        logger.info(f"Job {job_id} removed")
        return True
    except Exception as e:
        logger.error(f"Error removing job: {str(e)}")
        return False

import asyncio
