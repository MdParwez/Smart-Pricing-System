"""
Test script for Ryanair and Lufthansa scrapers
Run this from the backend directory: python test_ryanair.py
"""

import asyncio
from app.scraper.ryanair_scraper import RyanairScraper
from app.scraper.lufthansa_scraper import LufthansaScraper
from datetime import datetime, timedelta
import json

async def test_ryanair_scraper():
    """Test the Ryanair scraper with sample data"""
    
    print("\n" + "=" * 60)
    print("RYANAIR SCRAPER TEST")
    print("=" * 60)
    
    scraper = RyanairScraper()
    
    # Test Route 1: Dublin -> London
    routes = [
        {
            "origin": "DUB",
            "destination": "STN"  # Stansted
        }
    ]
    
    # Set date to tomorrow
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"\nTest Configuration:")
    print(f"  Routes: {routes}")
    print(f"  Date: {tomorrow}")
    print(f"  Passengers: 1")
    print(f"\nStarting scraper...")
    print("-" * 60)
    
    try:
        flights = await scraper.scrape(
            routes=routes,
            start_date=tomorrow,
            num_passengers=1
        )
        
        print(f"\n✅ Scraping completed successfully!")
        print(f"📊 Found {len(flights)} flights\n")
        
        if flights:
            print("Sample Flight Data:")
            print("-" * 60)
            for idx, flight in enumerate(flights[:3]):  # Show first 3
                print(f"\nFlight {idx + 1}:")
                for key, value in flight.items():
                    print(f"  {key:20}: {value}")
            
            if len(flights) > 3:
                print(f"\n... and {len(flights) - 3} more flights")
            
            # Summary statistics
            print("\n" + "=" * 60)
            print("RYANAIR SUMMARY:")
            print("=" * 60)
            print(f"Total flights found: {len(flights)}")
            
            prices = [f["price"] for f in flights if isinstance(f["price"], (int, float))]
            if prices:
                print(f"Price range: €{min(prices):.2f} - €{max(prices):.2f}")
                print(f"Average price: €{sum(prices)/len(prices):.2f}")
        else:
            print("⚠️  No flights found. This might be due to:")
            print("  - Website structure changes")
            print("  - Selectors need to be updated")
            print("  - No flights available for this route/date")
            
    except Exception as e:
        print(f"\n❌ Error during scraping:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()

async def test_lufthansa_scraper():
    """Test the Lufthansa scraper with sample data"""
    
    print("\n" + "=" * 60)
    print("LUFTHANSA SCRAPER TEST")
    print("=" * 60)
    
    scraper = LufthansaScraper()
    
    # Test Route: Frankfurt -> London
    routes = [
        {
            "origin": "FRA",
            "destination": "LHR"
        }
    ]
    
    # Set date to tomorrow
    tomorrow = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    
    print(f"\nTest Configuration:")
    print(f"  Routes: {routes}")
    print(f"  Date: {tomorrow}")
    print(f"  Passengers: 1")
    print(f"\nStarting scraper...")
    print("-" * 60)
    
    try:
        flights = await scraper.scrape(
            routes=routes,
            start_date=tomorrow,
            num_passengers=1
        )
        
        print(f"\n✅ Scraping completed successfully!")
        print(f"📊 Found {len(flights)} flights\n")
        
        if flights:
            print("Sample Flight Data:")
            print("-" * 60)
            for idx, flight in enumerate(flights[:3]):  # Show first 3
                print(f"\nFlight {idx + 1}:")
                for key, value in flight.items():
                    print(f"  {key:20}: {value}")
            
            if len(flights) > 3:
                print(f"\n... and {len(flights) - 3} more flights")
            
            # Summary statistics
            print("\n" + "=" * 60)
            print("LUFTHANSA SUMMARY:")
            print("=" * 60)
            print(f"Total flights found: {len(flights)}")
            
            prices = [f["price"] for f in flights if isinstance(f["price"], (int, float))]
            if prices:
                print(f"Price range: €{min(prices):.2f} - €{max(prices):.2f}")
                print(f"Average price: €{sum(prices)/len(prices):.2f}")
        else:
            print("⚠️  No flights found. This might be due to:")
            print("  - Website structure changes")
            print("  - Selectors need to be updated")
            print("  - Website blocking the scraper")
            
    except Exception as e:
        print(f"\n❌ Error during scraping:")
        print(f"  {str(e)}")
        import traceback
        traceback.print_exc()

async def test_airline_config():
    """Test airline configuration loading"""
    from app.utils.airline_models import (
        get_airline_config,
        get_competitors,
        get_airline_routes
    )
    
    print("\n" + "=" * 60)
    print("AIRLINE CONFIGURATION TEST")
    print("=" * 60)
    
    # Test Ryanair
    print("\n--- RYANAIR ---")
    config = get_airline_config("Ryanair")
    routes = get_airline_routes("Ryanair")
    competitors = get_competitors("Ryanair")
    
    print(f"Base URL: {config.get('base_url')}")
    print(f"Website Type: {config.get('website_type')}")
    print(f"Routes: {len(routes)}")
    for route in routes:
        print(f"  - {route['origin']} -> {route['destination']}")
    print(f"Competitors: {', '.join(competitors)}")
    
    # Test Lufthansa
    print("\n--- LUFTHANSA ---")
    config = get_airline_config("Lufthansa")
    routes = get_airline_routes("Lufthansa")
    competitors = get_competitors("Lufthansa")
    
    print(f"Base URL: {config.get('base_url')}")
    print(f"Website Type: {config.get('website_type')}")
    print(f"Routes: {len(routes)}")
    for route in routes:
        print(f"  - {route['origin']} -> {route['destination']}")
    print(f"Competitors: {', '.join(competitors)}")

async def test_database():
    """Test database initialization"""
    from app.database import init_db, SessionLocal, ScrapingTask, Flight
    
    print("\n" + "=" * 60)
    print("DATABASE TEST")
    print("=" * 60)
    
    try:
        init_db()
        print("✅ Database initialized successfully")
        
        db = SessionLocal()
        
        # Count existing records
        task_count = db.query(ScrapingTask).count()
        flight_count = db.query(Flight).count()
        
        print(f"📊 Scraping Tasks: {task_count}")
        print(f"📊 Flights: {flight_count}")
        
        # Show recent tasks
        recent_tasks = db.query(ScrapingTask).order_by(ScrapingTask.started_at.desc()).limit(5).all()
        if recent_tasks:
            print(f"\n📋 Recent Tasks:")
            for task in recent_tasks:
                print(f"  - {task.report_name} ({task.status}): {task.records_count} flights")
        
        db.close()
        
    except Exception as e:
        print(f"❌ Error testing database: {str(e)}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests"""
    print("\n" + "🚀 " * 10)
    print("FLIGHT SCRAPER TEST SUITE")
    print("🚀 " * 10)
    
    # Test configuration
    await test_airline_config()
    
    # Test database
    await test_database()
    
    # Test Ryanair
    await test_ryanair_scraper()
    
    # Test Lufthansa
    await test_lufthansa_scraper()
    
    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETED")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
