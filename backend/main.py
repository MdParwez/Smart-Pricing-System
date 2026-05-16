from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os
from datetime import datetime, timedelta
import asyncio
from app.routes import scraper_routes
from app.scheduler.job_scheduler import scheduler
from app.utils.logger import logger

# Initialize FastAPI app
app = FastAPI(
    title="Flight Fare Intelligence API",
    description="Production-ready flight fare scraping dashboard API",
    version="1.0.0"
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routes
app.include_router(scraper_routes.router, prefix="/api", tags=["Scraper"])

# Startup and shutdown events
@app.on_event("startup")
async def startup_event():
    logger.info("Starting Flight Fare Intelligence API")
    scheduler.start()
    logger.info("Scheduler started")

@app.on_event("shutdown")
async def shutdown_event():
    logger.info("Shutting down Flight Fare Intelligence API")
    if scheduler.running:
        scheduler.shutdown()
    logger.info("Scheduler shut down")

# Health check
@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "scheduler_running": scheduler.running
    }

# Root endpoint
@app.get("/")
async def root():
    return {
        "name": "Flight Fare Intelligence API",
        "version": "1.0.0",
        "status": "running"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False
    )
