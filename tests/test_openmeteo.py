# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

from typing import Any
from unittest.mock import patch, MagicMock, Mock

from services import openmeteo


SAMPLE_FORECAST: dict[str, Any] = {
    "latitude": 52.52,
    "longitude": 13.41,
    "current": {
        "temperature_2m": 12.5,
        "relative_humidity_2m": 65,
        "wind_speed_10m": 14.2,
        "weather_code": 3,
    },
    "daily": {
        "time": ["2026-04-04", "2026-04-05"],
        "temperature_2m_max": [15.0, 13.2],
        "temperature_2m_min": [6.1, 5.8],
        "precipitation_sum": [0.0, 2.3],
        "weather_code": [3, 61],
    },
}

SAMPLE_GEOCODING: dict[str, Any] = {
    "results": [
        {
            "name": "Berlin",
            "country": "Germany",
            "admin1": "Berlin",
            "latitude": 52.52,
            "longitude": 13.41,
        }
    ]
}


@patch("services.openmeteo.requests.get")
def test_fetch_weather_success(mock_get: MagicMock) -> None:
    mock_resp: Mock = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_FORECAST
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp

    result: dict[str, Any] | None = openmeteo.fetch_weather(52.52, 13.41)
    assert result is not None

    assert result["source"] == "openmeteo"
    assert result["current"]["temperature"] == 12.5
    assert result["current"]["humidity"] == 65
    assert result["current"]["wind_speed"] == 14.2
    assert result["current"]["weather_code"] == 3
    assert result["current"]["description"] == "Overcast"
    assert len(result["daily"]) == 2
    assert result["daily"][0]["temp_max"] == 15.0
    assert result["daily"][1]["description"] == "Slight rain"


@patch("services.openmeteo.requests.get")
def test_fetch_weather_http_error(mock_get: MagicMock) -> None:
    mock_resp: Mock = Mock()
    import requests
    mock_resp.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
    mock_get.return_value = mock_resp

    result: dict[str, Any] | None = openmeteo.fetch_weather(52.52, 13.41)
    assert result is None


@patch("services.openmeteo.requests.get")
def test_fetch_weather_network_error(mock_get: MagicMock) -> None:
    import requests
    mock_get.side_effect = requests.ConnectionError("Connection refused")

    result: dict[str, Any] | None = openmeteo.fetch_weather(52.52, 13.41)
    assert result is None


@patch("services.openmeteo.requests.get")
def test_search_location_success(mock_get: MagicMock) -> None:
    mock_resp: Mock = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_GEOCODING
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp

    results: list[dict[str, Any]] = openmeteo.search_location("Berlin")

    assert len(results) == 1
    assert results[0]["name"] == "Berlin"
    assert results[0]["latitude"] == 52.52


@patch("services.openmeteo.requests.get")
def test_search_location_error(mock_get: MagicMock) -> None:
    import requests
    mock_get.side_effect = requests.ConnectionError()

    results: list[dict[str, Any]] = openmeteo.search_location("Berlin")
    assert results == []


def test_wmo_codes() -> None:
    assert openmeteo.WMO_CODES[0] == "Clear sky"
    assert openmeteo.WMO_CODES[95] == "Thunderstorm"
    assert 99 in openmeteo.WMO_CODES
