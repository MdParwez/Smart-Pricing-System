"""
Database models and setup for flight data storage
Using SQLite with SQLAlchemy ORM
"""

from sqlalchemy import create_engine, Column, String, Float, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Database setup
DATABASE_URL = "sqlite:///./flight_fares.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


class ScrapingTask(Base):
    """Track scraping tasks"""
    __tablename__ = "scraping_tasks"
    
    id = Column(String, primary_key=True, index=True)
    report_name = Column(String, index=True)
    report_description = Column(String, nullable=True)
    user_notes = Column(String, nullable=True)
    airline = Column(String, index=True)
    origin = Column(String)
    destination = Column(String)
    start_date = Column(String)
    end_date = Column(String)
    num_passengers = Column(Integer, default=1)
    include_competitors = Column(Boolean, default=True)
    status = Column(String)  # "running", "completed", "failed"
    progress = Column(Integer, default=0)
    records_count = Column(Integer, default=0)
    airlines_scraped = Column(String)  # JSON string of list
    error_message = Column(String, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)
    output_file = Column(String, nullable=True)
    
    # Relationships
    flights = relationship("Flight", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ScrapingTask(id={self.id}, airline={self.airline}, status={self.status})>"


class Flight(Base):
    """Store scraped flight data"""
    __tablename__ = "flights"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, ForeignKey("scraping_tasks.id"), index=True)
    airline = Column(String, index=True)
    origin = Column(String, index=True)
    destination = Column(String, index=True)
    departure_date = Column(String, index=True)  # "2026-06-01"
    departure_time = Column(String)  # "14:00"
    arrival_time = Column(String)  # "15:30"
    duration = Column(String)  # "1h 30m"
    price = Column(Float, index=True)
    currency = Column(String, default="EUR")
    stops = Column(String)  # "Non-stop", "1 stop", etc.
    flight_number = Column(String, nullable=True)
    booking_url = Column(String, nullable=True)
    scraped_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Relationships
    task = relationship("ScrapingTask", back_populates="flights")
    
    def __repr__(self):
        return f"<Flight(airline={self.airline}, {self.origin}->{self.destination}, price={self.price})>"


class PriceHistory(Base):
    """Track price history for analysis"""
    __tablename__ = "price_history"
    
    id = Column(Integer, primary_key=True, index=True)
    airline = Column(String, index=True)
    origin = Column(String, index=True)
    destination = Column(String, index=True)
    departure_date = Column(String, index=True)
    lowest_price = Column(Float)
    average_price = Column(Float)
    highest_price = Column(Float)
    flight_count = Column(Integer)
    currency = Column(String, default="EUR")
    recorded_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<PriceHistory({self.airline}, {self.origin}->{self.destination}, {self.lowest_price})>"


def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")


def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
