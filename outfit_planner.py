"""
Vacation Outfit Planner
------------------------
Give it a city and a date (or a date range for a whole trip), and it
suggests what to wear based on the weather forecast (temperature, rain,
wind). If you're arriving that day, pass --arrival to get a travel-friendly
suggestion instead of a full outfit for the arrival day. Multi-day trips
also get a packing summary at the end.

Usage:
    python outfit_planner.py "Lisbon" 2026-09-10
    python outfit_planner.py "Lisbon" 2026-09-10 --arrival midday
    python outfit_planner.py "Tokyo" 2026-08-24 through 2026-08-30
    python outfit_planner.py "Tokyo" 2026-08-24 through 2026-08-30 --arrival midday
"""

import argparse
import math
import sys
from datetime import date, datetime
from typing import Optional

import requests

GEOCODE_URL = "https://geocoding-api.open-meteo.com/v1/search"
FORECAST_URL = "https://api.open-meteo.com/v1/forecast"

# Open-Meteo's free forecast only looks ~16 days ahead reliably.
MAX_FORECAST_DAYS = 16


def geocode_city(city: str):
    """Turn a city name into (latitude, longitude, resolved display name)."""
    response = requests.get(GEOCODE_URL, params={"name": city, "count": 1}, timeout=10)
    response.raise_for_status()
    results = response.json().get("results")

    if not results:
        sys.exit(f"Couldn't find a location called '{city}'. Try a different spelling?")

    top = results[0]
    display_name = f"{top['name']}, {top.get('country', '')}".strip(", ")
    return top["latitude"], top["longitude"], display_name


def get_forecast_range(lat: float, lon: float, start_date: str, end_date: str):
    """Fetch the daily forecast summary for every date from start_date to end_date (inclusive)."""
    params = {
        "latitude": lat,
        "longitude": lon,
        "daily": [
            "temperature_2m_max",
            "temperature_2m_min",
            "precipitation_probability_max",
            "windspeed_10m_max",
        ],
        "timezone": "auto",
        "start_date": start_date,
        "end_date": end_date,
    }
    response = requests.get(FORECAST_URL, params=params, timeout=10)
    response.raise_for_status()
    daily = response.json().get("daily")

    if not daily or not daily.get("time"):
        sys.exit(
            f"No forecast available for {start_date} to {end_date}. "
            f"Open-Meteo's free forecast only covers about {MAX_FORECAST_DAYS} days ahead."
        )

    return [
        {
            "date": daily["time"][i],
            "temp_max": daily["temperature_2m_max"][i],
            "temp_min": daily["temperature_2m_min"][i],
            "rain_chance": daily["precipitation_probability_max"][i],
            "wind_max": daily["windspeed_10m_max"][i],
        }
        for i in range(len(daily["time"]))
    ]


def classify_conditions(forecast: dict):
    """Turn raw numbers into simple, human buckets."""
    temp_max = forecast["temp_max"]

    if temp_max < 5:
        temp_band = "cold"
    elif temp_max < 15:
        temp_band = "cool"
    elif temp_max < 25:
        temp_band = "mild"
    elif temp_max < 32:
        temp_band = "warm"
    else:
        temp_band = "hot"

    rain_chance = forecast["rain_chance"]
    if rain_chance >= 60:
        rain = "likely"
    elif rain_chance >= 30:
        rain = "possible"
    else:
        rain = "unlikely"

    wind_max = forecast["wind_max"]
    if wind_max >= 40:
        wind = "windy"
    elif wind_max >= 20:
        wind = "breezy"
    else:
        wind = "calm"

    return {"temp_band": temp_band, "rain": rain, "wind": wind}


def suggest_outfit(conditions: dict, arrival: Optional[str] = None):
    """Build a plain-language outfit suggestion from the condition buckets."""

    # Arrival day, arriving midday or evening: you're mostly in transit,
    # so suggest easy layers instead of planning a full outfit change.
    if arrival in ("midday", "evening"):
        pieces = [
            "You're arriving partway through the day, so keep it simple: "
            "wear breathable layers you can add or remove on the move "
            "(t-shirt + light layer you can tie around your waist or stuff in a bag), "
            "and comfortable shoes for travel."
        ]
        if conditions["rain"] != "unlikely":
            pieces.append("Pack a compact umbrella or rain shell in your bag rather than wearing it.")
        if conditions["temp_band"] in ("cold", "cool"):
            pieces.append("Bring an extra layer for when the temperature drops later.")
        return " ".join(pieces)

    # Otherwise: full outfit suggestion for the day.
    base = {
        "cold": "Wear a warm coat, sweater, and long pants — layer up.",
        "cool": "A jacket or light coat over a sweater or long sleeves works well.",
        "mild": "Light layers — a t-shirt or long sleeves with a light jacket you can remove.",
        "warm": "Light, breathable clothing — shorts or a sundress, short sleeves.",
        "hot": "Stay cool with light, loose clothing, and sun protection.",
    }[conditions["temp_band"]]

    pieces = [base]

    if conditions["rain"] == "likely":
        pieces.append("Bring a rain jacket or umbrella — rain is likely.")
    elif conditions["rain"] == "possible":
        pieces.append("Pack a compact umbrella just in case.")

    if conditions["wind"] == "windy":
        pieces.append("It'll be windy, so skip loose hats or anything easily blown around.")
    elif conditions["wind"] == "breezy":
        pieces.append("Expect a breeze — a light layer helps.")

    return " ".join(pieces)


