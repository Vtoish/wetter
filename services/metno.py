import logging
from collections import defaultdict
from datetime import datetime
from typing import Any

import requests
import config

logger = logging.getLogger(__name__)

FORECAST_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

SYMBOL_CODES: dict[str, str] = {
    "clearsky": "Clear sky",
    "cloudy": "Cloudy",
    "fair": "Fair",
    "fog": "Fog",
    "heavyrain": "Heavy rain",
    "heavyrainandthunder": "Heavy rain and thunder",
    "heavyrainshowers": "Heavy rain showers",
    "heavyrainshowersandthunder": "Heavy rain showers and thunder",
    "heavysleet": "Heavy sleet",
    "heavysleetandthunder": "Heavy sleet and thunder",
    "heavysleetshowers": "Heavy sleet showers",
    "heavysleetshowersandthunder": "Heavy sleet showers and thunder",
    "heavysnow": "Heavy snow",
    "heavysnowandthunder": "Heavy snow and thunder",
    "heavysnowshowers": "Heavy snow showers",
    "heavysnowshowersandthunder": "Heavy snow showers and thunder",
    "lightrain": "Light rain",
    "lightrainandthunder": "Light rain and thunder",
    "lightrainshowers": "Light rain showers",
    "lightrainshowersandthunder": "Light rain showers and thunder",
    "lightsleet": "Light sleet",
    "lightsleetandthunder": "Light sleet and thunder",
    "lightsleetshowers": "Light sleet showers",
    "lightsnow": "Light snow",
    "lightsnowandthunder": "Light snow and thunder",
    "lightsnowshowers": "Light snow showers",
    "lightssleetshowersandthunder": "Light sleet showers and thunder",
    "lightsssnowshowersandthunder": "Light snow showers and thunder",
    "partlycloudy": "Partly cloudy",
    "rain": "Rain",
    "rainandthunder": "Rain and thunder",
    "rainshowers": "Rain showers",
    "rainshowersandthunder": "Rain showers and thunder",
    "sleet": "Sleet",
    "sleetandthunder": "Sleet and thunder",
    "sleetshowers": "Sleet showers",
    "sleetshowersandthunder": "Sleet showers and thunder",
    "snow": "Snow",
    "snowandthunder": "Snow and thunder",
    "snowshowers": "Snow showers",
    "snowshowersandthunder": "Snow showers and thunder",
}


def _strip_variant(symbol_code: str) -> str:
    """Remove _day/_night/_polartwilight suffix from symbol code."""
    for suffix in ("_day", "_night", "_polartwilight"):
        if symbol_code.endswith(suffix):
            return symbol_code[: -len(suffix)]
    return symbol_code


def fetch_weather(lat: float, lon: float) -> dict[str, Any] | None:
    """Fetch compact forecast from Met.no Locationforecast API."""
    try:
        resp = requests.get(
            FORECAST_URL,
            params={"lat": round(lat, 4), "lon": round(lon, 4)},
            headers={"User-Agent": config.METNO_USER_AGENT},
            timeout=config.REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return _normalize(resp.json())
    except requests.RequestException as e:
        logger.error("Met.no request failed: %s", e)
        return None


def _normalize(raw: dict[str, Any]) -> dict[str, Any] | None:
    timeseries: list[dict[str, Any]] = raw.get("properties", {}).get("timeseries", [])
    if not timeseries:
        return None

    # Current conditions from first entry
    first: dict[str, Any] = timeseries[0]
    instant: dict[str, Any] = first["data"]["instant"]["details"]
    next_period: dict[str, Any] = (
        first["data"].get("next_1_hours")
        or first["data"].get("next_6_hours")
        or {}
    )
    symbol: str = next_period.get("summary", {}).get("symbol_code", "")
    base_symbol: str = _strip_variant(symbol)

    current: dict[str, Any] = {
        "temperature": instant.get("air_temperature"),
        "humidity": instant.get("relative_humidity"),
        "wind_speed": round(float(instant.get("wind_speed", 0)) * 3.6, 1),
        "weather_code": None,
        "description": SYMBOL_CODES.get(base_symbol, symbol),
    }

    # Aggregate daily forecasts
    days: defaultdict[str, list[tuple[datetime, dict[str, Any]]]] = defaultdict(list)
    for entry in timeseries:
        dt = datetime.fromisoformat(str(entry["time"]).replace("Z", "+00:00"))
        date_str = dt.strftime("%Y-%m-%d")
        days[date_str].append((dt, entry["data"]))

    daily: list[dict[str, Any]] = []
    for date_str in sorted(days.keys())[:7]:
        entries = days[date_str]
        temps: list[float] = [
            e["instant"]["details"].get("air_temperature")
            for _, e in entries
            if e["instant"]["details"].get("air_temperature") is not None
        ]
        precip: float = 0.0
        for _, e in entries:
            p: float | None = e.get("next_1_hours", {}).get("details", {}).get("precipitation_amount")
            if p is None:
                p6: float | None = e.get("next_6_hours", {}).get("details", {}).get("precipitation_amount")
                if p6 is not None:
                    p = p6
            if p is not None:
                precip += p

        # Pick symbol closest to noon
        noon_symbol: str = ""
        best_dist: int | None = None
        for dt, e in entries:
            period: dict[str, Any] = e.get("next_1_hours") or e.get("next_6_hours") or {}
            sc: str = period.get("summary", {}).get("symbol_code", "")
            if not sc:
                continue
            dist: int = abs(dt.hour - 12)
            if best_dist is None or dist < best_dist:
                best_dist = dist
                noon_symbol = sc

        daily.append({
            "date": date_str,
            "temp_max": max(temps) if temps else None,
            "temp_min": min(temps) if temps else None,
            "precipitation": round(precip, 1),
            "description": SYMBOL_CODES.get(_strip_variant(noon_symbol), noon_symbol),
        })

    return {
        "source": "metno",
        "current": current,
        "daily": daily,
    }
