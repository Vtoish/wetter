# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

import logging
from typing import Any

import requests
import config

logger = logging.getLogger(__name__)

MAPS_URL = "https://api.rainviewer.com/public/weather-maps.json"


def fetch_radar_metadata() -> dict[str, Any] | None:
    """Fetch radar tile metadata from RainViewer."""
    try:
        resp = requests.get(MAPS_URL, timeout=config.REQUEST_TIMEOUT)
        resp.raise_for_status()
        return _normalize(resp.json())
    except requests.RequestException as e:
        logger.error("RainViewer request failed: %s", e)
        return None


def _normalize(raw: dict[str, Any]) -> dict[str, Any]:
    host: str = raw.get("host", "https://tilecache.rainviewer.com")
    generated: int = raw.get("generated", 0)

    radar: dict[str, Any] = raw.get("radar", {})
    past: list[dict[str, Any]] = radar.get("past", [])
    nowcast: list[dict[str, Any]] = radar.get("nowcast", [])

    def build_frames(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [
            {"time": entry["time"], "path": entry["path"]}
            for entry in entries
        ]

    return {
        "generated": generated,
        "host": host,
        "frames": build_frames(past),
        "nowcast": build_frames(nowcast),
    }