def build_packing_list(daily_conditions: list):
    """Tally how many of each item to pack for the whole trip."""
    trip_days = len(daily_conditions)

    packing_list = {
        "shirts": trip_days,
        "underwear": trip_days,
        "socks": trip_days,
        # Pants get re-worn, so pack roughly one pair per 3 days rather than one per day.
        "pants": max(1, math.ceil(trip_days / 3)),
    }

    if any(c["rain"] != "unlikely" for c in daily_conditions):
        packing_list["rain jacket/umbrella"] = 1
    if any(c["temp_band"] in ("cold", "cool") for c in daily_conditions):
        packing_list["extra warm layer"] = 1

    return packing_list


def format_packing_line(packing_list: dict) -> str:
    """'7 shirts, 7 underwear, 7 socks, 3 pants, and bring the rain jacket/umbrella'"""
    base_items = ["shirts", "underwear", "socks", "pants"]
    base = ", ".join(f"{packing_list[item]} {item}" for item in base_items)

    extras = [item for item in packing_list if item not in base_items]
    if not extras:
        return base
    return f"{base}, and bring the " + " and ".join(extras)


def format_date_range(start_str: str, end_str: str) -> str:
    """'2026-08-24', '2026-08-30' -> 'Aug 24–30' (or 'Aug 30 – Sep 02' across months)."""
    start = datetime.strptime(start_str, "%Y-%m-%d").date()
    end = datetime.strptime(end_str, "%Y-%m-%d").date()
    if (start.year, start.month) == (end.year, end.month):
        return f"{start.strftime('%b')} {start.day}–{end.day}"
    return f"{start.strftime('%b %d')} – {end.strftime('%b %d')}"


def _format_day_span(day_nums: list) -> str:
    """[5, 6, 7] -> 'days 5–7'; [3] -> 'day 3'; [2, 5] -> 'days 2 and 5'."""
    if len(day_nums) == 1:
        return f"day {day_nums[0]}"
    if day_nums == list(range(day_nums[0], day_nums[-1] + 1)):
        return f"days {day_nums[0]}–{day_nums[-1]}"
    return "days " + ", ".join(str(d) for d in day_nums[:-1]) + f" and {day_nums[-1]}"


def summarize_weather(daily_conditions: list, daily_forecasts: list) -> str:
    """One clause on temperature range and rain risk across the trip, e.g. 'mild and warm, mostly dry early on with rain picking up around days 5–7 (up to 60% chance)'."""
    band_order = ["cold", "cool", "mild", "warm", "hot"]
    bands_present = sorted({c["temp_band"] for c in daily_conditions}, key=band_order.index)
    if len(bands_present) == 1:
        temp_part = bands_present[0]
    elif len(bands_present) == 2:
        temp_part = f"{bands_present[0]} and {bands_present[1]}"
    else:
        temp_part = f"ranging from {bands_present[0]} to {bands_present[-1]}"

    rainy_indices = [i for i, c in enumerate(daily_conditions) if c["rain"] != "unlikely"]
    if not rainy_indices:
        rain_part = "dry throughout"
    elif len(rainy_indices) == len(daily_conditions):
        rain_part = "rain likely throughout"
    else:
        day_span = _format_day_span([i + 1 for i in rainy_indices])
        max_chance = max(daily_forecasts[i]["rain_chance"] for i in rainy_indices)
        rain_part = f"mostly dry early on with rain picking up around {day_span} (up to {max_chance:.0f}% chance)"

    return f"{temp_part}, {rain_part}"


