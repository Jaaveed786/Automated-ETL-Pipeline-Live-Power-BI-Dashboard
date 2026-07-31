"""
Tests for WeatherExtractor — uses mock HTTP responses so no live API calls are made.
"""
import json
import pytest
from unittest.mock import patch, MagicMock
from src.extractors.weather_extractor import WeatherExtractor

MOCK_CONFIG = {
    "pipeline": {"name": "test_pipeline", "raw_data_dir": "data/raw", "retention_days": 30},
    "api": {
        "base_url": "https://api.open-meteo.com/v1/forecast",
        "hourly_metrics": ["temperature_2m", "relative_humidity_2m", "precipitation",
                           "wind_speed_10m", "surface_pressure"],
        "timeout_seconds": 10,
        "max_retries": 1,
    },
    "cities": [
        {"id": "LON", "name": "London", "country": "United Kingdom",
         "latitude": 51.5074, "longitude": -0.1278, "timezone": "Europe/London"},
    ],
}

MOCK_API_RESPONSE = {
    "hourly": {
        "time":                ["2024-01-15T00:00", "2024-01-15T01:00"],
        "temperature_2m":      [5.2, 4.8],
        "relative_humidity_2m":[82, 85],
        "precipitation":       [0.0, 0.2],
        "wind_speed_10m":      [12.5, 14.0],
        "surface_pressure":    [1013.2, 1012.8],
    }
}


@patch("src.extractors.weather_extractor.WeatherExtractor._archive_raw_payload")
@patch("requests.Session.get")
def test_fetch_city_weather_returns_dict(mock_get, mock_archive):
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_API_RESPONSE
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    extractor = WeatherExtractor(MOCK_CONFIG)
    result = extractor.fetch_city_weather(MOCK_CONFIG["cities"][0])

    assert isinstance(result, dict)
    assert result["city_id"] == "LON"
    assert result["city_name"] == "London"
    assert "hourly" in result


@patch("src.extractors.weather_extractor.WeatherExtractor._archive_raw_payload")
@patch("requests.Session.get")
def test_extract_all_returns_list(mock_get, mock_archive):
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_API_RESPONSE
    mock_response.raise_for_status = MagicMock()
    mock_get.return_value = mock_response

    extractor = WeatherExtractor(MOCK_CONFIG)
    results = extractor.extract_all()

    assert isinstance(results, list)
    assert len(results) == 1


@patch("requests.Session.get")
def test_fetch_raises_on_http_error(mock_get):
    import requests
    mock_response = MagicMock()
    mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError("404 Not Found")
    mock_get.return_value = mock_response

    extractor = WeatherExtractor(MOCK_CONFIG)
    with pytest.raises(requests.exceptions.HTTPError):
        extractor.fetch_city_weather(MOCK_CONFIG["cities"][0])
