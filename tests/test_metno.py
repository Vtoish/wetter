# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

from typing import Any
from unittest.mock import patch, MagicMock, Mock

from services import metno


SAMPLE_FORECAST: dict[str, Any] = {
    "type": "Feature",
    "properties": {
        "timeseries": [
            {
                "time": "2026-04-04T12:00:00Z",
                "data": {
                    "instant": {
                        "details": {
                            "air_temperature": 10.5,
                            "relative_humidity": 72.0,
                            "wind_speed": 5.1,
                        }
                    },
                    "next_1_hours": {
                        "summary": {"symbol_code": "partlycloudy_day"},
                        "details": {"precipitation_amount": 0.0},
                    },
                },
            },
            {
                "time": "2026-04-04T13:00:00Z",
                "data": {
                    "instant": {
                        "details": {
                            "air_temperature": 11.2,
                            "relative_humidity": 68.0,
                            "wind_speed": 4.8,
                        }
                    },
                    "next_1_hours": {
                        "summary": {"symbol_code": "cloudy"},
                        "details": {"precipitation_amount": 0.2},
                    },
                },
            },
            {
                "time": "2026-04-05T12:00:00Z",
                "data": {
                    "instant": {
                        "details": {
                            "air_temperature": 8.0,
                            "relative_humidity": 80.0,
                            "wind_speed": 6.0,
                        }
                    },
                    "next_6_hours": {
                        "summary": {"symbol_code": "rain"},
                        "details": {"precipitation_amount": 3.5},
                    },
                },
            },
        ]
    },
}


@patch("services.metno.requests.get")
def test_fetch_weather_success(mock_get: MagicMock) -> None:
    mock_resp: Mock = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_FORECAST
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp

    result: dict[str, Any] | None = metno.fetch_weather(52.52, 13.41)
    assert result is not None

    assert result["source"] == "metno"
    assert result["current"]["temperature"] == 10.5
    assert result["current"]["humidity"] == 72.0
    assert result["current"]["weather_code"] is None
    assert result["current"]["description"] == "Partly cloudy"

    # Check daily aggregation
    assert len(result["daily"]) == 2
    day1: dict[str, Any] = result["daily"][0]
    assert day1["date"] == "2026-04-04"
    assert day1["temp_max"] == 11.2
    assert day1["temp_min"] == 10.5


@patch("services.metno.requests.get")
def test_fetch_weather_sends_user_agent(mock_get: MagicMock) -> None:
    mock_resp: Mock = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_FORECAST
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp

    metno.fetch_weather(52.52, 13.41)

    call_kwargs: Any = mock_get.call_args
    assert "User-Agent" in call_kwargs.kwargs.get("headers", {}) or \
           "User-Agent" in call_kwargs[1].get("headers", {})


@patch("services.metno.requests.get")
def test_fetch_weather_network_error(mock_get: MagicMock) -> None:
    import requests
    mock_get.side_effect = requests.ConnectionError()

    result: dict[str, Any] | None = metno.fetch_weather(52.52, 13.41)
    assert result is None


def test_wind_speed_conversion() -> None:
    """Met.no wind speed (m/s) should be converted to km/h."""
    raw: dict[str, Any] = {
        "properties": {
            "timeseries": [
                {
                    "time": "2026-04-04T12:00:00Z",
                    "data": {
                        "instant": {
                            "details": {
                                "air_temperature": 10.0,
                                "relative_humidity": 50.0,
                                "wind_speed": 5.0,
                            }
                        },
                        "next_1_hours": {
                            "summary": {"symbol_code": "clearsky"},
                            "details": {"precipitation_amount": 0.0},
                        },
                    },
                }
            ]
        }
    }
    result: dict[str, Any] | None = metno._normalize(raw)
    assert result is not None
    assert result["current"]["wind_speed"] == 18.0  # 5.0 * 3.6


def test_strip_variant() -> None:
    assert metno._strip_variant("clearsky_day") == "clearsky"
    assert metno._strip_variant("rain_night") == "rain"
    assert metno._strip_variant("fog_polartwilight") == "fog"
    assert metno._strip_variant("cloudy") == "cloudy"


def test_symbol_codes_lookup() -> None:
    assert metno.SYMBOL_CODES["clearsky"] == "Clear sky"
    assert metno.SYMBOL_CODES["heavyrain"] == "Heavy rain"
    assert "partlycloudy" in metno.SYMBOL_CODES
