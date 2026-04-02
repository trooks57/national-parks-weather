import os
import time
import requests
import pandas as pd
from dotenv import load_dotenv
from config import (
    NPS_API_URL,
    PAGE_SIZE,
    NATIONAL_PARK_KEYWORDS,
    NATIONAL_PARKS_FILE,
    EXCLUDE_PARKS,
    WEATHER_FILE
)

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
NPS_API_KEY = os.getenv("NPS_API_KEY")
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY")


# -----------------------------
# Fetch National Parks → DataFrame
# -----------------------------
def fetch_national_parks_df(api_key: str, page_size: int = PAGE_SIZE) -> pd.DataFrame:
    all_parks = []
    pagination_start = 0

    while True:
        params = {"api_key": api_key, "start": pagination_start, "limit": page_size}
        response = requests.get(NPS_API_URL, params=params)
        data = response.json()

        parks_batch = data.get("data", [])
        all_parks.extend(parks_batch)

        total = int(data.get("total", 0))
        pagination_start += page_size
        if pagination_start >= total:
            break

    # Convert to DataFrame
    df = pd.DataFrame(all_parks)

    return df


# -----------------------------
# Clean & Filter National Parks
# -----------------------------
def clean_parks_df(df: pd.DataFrame) -> pd.DataFrame:
    # Filter National Parks
    df = df[
        (
            df["designation"].str.contains("|".join(NATIONAL_PARK_KEYWORDS), na=False)
            | df["fullName"].str.contains("National Park", na=False)
        )
        & ~df["fullName"].isin(EXCLUDE_PARKS)
    ]

    # Clean latLong string
    df["lat_long"] = (
        df["latLong"]
        .fillna("")
        .str.replace("lat:", "", regex=False)
        .str.replace("long:", "", regex=False)
        .str.replace(" ", "", regex=False)
    )

    # Split into latitude & longitude
    df[["latitude", "longitude"]] = df["lat_long"].str.split(",", expand=True)

    # Convert to numeric
    df["latitude"] = pd.to_numeric(df["latitude"], errors="coerce")
    df["longitude"] = pd.to_numeric(df["longitude"], errors="coerce")

    # Keep only needed columns
    df = df[["fullName", "designation", "latitude", "longitude"]]

    return df.reset_index(drop=True)


# -----------------------------
# Fetch Weather
# -----------------------------
def fetch_weather(lat: float, lon: float) -> dict:
    if pd.isna(lat) or pd.isna(lon):
        return {"temperature_f": None, "condition": None}

    url = "https://api.weatherapi.com/v1/current.json"
    params = {
        "key": WEATHERAPI_KEY,
        "q": f"{lat},{lon}"
    }

    try:
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"HTTP Error {response.status_code}: {response.text}")
            return {"temperature_f": None, "condition": None}

        data = response.json()

        if "error" in data:
            print(f"API Error: {data['error']}")
            return {"temperature_f": None, "condition": None}

        current = data.get("current", {})
        return {
            "temperature_f": current.get("temp_f"),
            "condition": current.get("condition", {}).get("text")
        }

    except Exception as e:
        print(f"Error fetching weather for {lat},{lon}: {e}")
        return {"temperature_f": None, "condition": None}


# -----------------------------
# Enrich DataFrame with Weather
# -----------------------------
def add_weather_to_df(df: pd.DataFrame) -> pd.DataFrame:
    temperatures = []
    conditions = []

    for _, row in df.iterrows():
        lat = row["latitude"]
        lon = row["longitude"]

        print(f"Fetching weather for {row['fullName']} → {lat},{lon}")

        weather = fetch_weather(lat, lon)

        temperatures.append(weather["temperature_f"])
        conditions.append(weather["condition"])

        time.sleep(1)  # prevent rate limiting

    df["temperature_f"] = temperatures
    df["condition"] = conditions

    return df


# -----------------------------
# Main
# -----------------------------
def main():
    if not NPS_API_KEY or not WEATHERAPI_KEY:
        print("Missing API keys")
        return

    # Step 1: Fetch
    df = fetch_national_parks_df(NPS_API_KEY)

    # Step 2: Clean
    df = clean_parks_df(df)

    # Step 3: Add Weather
    df = add_weather_to_df(df)

    # Step 4: Save
    df.to_json(WEATHER_FILE, orient="records", indent=2)

    print(df.head())


if __name__ == "__main__":
    main()