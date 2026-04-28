# SPDX-License-Identifier: AGPL-3.0-only
# Copyright (C) 2026 Vtoish (Vtoish@live.com)

from typing import Any
from unittest.mock import patch, MagicMock

from flask import Flask
from flask.testing import FlaskClient


def test_index_redirects_when_unauthenticated(client: FlaskClient, app: Flask) -> None:
    resp = client.get("/")
    assert resp.status_code == 302


def test_index_returns_200_when_authenticated(authenticated_client: FlaskClient) -> None:
    resp = authenticated_client.get("/")
    assert resp.status_code == 200
    assert b"Wetter" in resp.data


def test_weather_requires_auth(client: FlaskClient, app: Flask) -> None:
    resp = client.get("/api/weather?lat=52.52&lon=13.41")
    assert resp.status_code == 302


def test_weather_requires_params(authenticated_client: FlaskClient) -> None:
    resp = authenticated_client.get("/api/weather")
    assert resp.status_code == 400


@patch("services.openmeteo.fetch_weather")
@patch("services.metno.fetch_weather")
def test_weather_returns_data(mock_metno: MagicMock, mock_openmeteo: MagicMock, authenticated_client: FlaskClient) -> None:
    mock_openmeteo.return_value = {
        "source": "openmeteo",
        "current": {
            "temperature": 12.0,
            "humidity": 60,
            "wind_speed": 10.0,
            "weather_code": 0,
            "description": "Clear sky",
        },
        "daily": [],
    }
    mock_metno.return_value = None

    resp = authenticated_client.get("/api/weather?lat=52.52&lon=13.41")
    data: dict[str, Any] = resp.get_json()

    assert resp.status_code == 200
    assert data["source"] == "openmeteo"
    assert data["current"]["temperature"] == 12.0


@patch("services.openmeteo.fetch_weather")
@patch("services.metno.fetch_weather")
def test_weather_fallback_to_metno(mock_metno: MagicMock, mock_openmeteo: MagicMock, authenticated_client: FlaskClient) -> None:
    mock_openmeteo.return_value = None
    mock_metno.return_value = {
        "source": "metno",
        "current": {
            "temperature": 11.0,
            "humidity": 70,
            "wind_speed": 8.0,
            "weather_code": None,
            "description": "Cloudy",
        },
        "daily": [],
    }

    resp = authenticated_client.get("/api/weather?lat=52.52&lon=13.41")
    data: dict[str, Any] = resp.get_json()

    assert data["source"] == "metno"


@patch("services.openmeteo.fetch_weather")
@patch("services.metno.fetch_weather")
def test_weather_both_fail(mock_metno: MagicMock, mock_openmeteo: MagicMock, authenticated_client: FlaskClient) -> None:
    mock_openmeteo.return_value = None
    mock_metno.return_value = None

    resp = authenticated_client.get("/api/weather?lat=52.52&lon=13.41")
    data: dict[str, Any] = resp.get_json()

    assert resp.status_code == 200
    assert "error" in data
    assert data["current"] is None


@patch("services.rainviewer.fetch_radar_metadata")
def test_radar_returns_data(mock_radar: MagicMock, authenticated_client: FlaskClient) -> None:
    mock_radar.return_value = {"generated": 123, "host": "https://example.com", "frames": [], "nowcast": []}

    resp = authenticated_client.get("/api/radar")
    assert resp.status_code == 200


@patch("services.rainviewer.fetch_radar_metadata")
def test_radar_unavailable(mock_radar: MagicMock, authenticated_client: FlaskClient) -> None:
    mock_radar.return_value = None

    resp = authenticated_client.get("/api/radar")
    assert resp.status_code == 503


@patch("services.openmeteo.search_location")
def test_search_returns_results(mock_search: MagicMock, authenticated_client: FlaskClient) -> None:
    mock_search.return_value = [{"name": "Berlin", "country": "Germany",
                                  "admin1": "Berlin", "latitude": 52.52, "longitude": 13.41}]

    resp = authenticated_client.get("/api/search?q=Berlin")
    data: Any = resp.get_json()

    assert len(data) == 1
    assert data[0]["name"] == "Berlin"


def test_search_empty_query(authenticated_client: FlaskClient) -> None:
    resp = authenticated_client.get("/api/search?q=")
    data: Any = resp.get_json()
    assert data == []
