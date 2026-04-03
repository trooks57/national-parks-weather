# main.py
import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from config import (
    NPS_API_URL,              # Base URL for National Parks API
    PAGE_SIZE,                # Number of results per API page
    NATIONAL_PARK_KEYWORDS,   # Keywords to identify National Parks
    EXCLUDE_PARKS,            # Parks to exclude
    WEATHER_FILE              # Path to save final JSON
)

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()  # Reads .env file into environment
NPS_API_KEY = os.getenv("NPS_API_KEY")
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY")

# -----------------------------
# 1️⃣ Fetch National Parks from NPS API
# -----------------------------
def fetch_national_parks_df(api_key: str, page_size: int = PAGE_SIZE) -> pd.DataFrame:
    """
    Fetch all parks from NPS API, handle pagination, and return as a DataFrame.
    """
    all_parks = []
    pagination_start = 0

    while True:
        # Request a page of parks
        params = {"api_key": api_key, "start": pagination_start, "limit": page_size}
        response = requests.get(NPS_API_URL, params=params)
        data = response.json()

        parks_batch = data.get("data", [])
        all_parks.extend(parks_batch)  # Add this page to master list

        total = int(data.get("total", 0))
        pagination_start += page_size
        if pagination_start >= total:
            break  # Stop when all pages fetched

    # Convert list of dicts → pandas DataFrame
    df = pd.DataFrame(all_parks)
    return df

# -----------------------------
# 2️⃣ Clean and filter parks
# -----------------------------
def clean_parks_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters to only National Parks, removes excluded parks,
    and extracts numeric latitude/longitude.
    """
    # Filter for National Parks using keywords in designation or fullName
    df = df[
        (
            df["designation"].str.contains("|".join(NATIONAL_PARK_KEYWORDS), na=False)
            | df["fullName"].str.contains("National Park", na=False)
        )
        & ~df["fullName"].isin(EXCLUDE_PARKS)  # Exclude unwanted parks
    ]

    # Clean latLong string: remove 'lat:', 'long:', spaces
    df["lat_long"] = (
        df["latLong"]
        .fillna("")  # Replace missing latLong with empty string
        .str.replace("lat:", "", regex=False)
        .str.replace("long:", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    # Split into latitude and longitude columns
    df[["latitude", "longitude"]] = df["lat_long"].str.split(",", expand=True)

    # Convert strings → numbers, invalid become NaN
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Keep only necessary columns
    df = df[["fullName", "designation", "latitude", "longitude"]]

    # Reset index for clean DataFrame
    return df.reset_index(drop=True)

# -----------------------------
# 3️⃣ Fetch weather for each park
# -----------------------------
def fetch_weather(lat: float, lon: float) -> dict:
    """
    Fetch current weather from WeatherAPI.com for given coordinates.
    Returns temperature (F) and condition text.
    """
    if pd.isna(lat) or pd.isna(lon):  # Skip if coordinates missing
        return {"temperature_f": None, "condition": None}

    url = "https://api.weatherapi.com/v1/current.json"
    params = {"key": WEATHERAPI_KEY, "q": f"{lat},{lon}"}

    try:
        response = requests.get(url, params=params)
        if response.status_code != 200:  # Handle HTTP errors
            print(f"HTTP Error {response.status_code}: {response.text}")
            return {"temperature_f": None, "condition": None}

        data = response.json()
        if "error" in data:  # Handle API errors
            print(f"API Error: {data['error']}")
            return {"temperature_f": None, "condition": None}

        current = data.get("current", {})
        return {
            "temperature_f": current.get("temp_f"),
            "condition": current.get("condition", {}).get("text")
        }

    except Exception as e:  # Catch unexpected exceptions
        print(f"Error fetching weather for {lat},{lon}: {e}")
        return {"temperature_f": None, "condition": None}

# -----------------------------
# 4️⃣ Add weather to DataFrame
# -----------------------------
def add_weather_to_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Loops through parks and fetches weather for each.
    Adds temperature_f and condition columns.
    """
    temperatures = []
    conditions = []

    for _, row in df.iterrows():  # Loop row by row
        lat = row["latitude"]
        lon = row["longitude"]

        print(f"Fetching weather for {row['fullName']} → {lat},{lon}")
        weather = fetch_weather(lat, lon)
        temperatures.append(weather["temperature_f"])
        conditions.append(weather["condition"])
        time.sleep(1)  # Prevent API rate limiting

    # Add new columns to DataFrame
    df["temperature_f"] = temperatures
    df["condition"] = conditions
    return df

# -----------------------------
# 5️⃣ Main pipeline
# -----------------------------
def main():
    # Check for keys
    if not NPS_API_KEY or not WEATHERAPI_KEY:
        print("Missing API keys")
        return

    # Fetch, clean, and enrich parks
    df = fetch_national_parks_df(NPS_API_KEY)
    df = clean_parks_df(df)
    df = add_weather_to_df(df)

    # Save to JSON
    df.to_json(WEATHER_FILE, orient="records", indent=2)

    print("Finished! Sample data:")
    print(df.head())

# Entry point
if __name__ == "__main__":
    main()