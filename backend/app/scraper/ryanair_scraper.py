"""
Ryanair flight scraper using Playwright
Handles dynamic React-based website
"""

from playwright.async_api import async_playwright, Page, Browser
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import asyncio
import os
import re
from pathlib import Path
from app.utils.logger import logger
from app.utils.airline_models import get_airline_config


class RyanairScraper:
    """
    Scraper for Ryanair flights
    Handles JavaScript-rendered React website using Playwright
    """
    
    def __init__(self, task_id: Optional[str] = None, debug_dir: Optional[Path] = None, headless: Optional[bool] = None):
        self.config = get_airline_config("Ryanair")
        self.base_url = self.config["base_url"]
        self.airline_name = "Ryanair"
        self.browser = None
        self.task_id = task_id or "manual"
        self.debug_dir = Path(debug_dir or "outputs/debug")
        self.debug_records = []
        if headless is None:
            headless = os.getenv("MULTI_AIRLINE_HEADLESS", "false").lower() in ("1", "true", "yes")
        self.headless = headless
        
    async def scrape(
        self,
        routes: List[Dict],
        start_date: str,
        end_date: Optional[str] = None,
        num_passengers: int = 1
    ) -> List[Dict]:
        """
        Scrape flights for multiple routes across date range
        
        Args:
            routes: List of {"origin": "DUB", "destination": "LHR"} dicts
            start_date: Start date in format "2026-06-01"
            end_date: End date in format "2026-06-15" (optional, defaults to start_date)
            num_passengers: Number of passengers
            
        Returns:
            List of flight records with price, times, etc.
        """
        if end_date is None:
            end_date = start_date
            
        all_flights = []
        
        try:
            async with async_playwright() as p:
                launch_options = {
                    "headless": self.headless,
                    "slow_mo": 300 if not self.headless else 0,
                    "args": ["--disable-blink-features=AutomationControlled"]
                }
                chrome_path = "C:/Program Files/Google/Chrome/Application/chrome.exe"
                if os.path.exists(chrome_path):
                    launch_options["executable_path"] = chrome_path
                self.browser = await p.chromium.launch(**launch_options)
                
                # Create context with user agent to avoid detection
                context = await self.browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    ignore_https_errors=True
                )
                
                # Process each route and date combination
                for route in routes:
                    logger.info(f"Scraping Ryanair: {route['origin']} -> {route['destination']}")
                    
                    # Generate date range
                    current_date = datetime.strptime(start_date, "%Y-%m-%d")
                    end = datetime.strptime(end_date, "%Y-%m-%d")
                    
                    while current_date <= end:
                        date_str = current_date.strftime("%Y-%m-%d")
                        
                        page = await context.new_page()
                        try:
                            flights = await self._scrape_single_route(
                                page,
                                route['origin'],
                                route['destination'],
                                date_str,
                                num_passengers
                            )
                            all_flights.extend(flights)
                        except Exception as e:
                            logger.error(f"Error scraping {route['origin']}->{route['destination']} on {date_str}: {str(e)}")
                        finally:
                            await page.close()
                            
                        current_date += timedelta(days=1)
                        # Add delay between requests to avoid rate limiting
                        await asyncio.sleep(2)
                
                await context.close()
                
        except Exception as e:
            logger.error(f"Fatal error in Ryanair scraper: {str(e)}")
            raise
        finally:
            if self.browser:
                await self.browser.close()
                
        logger.info(f"Ryanair scraping complete. Found {len(all_flights)} flights")
        return all_flights
    
    async def _scrape_single_route(
        self,
        page: Page,
        origin: str,
        destination: str,
        date: str,
        num_passengers: int
    ) -> List[Dict]:
        """
        Scrape flights for a single route and date
        """
        try:
            url = (
                f"{self.base_url}/gb/en/trip/flights/select"
                f"?adults={num_passengers}&teens=0&children=0&infants=0"
                f"&dateOut={date}&originIata={origin}&destinationIata={destination}"
                f"&isReturn=false&promoCode="
            )
            logger.info(f"Navigating to: {url}")
            
            # Navigate to page
            response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
            
            # Wait for flight data to load
            await asyncio.sleep(8)

            api_flights = await self._extract_flights_from_api(page, origin, destination, date, num_passengers)
            if api_flights:
                await self._save_debug_snapshot(page, origin, destination, date, "api_flights_found", len(api_flights))
                return api_flights
            
            # Try to extract flight data from page
            flights = await self._extract_flights_from_page(page, origin, destination, date)
            if flights:
                for flight in flights:
                    flight.setdefault("booking_url", page.url)
                await self._save_debug_snapshot(page, origin, destination, date, "flights_found", len(flights))
            else:
                await self._save_debug_snapshot(page, origin, destination, date, "no_flights_found", 0)
            
            return flights
            
        except Exception as e:
            logger.error(f"Error in single route scrape: {str(e)}")
            try:
                await self._save_debug_snapshot(page, origin, destination, date, f"scrape_error: {str(e)}", 0)
            except Exception:
                pass
            return []

    async def _extract_flights_from_api(
        self,
        page: Page,
        origin: str,
        destination: str,
        date: str,
        num_passengers: int
    ) -> List[Dict]:
        """Read Ryanair's availability payload to capture the full returned price list."""
        api_url = (
            f"{self.base_url}/api/booking/v4/en-gb/availability"
            f"?ADT={num_passengers}&CHD=0&DateIn=&DateOut={date}"
            f"&Destination={destination}&Disc=0&INF=0&Origin={origin}&TEEN=0"
            f"&IncludeConnectingFlights=false&FlexDaysBeforeOut=0&FlexDaysOut=0"
            f"&RoundTrip=false&ToUs=AGREED"
        )
        logger.info(f"Reading Ryanair availability API: {api_url}")
        try:
            response = await page.context.request.get(api_url, timeout=30000)
            if not response.ok:
                logger.warning(f"Ryanair availability API returned {response.status}")
                return []

            payload = await response.json()
            trips = payload.get("trips", [])
            results = []
            seen = set()
            for trip in trips:
                for date_bucket in trip.get("dates", []):
                    flight_date = str(date_bucket.get("dateOut") or date)[:10]
                    for flight in date_bucket.get("flights", []):
                        fare = None
                        regular_fare = flight.get("regularFare") or {}
                        fares = regular_fare.get("fares") or []
                        if fares:
                            fare = fares[0].get("amount")
                        if fare is None:
                            fare = flight.get("price", {}).get("value") if isinstance(flight.get("price"), dict) else None

                        time_values = flight.get("time", ["N/A", "N/A"])
                        departure_time = str(time_values[0])[:5] if len(time_values) > 0 else "N/A"
                        arrival_time = str(time_values[1])[:5] if len(time_values) > 1 else "N/A"
                        flight_number = flight.get("flightNumber")
                        record_key = (flight_date, departure_time, arrival_time, flight_number, fare)
                        if record_key in seen:
                            continue
                        seen.add(record_key)

                        results.append({
                            "airline": self.airline_name,
                            "origin": origin,
                            "destination": destination,
                            "date": flight_date,
                            "departure_time": departure_time,
                            "arrival_time": arrival_time,
                            "duration": flight.get("duration") or "N/A",
                            "price": fare if fare is not None else "N/A",
                            "currency": regular_fare.get("currency") or payload.get("currency") or "EUR",
                            "stops": "Non-stop" if not flight.get("segments") or len(flight.get("segments", [])) <= 1 else f"{len(flight.get('segments', [])) - 1} stop",
                            "flight_number": flight_number,
                            "booking_url": page.url,
                            "scraped_at": datetime.now().isoformat(),
                        })

            logger.info(f"Ryanair availability API returned {len(results)} flights")
            return results
        except Exception as e:
            logger.warning(f"Ryanair availability API extraction failed: {e}")
            return []
    
    async def _extract_flights_from_page(
        self,
        page: Page,
        origin: str,
        destination: str,
        date: str
    ) -> List[Dict]:
        """
        Extract flight information from the rendered page
        """
        flights = []
        
        try:
            # Wait for flight containers to be visible
            await page.wait_for_selector('[data-testid="flight-card"], flight-card, [class*="flight"]', timeout=15000)
            
            # Get all flight cards
            flight_cards = await page.query_selector_all('[data-testid="flight-card"], flight-card, [class*="flight-card"]')
            logger.info(f"Found {len(flight_cards)} flight cards")
            seen = set()
            
            for idx, card in enumerate(flight_cards):
                try:
                    flight_data = await self._parse_flight_card(
                        card,
                        page,
                        origin,
                        destination,
                        date
                    )
                    if flight_data:
                        record_key = (
                            flight_data.get("date"),
                            flight_data.get("flight_number"),
                            flight_data.get("departure_time"),
                            flight_data.get("arrival_time"),
                            flight_data.get("price"),
                        )
                        if record_key in seen:
                            continue
                        seen.add(record_key)
                        flights.append(flight_data)
                except Exception as e:
                    logger.warning(f"Error parsing flight card {idx}: {str(e)}")
                    continue
            
            return flights
            
        except Exception as e:
            logger.error(f"Error extracting flights: {str(e)}")
            # Try alternative extraction method
            return await self._extract_flights_fallback(page, origin, destination, date)
    
    async def _parse_flight_card(
        self,
        card,
        page: Page,
        origin: str,
        destination: str,
        date: str
    ) -> Optional[Dict]:
        """
        Parse individual flight card
        """
        try:
            card_text = await card.inner_text()

            # Extract departure time
            departure_elem = await card.query_selector('[data-testid="departure-time"]')
            departure_time = await departure_elem.text_content() if departure_elem else "N/A"
            
            # Extract arrival time
            arrival_elem = await card.query_selector('[data-testid="arrival-time"]')
            arrival_time = await arrival_elem.text_content() if arrival_elem else "N/A"
            
            # Extract duration
            duration_elem = await card.query_selector('[data-testid="duration"]')
            duration = await duration_elem.text_content() if duration_elem else "N/A"

            times = re.findall(r"\b\d{1,2}:\d{2}\b", card_text or "")
            if departure_time == "N/A" and len(times) >= 1:
                departure_time = times[0]
            if arrival_time == "N/A" and len(times) >= 2:
                arrival_time = times[1]

            if duration == "N/A":
                duration_match = re.search(r"\b\d+h\s*\d{0,2}m?\b", card_text or "")
                if duration_match:
                    duration = duration_match.group(0)
            
            # Extract price - try multiple selectors
            price = "N/A"
            text_price_match = re.search(r"(?:€|EUR)\s*([\d,.]+)", card_text or "", re.I)
            if text_price_match:
                price = float(text_price_match.group(1).replace(",", ""))

            price_selectors = [
                '[data-testid="price"]',
                '[data-ref="flight-card-price"]',
                '[class*="fare"]',
                '.price',
                '[class*="price"]',
                'span[class*="Total"]'
            ]
            
            if price == "N/A":
                for selector in price_selectors:
                    price_elem = await card.query_selector(selector)
                    if price_elem:
                        price_text = await price_elem.text_content()
                        price_match = re.search(r"(?:€|EUR)?\s*([\d.]+)", price_text.replace(',', ''), re.I)
                        if price_match:
                            price = float(price_match.group(1))
                            break
            
            # Extract stops
            stops_elem = await card.query_selector('[data-testid="stops"]')
            stops = await stops_elem.text_content() if stops_elem else "Non-stop"
            flight_number_match = re.search(r"\bFR\s*\d+\b", card_text or "", re.I)
            if (
                not flight_number_match
                or departure_time == "N/A"
                or arrival_time == "N/A"
                or price == "N/A"
            ):
                return None
            
            flight_record = {
                "airline": self.airline_name,
                "origin": origin,
                "destination": destination,
                "date": date,
                "departure_time": departure_time.strip() if isinstance(departure_time, str) else "N/A",
                "arrival_time": arrival_time.strip() if isinstance(arrival_time, str) else "N/A",
                "duration": duration.strip() if isinstance(duration, str) else "N/A",
                "price": price,
                "currency": "EUR",
                "stops": stops.strip() if isinstance(stops, str) else "Unknown",
                "flight_number": flight_number_match.group(0).replace(" ", "") if flight_number_match else None,
                "booking_url": page.url,
                "scraped_at": datetime.now().isoformat()
            }
            
            logger.debug(f"Parsed flight: {flight_record}")
            return flight_record
            
        except Exception as e:
            logger.error(f"Error parsing flight card: {str(e)}")
            return None
    
    async def _extract_flights_fallback(
        self,
        page: Page,
        origin: str,
        destination: str,
        date: str
    ) -> List[Dict]:
        """
        Fallback method to extract flights using JavaScript injection
        """
        try:
            logger.info("Using fallback extraction method")
            
            # Inject JavaScript to extract flight data from React state
            flights_data = await page.evaluate("""
                () => {
                    const flights = [];
                    const cards = document.querySelectorAll('[data-testid="flight-card"]');
                    
                    cards.forEach(card => {
                        try {
                            const departure = card.querySelector('[data-testid="departure-time"]')?.textContent || 'N/A';
                            const arrival = card.querySelector('[data-testid="arrival-time"]')?.textContent || 'N/A';
                            const price = card.querySelector('[data-testid="price"]')?.textContent || 'N/A';
                            
                            flights.push({
                                departure: departure.trim(),
                                arrival: arrival.trim(),
                                price: price.trim()
                            });
                        } catch (e) {
                            console.log('Error parsing card:', e);
                        }
                    });
                    
                    return flights;
                }
            """)
            
            # Convert to proper format
            results = []
            for flight in flights_data:
                # Extract price value
                price_match = re.search(r'[\d.]+', str(flight['price']).replace(',', ''))
                price = float(price_match.group()) if price_match else "N/A"
                
                results.append({
                    "airline": self.airline_name,
                    "origin": origin,
                    "destination": destination,
                    "date": date,
                    "departure_time": flight['departure'],
                    "arrival_time": flight['arrival'],
                    "price": price,
                    "currency": "EUR",
                    "booking_url": page.url,
                    "scraped_at": datetime.now().isoformat()
                })
            
            return results
            
        except Exception as e:
            logger.error(f"Fallback extraction also failed: {str(e)}")
            return []

    async def _save_debug_snapshot(
        self,
        page: Page,
        origin: str,
        destination: str,
        date: str,
        status: str,
        card_count: int
    ) -> Dict:
        self.debug_dir.mkdir(parents=True, exist_ok=True)
        safe_status = re.sub(r"[^a-zA-Z0-9_-]+", "_", status)[:50]
        stem = f"{self.task_id}_Ryanair_{origin}_{destination}_{date}_{safe_status}"
        screenshot_path = self.debug_dir / f"{stem}.png"
        html_path = self.debug_dir / f"{stem}.html"

        try:
            await page.screenshot(path=str(screenshot_path), full_page=True)
        except Exception as e:
            logger.warning(f"Could not capture Ryanair screenshot: {e}")

        try:
            html_path.write_text(await page.content(), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not capture Ryanair HTML: {e}")

        record = {
            "airline": self.airline_name,
            "origin": origin,
            "destination": destination,
            "date": date,
            "price": None,
            "currency": "EUR",
            "scrape_status": status,
            "booking_url": page.url,
            "page_title": await page.title(),
            "flight_card_count": card_count,
            "debug_screenshot": str(screenshot_path),
            "debug_html": str(html_path),
            "scraped_at": datetime.now().isoformat(),
        }
        self.debug_records.append(record)
        logger.info(f"Saved Ryanair debug snapshot: {screenshot_path}")
        return record
