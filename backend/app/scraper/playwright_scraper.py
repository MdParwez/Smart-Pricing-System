from playwright.async_api import async_playwright
import asyncio
import pandas as pd
from datetime import datetime, timedelta
import re
from typing import Iterable, List, Optional, Tuple
import json
import os
from app.utils.logger import logger

class PlaywrightScraper:
    def __init__(self):
        self.airlines = ["IndiGo", "Air India Express", "Air India", "SpiceJet", "Akasa Air", "Vistara"]
        self.airline_codes = {
            "IndiGo": "6E",
            "Air India": "AI",
            "SpiceJet": "SG",
            "Air India Express": "IX",
            "Akasa Air": "QP",
            "Vistara": "UK",
        }
        self.base_url = "https://www.makemytrip.com/flight/search"
        self.airport_codes = {
            "DELHI": "DEL",
            "NEW DELHI": "DEL",
            "DEL": "DEL",
            "MUMBAI": "BOM",
            "BOMBAY": "BOM",
            "BOM": "BOM",
            "BENGALURU": "BLR",
            "BANGALORE": "BLR",
            "BLR": "BLR",
            "CHENNAI": "MAA",
            "MAA": "MAA",
            "KOLKATA": "CCU",
            "CALCUTTA": "CCU",
            "CCU": "CCU",
            "HYDERABAD": "HYD",
            "HYD": "HYD",
            "PUNE": "PNQ",
            "PNQ": "PNQ",
            "GOA": "GOI",
            "GOI": "GOI",
            "AHMEDABAD": "AMD",
            "AMD": "AMD",
        }

    async def scrape(
        self,
        routes: List[Tuple[str, str]],
        airlines: Optional[List[str]] = None,
        days: int = 30,
        dates: Optional[Iterable[datetime]] = None,
    ) -> List[dict]:
        """
        Scrape flight prices from MakeMyTrip
        
        Args:
            routes: List of (origin, destination) tuples
            airlines: Specific airlines to scrape (None = all)
            days: Number of days to scrape when dates are not provided
            dates: Exact travel dates to scrape
            
        Returns:
            List of flight records
        """
        all_data = []
        normalized_routes = self._normalize_routes(routes)
        flights_to_scrape = self._prepare_flights(normalized_routes, days=days, dates=dates)
        
        async with async_playwright() as p:
            launch_options = {
                "headless": False,
                "slow_mo": 500,
            }
            chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
            if os.path.exists(chrome_path):
                launch_options["executable_path"] = chrome_path

            browser = await p.chromium.launch(**launch_options)
            context = await browser.new_context()
            
            # MMT is sensitive to many parallel tabs and often never reaches networkidle.
            batch_size = 2
            for i in range(0, len(flights_to_scrape), batch_size):
                batch = flights_to_scrape[i:i+batch_size]
                logger.info(f"Processing batch {i//batch_size + 1} of {(len(flights_to_scrape)-1)//batch_size + 1}")
                
                tasks = [
                    self._scrape_route(
                        await context.new_page(),
                        flight['origin'],
                        flight['destination'],
                        flight['date'],
                        all_data,
                        airlines
                    )
                    for flight in batch
                ]
                
                await asyncio.gather(*tasks, return_exceptions=True)
            
            await context.close()
            await browser.close()
        
        return all_data

    def _normalize_routes(self, routes: List[Tuple[str, str]]) -> List[Tuple[str, str]]:
        """Convert city names from the UI into MMT airport codes."""
        normalized = []
        for origin, destination in routes:
            origin_code = self._normalize_airport(origin)
            destination_code = self._normalize_airport(destination)
            if not origin_code or not destination_code:
                logger.error(
                    f"Invalid route values: origin={origin!r}, destination={destination!r}"
                )
                continue
            normalized.append((origin_code, destination_code))
        return normalized

    def _normalize_airport(self, value: str) -> Optional[str]:
        if not value:
            return None
        cleaned = value.strip().upper()
        return self.airport_codes.get(cleaned, cleaned if len(cleaned) == 3 else None)

    def _prepare_flights(
        self,
        routes: List[Tuple[str, str]],
        days: int,
        dates: Optional[Iterable[datetime]] = None,
    ) -> List[dict]:
        """Prepare flight search list"""
        flights = []
        travel_dates = list(dates or [])
        if not travel_dates:
            today = datetime.today()
            travel_dates = [today + timedelta(days=day_offset) for day_offset in range(days)]
        
        for origin, destination in routes:
            for travel_date in travel_dates:
                flight_date = travel_date.strftime("%d/%m/%Y")
                flights.append({
                    'origin': origin,
                    'destination': destination,
                    'date': flight_date
                })
        
        return flights

    async def _scrape_route(
        self,
        page,
        origin: str,
        dest: str,
        flight_date: str,
        all_data: list,
        airlines: Optional[List[str]] = None,
    ):
        """Scrape a single route"""
        try:
            url = f"{self.base_url}?itinerary={origin}-{dest}-{flight_date}&tripType=O&paxType=A-1_C-0_I-0&intl=false&cabinClass=E"
            
            logger.info(f"Loading {origin}-{dest} {flight_date}")
            
            await page.goto(url, timeout=90000, wait_until="domcontentloaded")
            await page.wait_for_timeout(10000)
            
            # Close popup
            try:
                await page.click("button[data-cy='closeModal']", timeout=2000)
            except:
                pass
            
            await page.wait_for_timeout(1000)
            
            selectors = "div.fli-list, div.listingCard"
            records = {}
            stable_rounds = 0
            last_record_count = 0

            for scroll_round in range(80):
                card_count = await self._collect_visible_flights(
                    page=page,
                    selectors=selectors,
                    records=records,
                    origin=origin,
                    dest=dest,
                    flight_date=flight_date,
                    airlines=airlines,
                )

                scroll_state = await self._scroll_results_page(page)
                await page.wait_for_timeout(1200)

                if len(records) == last_record_count:
                    stable_rounds += 1
                else:
                    stable_rounds = 0
                    last_record_count = len(records)

                logger.info(
                    "Scroll %s for %s-%s %s: visible_cards=%s unique_records=%s bottom=%s",
                    scroll_round + 1,
                    origin,
                    dest,
                    flight_date,
                    card_count,
                    len(records),
                    scroll_state.get("at_bottom"),
                )

                if len(records) > 0 and scroll_state.get("at_bottom") and stable_rounds >= 5:
                    break

            # Final pass catches cards revealed by the last scroll.
            await self._collect_visible_flights(
                page=page,
                selectors=selectors,
                records=records,
                origin=origin,
                dest=dest,
                flight_date=flight_date,
                airlines=airlines,
            )

            all_data.extend(records.values())
            logger.info(
                "Captured %s unique flights for %s-%s %s",
                len(records),
                origin,
                dest,
                flight_date,
            )
            
            await page.close()
            
        except Exception as e:
            logger.error(f"Error scraping {origin}-{dest}: {str(e)}")

    async def _collect_visible_flights(
        self,
        page,
        selectors: str,
        records: dict,
        origin: str,
        dest: str,
        flight_date: str,
        airlines: Optional[List[str]] = None,
    ) -> int:
        """Collect currently rendered flight cards into records."""
        flights = await page.query_selector_all(selectors)
        for flight in flights:
            try:
                text = await flight.inner_text()
                airline = self._extract_airline(text)
                price = self._extract_price(text)
                times = self._extract_times(text)

                if not airline or not price:
                    continue

                code = self.airline_codes.get(airline)
                if airlines and airline not in airlines and code not in airlines:
                    continue

                record_key = (
                    origin,
                    dest,
                    flight_date,
                    code or airline,
                    times.get("departure"),
                    times.get("arrival"),
                    price,
                )
                if record_key in records:
                    continue

                records[record_key] = {
                    "Origin": origin,
                    "Destination": dest,
                    "Flight Date": flight_date,
                    "Airline": airline,
                    "Airline Code": code,
                    "Price": price,
                    "Departure Time": times.get("departure"),
                    "Arrival Time": times.get("arrival"),
                    "Scraped Date": datetime.today().strftime("%d/%m/%Y"),
                    "Base Fare": int(price * 0.8),
                    "Taxes": int(price * 0.12),
                    "Surcharge": int(price * 0.08),
                }
            except Exception as e:
                logger.error(f"Error parsing flight: {str(e)}")
                continue
        return len(flights)

    async def _scroll_results_page(self, page) -> dict:
        """Scroll the main document and the largest scrollable listing container."""
        return await page.evaluate(
            """
            () => {
              const doc = document.scrollingElement || document.documentElement;
              const card = document.querySelector('div.fli-list, div.listingCard');
              let cardScroller = null;
              let node = card ? card.parentElement : null;
              while (node && node !== document.body) {
                const style = window.getComputedStyle(node);
                const canScroll = /(auto|scroll|overlay)/.test(style.overflowY) || node.scrollHeight > node.clientHeight + 40;
                if (canScroll && node.scrollHeight > node.clientHeight + 40) {
                  cardScroller = node;
                  break;
                }
                node = node.parentElement;
              }
              const elements = [doc, ...Array.from(document.querySelectorAll('main, section, div'))];
              const largestScroller = elements
                .filter(el => el && el.scrollHeight > el.clientHeight + 40)
                .sort((a, b) => (b.scrollHeight - b.clientHeight) - (a.scrollHeight - a.clientHeight))[0];
              const target = cardScroller || largestScroller || doc;
              const step = Math.max(window.innerHeight * 0.85, target.clientHeight * 0.85, 700);

              target.scrollTop = Math.min(target.scrollTop + step, target.scrollHeight);
              window.scrollBy(0, step);

              const docBottom = Math.ceil(window.scrollY + window.innerHeight) >= doc.scrollHeight - 8;
              const targetBottom = Math.ceil(target.scrollTop + target.clientHeight) >= target.scrollHeight - 8;

              return {
                scroll_top: target.scrollTop,
                scroll_height: target.scrollHeight,
                client_height: target.clientHeight,
                window_y: window.scrollY,
                document_height: doc.scrollHeight,
                at_bottom: docBottom || targetBottom
              };
            }
            """
        )

    def _extract_airline(self, text: str) -> Optional[str]:
        """Extract airline name from flight text"""
        for airline in self.airlines:
            if airline.lower() in text.lower():
                return airline
        return None

    def _extract_price(self, text: str) -> Optional[int]:
        """Extract price from flight text"""
        match = re.search(r"(?:₹|Rs\.?|INR)\s?([\d,]+)", text)
        if match:
            try:
                return int(match.group(1).replace(",", ""))
            except:
                return None
        return None

    def _extract_times(self, text: str) -> dict:
        """Extract departure and arrival times"""
        times = re.findall(r"\d{2}:\d{2}", text)
        return {
            'departure': times[0] if len(times) > 0 else None,
            'arrival': times[1] if len(times) > 1 else None,
        }

    def export_to_excel(self, data: List[dict], filename: str) -> str:
        """Export data to Excel file"""
        try:
            df = pd.DataFrame(data)
            
            # Create output directory
            os.makedirs("outputs", exist_ok=True)
            
            filepath = f"outputs/{filename}.xlsx"
            
            with pd.ExcelWriter(filepath, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name="Flights", index=False)
            
            logger.info(f"Data exported to {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Error exporting to Excel: {str(e)}")
            raise
