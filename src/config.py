# config.py

# Keywords to identify National Parks in API
NATIONAL_PARK_KEYWORDS = [
    "National Park",
    "National Park & Preserve",
    "National Park and Preserve",
    "National Parks",             # plural (Sequoia & Kings Canyon)
    "National and State Parks"    # Redwood
]

# Parks to explicitly exclude (for strict 63 parks)
EXCLUDE_PARKS = ["National Parks of New York Harbor", "Wolf Trap National Park for the Performing Arts"] # These are more like monuments/performing arts venues, not traditional parks

# File paths
NATIONAL_PARKS_FILE = "data/national_parks.json"
WEATHER_FILE = "data/national_parks_weather.json"

# API settings
NPS_API_URL = "https://developer.nps.gov/api/v1/parks"
WEATHER_API_URL = "http://api.weatherapi.com/v1/forecast.json"
PAGE_SIZE = 100