def summarize_suggestions(arrival, daily_conditions: list) -> str:
    """One or two clauses describing what to wear, in aggregate rather than day by day."""
    band_order = ["cold", "cool", "mild", "warm", "hot"]
    band_desc = {
        "cold": "warm, heavily layered outfits",
        "cool": "a jacket over layers",
        "mild": "light layers you can adjust through the day",
        "warm": "light, breathable clothing",
        "hot": "light, loose clothing with sun protection",
    }

    rest = daily_conditions[1:] if arrival else daily_conditions
    subject = "the rest are" if arrival else "outfits are"

    clauses = []
    if arrival:
        clauses.append("Arrival day gets travel-friendly layers")

    if rest:
        bands_present = sorted({c["temp_band"] for c in rest}, key=band_order.index)
        if len(bands_present) == 1:
            desc = band_desc[bands_present[0]]
        else:
            desc = f"{band_desc[bands_present[0]]}, trending toward {band_desc[bands_present[-1]]} on warmer days"
        if any(c["rain"] != "unlikely" for c in rest):
            desc += ", with an umbrella handy for a few days"
        clauses.append(f"{subject} {desc}")

    summary = ", ".join(clauses) + "."
    return summary[0].upper() + summary[1:]


def build_trip_narrative(place, start_date, end_date, arrival, daily_forecasts, daily_conditions, packing_list) -> str:
    """Assemble the full one-paragraph trip summary."""
    date_range = format_date_range(start_date, end_date)
    arrival_note = f", arriving {arrival}" if arrival else ""
    weather = summarize_weather(daily_conditions, daily_forecasts)
    suggestions = summarize_suggestions(arrival, daily_conditions)
    packing = format_packing_line(packing_list)

    return f"Your {place} trip ({date_range}{arrival_note}): {weather}. {suggestions} Pack: {packing}."


def parse_args():
    parser = argparse.ArgumentParser(description="Suggest vacation outfits based on the weather forecast.")
    parser.add_argument("city", help='City name, e.g. "Lisbon"')
    parser.add_argument("date", help="Date in YYYY-MM-DD format (the arrival day, if a range is given)")
    parser.add_argument(
        "end_date",
        nargs="?",
        default=None,
        help="Optional: last day of the trip, YYYY-MM-DD. Omit for a single-day plan.",
    )
    parser.add_argument(
        "--arrival",
        choices=["morning", "midday", "evening"],
        default=None,
        help="When you land on the first day — adjusts that day's suggestion for travel.",
    )

    # Allow the human-friendly "start_date through end_date" phrasing by
    # dropping the literal word "through" before argparse ever sees it.
    raw_args = [arg for arg in sys.argv[1:] if arg.lower() != "through"]
    return parser.parse_args(raw_args)


def validate_date(date_str: str) -> date:
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        sys.exit(f"'{date_str}' isn't a valid date. Use YYYY-MM-DD, e.g. 2026-09-10.")

    days_out = (parsed - date.today()).days
    if days_out < 0:
        sys.exit(f"{date_str} is in the past.")
    if days_out > MAX_FORECAST_DAYS:
        sys.exit(
            f"{date_str} is {days_out} days away. Open-Meteo's free forecast only covers "
            f"about {MAX_FORECAST_DAYS} days ahead, so try a closer date."
        )
    return parsed


def validate_date_range(start_str: str, end_str: str):
    start = validate_date(start_str)
    end = validate_date(end_str)
    if end < start:
        sys.exit(f"{end_str} is before {start_str} — the end date has to come after the start date.")
    return start_str, end_str


def main():
    args = parse_args()

    if args.end_date:
        start_date, end_date = validate_date_range(args.date, args.end_date)
    else:
        start_date = end_date = validate_date(args.date).isoformat()

    lat, lon, place = geocode_city(args.city)
    daily_forecasts = get_forecast_range(lat, lon, start_date, end_date)
    all_conditions = [classify_conditions(f) for f in daily_forecasts]

    if args.end_date:
        packing_list = build_packing_list(all_conditions)
        narrative = build_trip_narrative(
            place, start_date, end_date, args.arrival, daily_forecasts, all_conditions, packing_list
        )
        print(f"\n{narrative}\n")
    else:
        forecast = daily_forecasts[0]
        outfit = suggest_outfit(all_conditions[0], arrival=args.arrival)

        print(f"\n{place}")
        print(f"\n{forecast['date']}")
        print(
            f"Forecast: {forecast['temp_min']:.0f}–{forecast['temp_max']:.0f}°C, "
            f"{forecast['rain_chance']:.0f}% chance of rain, "
            f"wind up to {forecast['wind_max']:.0f} km/h"
        )
        if args.arrival:
            print(f"Arrival: {args.arrival}")
        print(f"Suggestion: {outfit}\n")


if __name__ == "__main__":
    main()
