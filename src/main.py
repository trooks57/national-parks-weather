import os
import json
import requests
from dotenv import load_dotenv
from config import (
    NPS_API_URL,
    PAGE_SIZE,
    NATIONAL_PARK_KEYWORDS,
    EXCLUDE_PARKS,
    NATIONAL_PARKS_FILE
)

# -----------------------------
# Load environment variables
# -----------------------------
load_dotenv()
API_KEY = os.getenv("NPS_API_KEY")



# -----------------------------
# Functions
# -----------------------------
def fetch_national_parks(api_key: str, page_size: int = PAGE_SIZE) -> list:
    """
    Fetch National Parks directly from the NPS API,
    handling pagination and edge cases.
    Returns a simplified list of dicts with fullName and designation.
    """
    national_parks = []
    pagination_start = 0

    while True:
        params = {"api_key": api_key, "start": pagination_start, "limit": page_size}
        response = requests.get(NPS_API_URL, params=params)
        api_response = response.json()
        parks_batch = api_response.get("data", [])

        # Filter National Parks
        for park in parks_batch:
            full_name = park.get("fullName")
            designation = park.get("designation")
            lat_long_string = park.get("latLong", "")
            latitude, longitude = None, None
            
            if lat_long_string:
                try:
                    lat_long_parts = lat_long_string.split(",")
                    latitude = float(lat_long_parts[0].split(":")[1].strip())
                    longitude = float(lat_long_parts[1].split(":")[1].strip())
                except (IndexError, ValueError):
                    print(f"Warning: Could not parse latLong for {full_name}: '{lat_long_string}'")
            if (
                (designation and any(k in designation for k in NATIONAL_PARK_KEYWORDS))
                or ("National Park" in full_name)
            ) and full_name not in EXCLUDE_PARKS:
                national_parks.append({"fullName": full_name, "designation": designation, "latitude": latitude, "longitude": longitude})

        # Pagination
        total_parks = int(api_response.get("total", 0))
        pagination_start += page_size
        if pagination_start >= total_parks:
            break

    return national_parks


def save_to_json(data: list, file_path: str):
    """Save a list of dictionaries to a JSON file."""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    with open(file_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Saved {len(data)} items to {file_path}")


# -----------------------------
# Main
# -----------------------------
def main():
    if not API_KEY:
        print("ERROR: NPS_API_KEY not found in environment variables.")
        return

    national_parks = fetch_national_parks(API_KEY)
    save_to_json(national_parks, NATIONAL_PARKS_FILE)


if __name__ == "__main__":
    main()