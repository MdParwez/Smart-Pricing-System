"""
Airline-specific configurations and models
"""

class AirlineConfig:
    """Configuration for each airline's website"""
    pass


AIRLINE_CONFIGS = {
    "Ryanair": {
        "base_url": "https://www.ryanair.com",
        "website_type": "react",  # JavaScript-heavy SPA
        "airport_codes": {
            "DUB": "Dublin",
            "STN": "London Stansted",
            "ORK": "Cork"
        },
        "routes": [
            {
                "origin": "DUB",
                "destination": "STN",
                "origin_name": "Dublin",
                "destination_name": "London Stansted"
            },
            {
                "origin": "ORK",
                "destination": "STN",
                "origin_name": "Cork",
                "destination_name": "London Stansted"
            },
        ],
        "competitors": ["Wizz Air", "Easyjet"],
        "selectors": {
            "flight_card": '[data-testid="flight-card"]',
            "price": '[data-testid="price"]',
            "departure_time": '[data-testid="departure-time"]',
            "arrival_time": '[data-testid="arrival-time"]',
            "duration": '[data-testid="duration"]'
        }
    },
    "Lufthansa": {
        "base_url": "https://www.lufthansa.com",
        "website_type": "api_based",
        "airport_codes": {
            "FRA": "Frankfurt",
            "MUC": "Munich",
            "LHR": "London",
            "SAN": "San Diego"
        },
        "routes": [
            {
                "origin": "FRA",
                "destination": "LHR",
                "origin_name": "Frankfurt",
                "destination_name": "London"
            },
            {
                "origin": "MUC",
                "destination": "SAN",
                "origin_name": "Munich",
                "destination_name": "San Diego"
            },
        ],
        "competitors": ["BA", "Turkish", "Air France"],
        "selectors": {
            "departure_input": '[data-testid="departure"]',
            "arrival_input": '[data-testid="arrival"]',
            "date_input": '[data-testid="date"]',
            "search_button": '[data-testid="search-button"]',
            "flight_card": '.flight-result',
            "price": '.price'
        }
    },
    "Wizz Air": {
        "base_url": "https://wizzair.com",
        "website_type": "react",
        "airport_codes": {
            "DUB": "Dublin",
            "LHR": "London",
            "ORK": "Cork"
        },
        "routes": [
            {
                "origin": "DUB",
                "destination": "LHR",
                "origin_name": "Dublin",
                "destination_name": "London"
            },
        ],
        "competitors": [],
        "selectors": {
            "flight_card": '[data-flight]',
            "price": '[data-price]',
        }
    },
    "Easyjet": {
        "base_url": "https://www.easyjet.com",
        "website_type": "react",
        "airport_codes": {
            "DUB": "Dublin",
            "LHR": "London",
            "ORK": "Cork"
        },
        "routes": [
            {
                "origin": "DUB",
                "destination": "LHR",
                "origin_name": "Dublin",
                "destination_name": "London"
            },
        ],
        "competitors": [],
        "selectors": {
            "flight_card": '[data-testid="flight-card"]',
            "price": '[data-testid="flight-price"]',
        }
    }
}


def get_airline_config(airline_name: str) -> dict:
    """Get configuration for an airline"""
    return AIRLINE_CONFIGS.get(airline_name, {})


def get_competitors(airline_name: str) -> list:
    """Get competitors for an airline"""
    config = AIRLINE_CONFIGS.get(airline_name, {})
    return config.get("competitors", [])


def get_airline_routes(airline_name: str) -> list:
    """Get routes configured for an airline"""
    config = AIRLINE_CONFIGS.get(airline_name, {})
    return config.get("routes", [])
