from typing import Any
from unittest.mock import patch, MagicMock, Mock

from services import rainviewer


SAMPLE_MAPS: dict[str, Any] = {
    "version": "2.0",
    "generated": 1712188800,
    "host": "https://tilecache.rainviewer.com",
    "radar": {
        "past": [
            {"time": 1712188200, "path": "/v2/radar/1712188200"},
            {"time": 1712188800, "path": "/v2/radar/1712188800"},
        ],
        "nowcast": [
            {"time": 1712189400, "path": "/v2/radar/1712189400"},
        ],
    },
}


@patch("services.rainviewer.requests.get")
def test_fetch_radar_success(mock_get: MagicMock) -> None:
    mock_resp: Mock = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_MAPS
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp

    result: dict[str, Any] | None = rainviewer.fetch_radar_metadata()
    assert result is not None

    assert result["generated"] == 1712188800
    assert len(result["frames"]) == 2
    assert len(result["nowcast"]) == 1


@patch("services.rainviewer.requests.get")
def test_fetch_radar_error(mock_get: MagicMock) -> None:
    import requests
    mock_get.side_effect = requests.ConnectionError()

    result: dict[str, Any] | None = rainviewer.fetch_radar_metadata()
    assert result is None


@patch("services.rainviewer.requests.get")
def test_returns_host_and_paths(mock_get: MagicMock) -> None:
    mock_resp: Mock = Mock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = SAMPLE_MAPS
    mock_resp.raise_for_status = Mock()
    mock_get.return_value = mock_resp

    result: dict[str, Any] | None = rainviewer.fetch_radar_metadata()
    assert result is not None

    assert result["host"] == "https://tilecache.rainviewer.com"
    assert result["frames"][0]["path"] == "/v2/radar/1712188200"
    assert result["frames"][0]["time"] == 1712188200
