from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from datetime import datetime

class PassengerType(BaseModel):
    adult: int = 1
    child: int = 0
    infant: int = 0

class ScrapeRequest(BaseModel):
    reportName: str
    reportDescription: Optional[str] = None
    userNotes: Optional[str] = None
    reportType: str = "standard"
    journeyType: str = "one-way"
    passengerType: PassengerType
    classOfService: str = "economy"
    stops: str = "non-stop"
    origin: str
    destination: str
    airline: str = "all"
    reverseOND: bool = False
    dateRange: str = "continuous"
    outboundDateFrom: Optional[str] = None
    outboundDateTo: Optional[str] = None
    inboundDateFrom: Optional[str] = None
    inboundDateTo: Optional[str] = None
    daysOfWeek: List[str] = Field(default_factory=list)
    departureTime: str = "any"
    considerFarthestDate: bool = False
    channel: str = "playwright"

class ScheduleRequest(ScrapeRequest):
    scheduleDate: Optional[str] = None
    scheduleTime: Optional[str] = None
    timezone: str = "IST"
    runOption: str = "schedule"

class ScrapingStatus(BaseModel):
    task_id: str
    status: str
    progress: int
    records_count: int
    started_at: datetime
    completed_at: Optional[datetime] = None
    error_message: Optional[str] = None

class ExcelExportResponse(BaseModel):
    filename: str
    url: str
    created_at: datetime
    record_count: int
