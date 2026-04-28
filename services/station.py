# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

"""Ecowitt weather station ingestion.

Receives data pushed from Ecowitt Wittboy GW2001 and add-on sensors
via HTTP POST webhook. Parses, normalizes, and stores readings as
Observation records.

The ingest endpoint is not protected by login (devices push data)
but requires a valid API key or passkey.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from flask import Blueprint, Response, jsonify, request

import config

logger: logging.Logger = logging.getLogger(__name__)

station_bp: Blueprint = Blueprint("station", __name__, url_prefix="/station")


@station_bp.route("/ingest", methods=["POST"])
def ingest() -> Response | tuple[Response, int]:
    """Receive and store Ecowitt weather station data.

    Expects form-encoded or JSON data from the Ecowitt device.
    Validates the passkey before accepting data.
    """
    passkey: str = request.form.get("PASSKEY", "") or request.json.get("PASSKEY", "") if request.json else request.form.get("PASSKEY", "")

    if not config.ECOWITT_PASSKEY:
        return jsonify({"error": "Station ingestion not configured"}), 503

    if passkey != config.ECOWITT_PASSKEY:
        logger.warning("Station ingest: invalid passkey")
        return jsonify({"error": "Invalid passkey"}), 403

    raw_data: dict[str, Any] = dict(request.form) if request.form else (request.json or {})
    parsed: dict[str, Any] = parse_ecowitt(raw_data)

    # TODO: resolve sensor + location from hardware_id, store as Observation
    logger.info("Received station data: %d fields", len(parsed))

    return jsonify({"status": "ok", "fields": len(parsed)})


def parse_ecowitt(data: dict[str, Any]) -> dict[str, Any]:
    """Normalize raw Ecowitt payload to a canonical dict.

    Maps Ecowitt field names to standardized keys with proper units.
    Handles temperature (F->C), pressure (inHg->hPa), rain (in->mm),
    wind (mph->km/h), etc.

    Returns:
        Dict of normalized readings keyed by measurement type.
    """
    result: dict[str, Any] = {
        "raw_fields": len(data),
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }

    # Temperature (Ecowitt sends Fahrenheit)
    if "tempf" in data:
        try:
            result["temperature_c"] = round((float(data["tempf"]) - 32) * 5 / 9, 1)
        except (ValueError, TypeError):
            pass

    # Humidity
    if "humidity" in data:
        try:
            result["humidity"] = int(data["humidity"])
        except (ValueError, TypeError):
            pass

    # Pressure (inHg -> hPa)
    if "baromrelin" in data:
        try:
            result["pressure_hpa"] = round(float(data["baromrelin"]) * 33.8639, 1)
        except (ValueError, TypeError):
            pass

    # Wind speed (mph -> km/h)
    if "windspeedmph" in data:
        try:
            result["wind_speed_kmh"] = round(float(data["windspeedmph"]) * 1.60934, 1)
        except (ValueError, TypeError):
            pass

    # Wind direction
    if "winddir" in data:
        try:
            result["wind_direction"] = int(data["winddir"])
        except (ValueError, TypeError):
            pass

    # Rain (in -> mm)
    if "rainratein" in data:
        try:
            result["rain_rate_mm"] = round(float(data["rainratein"]) * 25.4, 1)
        except (ValueError, TypeError):
            pass

    # UV index
    if "uv" in data:
        try:
            result["uv_index"] = float(data["uv"])
        except (ValueError, TypeError):
            pass

    # Solar radiation
    if "solarradiation" in data:
        try:
            result["solar_radiation"] = float(data["solarradiation"])
        except (ValueError, TypeError):
            pass

    return result
