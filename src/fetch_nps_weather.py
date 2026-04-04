# main.py
import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from config import (
    NPS_API_URL,              # Base URL for National Parks API
    WEATHER_API_URL,          # Base URL for Weather API
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
# 1️. Fetch National Parks from NPS API
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
# 2️. Clean and filter parks
# -----------------------------
def clean_parks_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filters to only National Parks, removes excluded parks,
    and extracts numeric latitude/longitude.
    """
    # Filter for National Parks using keywords in designation or fullName
    df = df[
        (
            df["designation"].str.contains("|".join(NATIONAL_PARK_KEYWORDS), na=False) # Match any national park keyword
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
    #df = df[["fullName", "designation", "latitude", "longitude"]]

    # Reset index for clean DataFrame
    return df.reset_index(drop=True)

# -----------------------------
# 3️. Fetch weather for each park
# -----------------------------
def fetch_weather(lat: float, lon: float) -> dict:
    """
    Fetch full weather payload from WeatherAPI.com.
    Returns the entire JSON response.
    """
    if pd.isna(lat) or pd.isna(lon): # Skip if lat/lon are missing
        return {}

    url = WEATHER_API_URL # Endpoint for forecasted weather
    params = {"key": WEATHERAPI_KEY, "q": f"{lat},{lon}", "days": 3} # Query by lat/lon with 3-day forecast

    try:
        response = requests.get(url, params=params) # Make API request
        if response.status_code != 200:
            print(f"HTTP Error {response.status_code}: {response.text}")
            return {} # Return empty dict on error instead of raising exception

        data = response.json() #

        if "error" in data:
            print(f"API Error: {data['error']}") # Log API error message
            return {} # Return empty dict on API error instead of raising exception

        return data  # Return full JSON response for flexibility in analysis

    except Exception as e:
        print(f"Error fetching weather for {lat},{lon}: {e}")
        return {}

# -----------------------------
# 4️. Add weather to DataFrame
# -----------------------------
def add_weather_to_df(df: pd.DataFrame) -> pd.DataFrame:
    """
    Fetch full weather data and merge into DataFrame.
    """
    weather_rows = [] # List to hold weather data for each park

    for _, row in df.iterrows():
        lat = row["latitude"]
        lon = row["longitude"]

        print(f"Fetching weather for {row['fullName']} → {lat},{lon}")
        weather_json = fetch_weather(lat, lon) # Get full weather JSON for this park

        # Flatten JSON into single row
        if weather_json:
            flat = pd.json_normalize(weather_json) # Flatten nested JSON into a single row DataFrame
        else:
            flat = pd.DataFrame([{}]) # Empty row if no weather data

        weather_rows.append(flat) # Add this park's weather data to the list
        time.sleep(1) # Sleep to respect API rate limits (adjust as needed)

    # Combine all weather rows
    weather_df = pd.concat(weather_rows, ignore_index=True) # Combine list of DataFrames into one DataFrame

    # Merge with original df
    df = pd.concat([df.reset_index(drop=True), weather_df], axis=1) # Combine original park data with weather data side by side

    return df

# -----------------------------
# 5️. Main pipeline
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