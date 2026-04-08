import logging
from typing import Any

import requests
import config

logger = logging.getLogger(__name__)

FORECAST_URL = "https://api.open-meteo.com/v1/forecast"
GEOCODING_URL = "https://geocoding-api.open-meteo.com/v1/search"

WMO_CODES: dict[int, str] = {
    0: "Clear sky",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Foggy",
    48: "Depositing rime fog",
    51: "Light drizzle",
    53: "Moderate drizzle",
    55: "Dense drizzle",
    56: "Light freezing drizzle",
    57: "Dense freezing drizzle",
    61: "Slight rain",
    63: "Moderate rain",
    65: "Heavy rain",
    66: "Light freezing rain",
    67: "Heavy freezing rain",
    71: "Slight snowfall",
    73: "Moderate snowfall",
    75: "Heavy snowfall",
    77: "Snow grains",
    80: "Slight rain showers",
    81: "Moderate rain showers",
    82: "Violent rain showers",
    85: "Slight snow showers",
    86: "Heavy snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm with slight hail",
    99: "Thunderstorm with heavy hail",
}


def fetch_weather(lat: float, lon: float) -> dict[str, Any] | None:
    """Fetch current weather and 7-day forecast from Open-Meteo."""
    try:
        resp = requests.get(FORECAST_URL, params={
            "latitude": lat,
            "longitude": lon,
            "current": "temperature_2m,relative_humidity_2m,wind_speed_10m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,weather_code",
            "forecast_days": 7,
            "timezone": "auto",
        }, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        return _normalize(resp.json())
    except requests.RequestException as e:
        logger.error("Open-Meteo request failed: %s", e)
        return None


def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
    current: dict[str, Any] = raw.get("current", {})
    daily: dict[str, Any] = raw.get("daily", {})

    weather_code: int | None = current.get("weather_code")
    daily_dates: list[str] = daily.get("time", [])
    daily_maxs: list[float] = daily.get("temperature_2m_max", [])
    daily_mins: list[float] = daily.get("temperature_2m_min", [])
    daily_precip: list[float] = daily.get("precipitation_sum", [])
    daily_codes: list[int] = daily.get("weather_code", [])

    return {
        "source": "openmeteo",
        "current": {
            "temperature": current.get("temperature_2m"),
            "humidity": current.get("relative_humidity_2m"),
            "wind_speed": current.get("wind_speed_10m"),
            "weather_code": weather_code,
            "description": WMO_CODES.get(weather_code or 0, "Unknown"),
        },
        "daily": [
            {
                "date": daily_dates[i],
                "temp_max": daily_maxs[i],
                "temp_min": daily_mins[i],
                "precipitation": daily_precip[i],
                "description": WMO_CODES.get(daily_codes[i], ""),
            }
            for i in range(len(daily_dates))
        ],
    }


def search_location(query: str) -> list[dict[str, Any]]:
    """Search for locations by name using Open-Meteo geocoding API."""
    try:
        resp = requests.get(GEOCODING_URL, params={
            "name": query,
            "count": 5,
            "language": "en",
        }, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        results: list[dict[str, Any]] = resp.json().get("results", [])
        return [
            {
                "name": r.get("name"),
                "country": r.get("country"),
                "admin1": r.get("admin1"),
                "latitude": r.get("latitude"),
                "longitude": r.get("longitude"),
            }
            for r in results
        ]
    except requests.RequestException as e:
        logger.error("Open-Meteo geocoding failed: %s", e)
        return []
