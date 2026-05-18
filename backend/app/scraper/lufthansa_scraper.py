"""
Lufthansa flight scraper using Playwright
Handles form-based search interface
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


class LufthansaScraper:
    """
    Scraper for Lufthansa flights
    Handles form-based search interface
    """
    
    def __init__(self, task_id: Optional[str] = None, debug_dir: Optional[Path] = None, headless: Optional[bool] = None):
        self.config = get_airline_config("Lufthansa")
        self.base_url = self.config["base_url"]
        self.airline_name = "Lufthansa"
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
        Scrape Lufthansa flights for multiple routes and dates
        
        Args:
            routes: List of {"origin": "FRA", "destination": "LHR"} dicts
            start_date: Start date in format "2026-06-01"
            end_date: End date in format "2026-06-15" (optional)
            num_passengers: Number of passengers
            
        Returns:
            List of flight records
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
                
                context = await self.browser.new_context(
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                    ignore_https_errors=True
                )
                
                # Process each route and date
                for route in routes:
                    logger.info(f"Scraping Lufthansa: {route['origin']} -> {route['destination']}")
                    
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
                            logger.warning(f"Error scraping Lufthansa {route['origin']}->{route['destination']} on {date_str}: {str(e)}")
                        finally:
                            await page.close()
                            
                        current_date += timedelta(days=1)
                        await asyncio.sleep(2)
                
                await context.close()
                
        except Exception as e:
            logger.error(f"Fatal error in Lufthansa scraper: {str(e)}")
            raise
        finally:
            if self.browser:
                await self.browser.close()
                
        logger.info(f"Lufthansa scraping complete. Found {len(all_flights)} flights")
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
        Scrape flights for a single route and date via Lufthansa search
        """
        try:
            # Navigate to Lufthansa homepage
            logger.info(f"Navigating to Lufthansa search")
            await page.goto(self.base_url, wait_until="domcontentloaded", timeout=30000)
            await asyncio.sleep(5)
            await self._accept_cookies(page)
            await self._select_one_way(page)
            await self._close_popups(page)
            
            if not await self._select_airport(
                page,
                'input[name="flightQuery.flightSegments[0].originCode"]',
                origin,
            ):
                logger.warning("Could not fill departure field")
                await self._save_debug_snapshot(page, origin, destination, date, "departure_field_not_found", 0)
                return []
            
            if not await self._select_airport(
                page,
                'input[name="flightQuery.flightSegments[0].destinationCode"]',
                destination,
            ):
                logger.warning("Could not fill arrival field")
                await self._save_debug_snapshot(page, origin, destination, date, "arrival_field_not_found", 0)
                return []
            
            if not await self._select_departure_date(page, date):
                logger.warning("Could not fill date field")
                await self._save_debug_snapshot(page, origin, destination, date, "date_field_not_found", 0)
                return []
            await self._close_popups(page)
            
            await asyncio.sleep(1)
            
            # Click search button
            search_selectors = [
                'button[data-testid="search-button"]',
                'button:has-text("Find flights")',
                'button:has-text("Find Flights")',
                'button:has-text("Search")',
                'button:has-text("SEARCH")',
                '[role="button"]:has-text("Search")',
                'button[type="submit"]'
            ]
            
            search_clicked = False
            for selector in search_selectors:
                try:
                    locator = page.locator(selector)
                    count = await locator.count()
                    for idx in range(count):
                        elem = locator.nth(idx)
                        if not await elem.is_visible(timeout=500):
                            continue
                        box = await elem.bounding_box()
                        if box and box.get("y", 9999) > 500:
                            continue
                        await elem.click()
                        search_clicked = True
                        logger.debug("Clicked search button")
                        break
                    if search_clicked:
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} not found: {e}")
                    continue
            
            if not search_clicked:
                logger.warning("Could not click search button")
                await self._save_debug_snapshot(page, origin, destination, date, "search_button_not_found", 0)
                return []
            
            # Wait for results
            await asyncio.sleep(8)
            try:
                await page.wait_for_load_state("networkidle", timeout=20000)
            except Exception:
                pass
            
            # Extract flights
            title = await page.title()
            if "just a moment" in title.lower():
                await self._save_debug_snapshot(page, origin, destination, date, "blocked_by_security_challenge", 0)
                return []

            flights = await self._extract_flights_from_results(page, origin, destination, date)
            if flights:
                for flight in flights:
                    flight.setdefault("booking_url", page.url)
                await self._save_debug_snapshot(page, origin, destination, date, "flights_found", len(flights))
            else:
                await self._save_debug_snapshot(page, origin, destination, date, "no_flights_found", 0)
            return flights
            
        except Exception as e:
            logger.error(f"Error scraping single route: {str(e)}")
            try:
                await self._save_debug_snapshot(page, origin, destination, date, f"scrape_error: {str(e)}", 0)
            except Exception:
                pass
            return []

    async def _accept_cookies(self, page: Page):
        for selector in ("#cm-acceptAll", "button:has-text('Agree')", "button:has-text('Accept')"):
            try:
                await page.locator(selector).first.click(timeout=2000)
                await page.wait_for_timeout(500)
                return
            except Exception:
                continue

    async def _close_popups(self, page: Page):
        close_selectors = [
            'button[aria-label="Close"]',
            'button:has-text("×")',
            'button:has-text("Close")',
            '.modal button:has-text("×")',
            '[class*="modal"] button',
        ]
        for selector in close_selectors:
            try:
                candidates = page.locator(selector)
                count = await candidates.count()
                for idx in range(min(count, 5)):
                    candidate = candidates.nth(idx)
                    if await candidate.is_visible(timeout=500):
                        text = (await candidate.inner_text(timeout=500)).strip()
                        aria = await candidate.get_attribute("aria-label")
                        if aria == "Close" or text in {"×", "x", "X", ""}:
                            await candidate.click(timeout=1000)
                            await page.wait_for_timeout(500)
                            logger.info("Closed Lufthansa blocking popup")
                            return
            except Exception:
                continue

    async def _select_one_way(self, page: Page) -> bool:
        try:
            trip_type = page.locator('button[role="combobox"]').first
            current = await trip_type.inner_text(timeout=5000)
            if "one" in current.lower():
                return True
            await trip_type.click(timeout=5000)
            await page.wait_for_timeout(500)
            await page.locator('[role="option"]').filter(has_text=re.compile(r"One-way", re.I)).last.click(timeout=5000)
            await page.wait_for_timeout(1000)
            logger.info("Selected Lufthansa one-way trip type")
            return True
        except Exception as e:
            logger.warning(f"Could not select Lufthansa one-way trip type: {e}")
            return False

    async def _select_airport(self, page: Page, selector: str, airport_code: str) -> bool:
        try:
            field = page.locator(selector).first
            await self._close_popups(page)
            await field.wait_for(state="visible", timeout=10000)
            await field.click()
            await page.keyboard.press("Control+A")
            await page.keyboard.press("Backspace")
            await field.fill(airport_code)
            await page.wait_for_timeout(1800)

            option = page.locator('[role="option"]').filter(
                has_text=re.compile(rf"\b{re.escape(airport_code)}\b", re.I)
            ).first
            try:
                await option.click(timeout=5000)
            except Exception:
                await page.keyboard.press("ArrowDown")
                await page.keyboard.press("Enter")

            await page.wait_for_timeout(1000)
            value = await field.input_value()
            logger.info(f"Lufthansa airport field {selector} now has value: {value}")
            return airport_code.lower() in value.lower() or len(value.strip()) > 3
        except Exception as e:
            logger.warning(f"Could not select Lufthansa airport {airport_code}: {e}")
            return False

    async def _select_departure_date(self, page: Page, date: str) -> bool:
        try:
            target = datetime.strptime(date, "%Y-%m-%d")
            day = str(target.day)

            date_openers = [
                'input[name="flightQuery.flightSegments[0].travelDatetime"]',
                'button:has-text("Departure")',
                'text=Departure date',
                'text=Departure - Return',
                '[class*="date"]',
            ]
            opened = False
            for selector in date_openers:
                try:
                    await page.locator(selector).first.click(timeout=3000)
                    opened = True
                    await page.wait_for_timeout(1000)
                    break
                except Exception:
                    continue

            if not opened:
                return False

            month_name = target.strftime("%B")
            for _ in range(14):
                body = await page.locator("body").inner_text(timeout=5000)
                if month_name in body and str(target.year) in body:
                    break
                next_button = page.locator('button, [role="button"]').filter(
                    has_text=re.compile(r"next|›|>", re.I)
                ).last
                try:
                    await next_button.click(timeout=1500)
                    await page.wait_for_timeout(500)
                except Exception:
                    break

            day_candidates = page.locator('button, [role="button"], td, div').filter(
                has_text=re.compile(rf"^{day}$")
            )
            count = await day_candidates.count()
            for idx in range(count):
                candidate = day_candidates.nth(idx)
                try:
                    if await candidate.is_visible():
                        await candidate.click(timeout=1500)
                        await page.wait_for_timeout(800)
                        logger.info(f"Selected Lufthansa departure date {date}")
                        return True
                except Exception:
                    continue
            return False
        except Exception as e:
            logger.warning(f"Could not select Lufthansa date {date}: {e}")
            return False
    
    async def _extract_flights_from_results(
        self,
        page: Page,
        origin: str,
        destination: str,
        date: str
    ) -> List[Dict]:
        """
        Extract flight results from Lufthansa search results page
        """
        flights = []
        
        try:
            # Try to find flight result containers
            result_selectors = [
                '[data-testid="flight-result"]',
                '.flight-result',
                '[class*="flight"][class*="result"]',
                '.fare-card',
                '[data-testid="fare"]'
            ]
            
            flight_cards = []
            for selector in result_selectors:
                try:
                    cards = await page.query_selector_all(selector)
                    if cards and len(cards) > 0:
                        flight_cards = cards
                        logger.info(f"Found {len(cards)} flight cards with selector: {selector}")
                        break
                except Exception as e:
                    logger.debug(f"Selector {selector} failed: {e}")
                    continue
            
            if not flight_cards:
                logger.warning("No flight cards found")
                return await self._extract_flights_fallback(page, origin, destination, date)
            
            for idx, card in enumerate(flight_cards[:20]):  # Limit to first 20
                try:
                    flight_data = await self._parse_lufthansa_flight(
                        card,
                        page,
                        origin,
                        destination,
                        date
                    )
                    if flight_data:
                        flights.append(flight_data)
                except Exception as e:
                    logger.debug(f"Error parsing flight card {idx}: {str(e)}")
                    continue
            
            return flights
            
        except Exception as e:
            logger.error(f"Error extracting flights: {str(e)}")
            return await self._extract_flights_fallback(page, origin, destination, date)
    
    async def _parse_lufthansa_flight(
        self,
        card,
        page: Page,
        origin: str,
        destination: str,
        date: str
    ) -> Optional[Dict]:
        """
        Parse individual Lufthansa flight card
        """
        try:
            # Extract departure time
            departure_time = "N/A"
            arrival_time = "N/A"
            price = "N/A"
            duration = "N/A"
            
            # Try to extract from card text
            card_text = await card.text_content()
            
            # Look for time patterns (HH:MM)
            time_pattern = r'(\d{1,2}):(\d{2})'
            times = re.findall(time_pattern, card_text)
            
            if len(times) >= 2:
                departure_time = f"{times[0][0]}:{times[0][1]}"
                arrival_time = f"{times[1][0]}:{times[1][1]}"
            
            # Extract price - look for € symbol
            price_pattern = r'€\s*([\d.]+)'
            price_match = re.search(price_pattern, card_text)
            if price_match:
                price = float(price_match.group(1))
            
            # Extract duration if available
            duration_pattern = r'(\d+)h\s*(\d+)?m?'
            duration_match = re.search(duration_pattern, card_text)
            if duration_match:
                hours = duration_match.group(1)
                minutes = duration_match.group(2) or "0"
                duration = f"{hours}h {minutes}m"
            
            flight_record = {
                "airline": self.airline_name,
                "origin": origin,
                "destination": destination,
                "date": date,
                "departure_time": departure_time,
                "arrival_time": arrival_time,
                "duration": duration,
                "price": price,
                "currency": "EUR",
                "stops": "Unknown",
                "booking_url": page.url,
                "scraped_at": datetime.now().isoformat()
            }
            
            logger.debug(f"Parsed Lufthansa flight: {flight_record}")
            return flight_record if price != "N/A" else None
            
        except Exception as e:
            logger.error(f"Error parsing flight: {str(e)}")
            return None
    
    async def _extract_flights_fallback(
        self,
        page: Page,
        origin: str,
        destination: str,
        date: str
    ) -> List[Dict]:
        """
        Fallback extraction using JavaScript
        """
        try:
            logger.info("Using fallback extraction for Lufthansa")
            
            flights_data = await page.evaluate("""
                () => {
                    const flights = [];
                    const textContent = document.body.innerText;
                    
                    // Try to extract structured data
                    const priceMatches = textContent.match(/€\\s*([\\d.]+)/g);
                    const timeMatches = textContent.match(/(\\d{1,2}):(\\d{2})/g);
                    
                    if (priceMatches && timeMatches) {
                        for (let i = 0; i < Math.min(priceMatches.length, 5); i++) {
                            flights.push({
                                price: priceMatches[i],
                                departure: timeMatches[i * 2] || 'N/A',
                                arrival: timeMatches[i * 2 + 1] || 'N/A'
                            });
                        }
                    }
                    
                    return flights;
                }
            """)
            
            results = []
            for flight in flights_data:
                try:
                    price_match = re.search(r'€\s*([\d.]+)', flight.get('price', ''))
                    price = float(price_match.group(1)) if price_match else "N/A"
                    
                    results.append({
                        "airline": self.airline_name,
                        "origin": origin,
                        "destination": destination,
                        "date": date,
                        "departure_time": flight.get('departure', 'N/A'),
                        "arrival_time": flight.get('arrival', 'N/A'),
                        "price": price,
                        "currency": "EUR",
                        "booking_url": page.url,
                        "scraped_at": datetime.now().isoformat()
                    })
                except Exception as e:
                    logger.debug(f"Error processing fallback flight: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"Fallback extraction failed: {str(e)}")
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
        stem = f"{self.task_id}_Lufthansa_{origin}_{destination}_{date}_{safe_status}"
        screenshot_path = self.debug_dir / f"{stem}.png"
        html_path = self.debug_dir / f"{stem}.html"

        try:
            await page.screenshot(path=str(screenshot_path), full_page=True)
        except Exception as e:
            logger.warning(f"Could not capture Lufthansa screenshot: {e}")

        try:
            html_path.write_text(await page.content(), encoding="utf-8")
        except Exception as e:
            logger.warning(f"Could not capture Lufthansa HTML: {e}")

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
        logger.info(f"Saved Lufthansa debug snapshot: {screenshot_path}")
        return record
