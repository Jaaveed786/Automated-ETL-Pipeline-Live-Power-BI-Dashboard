import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
import requests
from urllib3.util import Retry
from requests.adapters import HTTPAdapter

from src.utils.logger import setup_logger

logger = setup_logger("weather_extractor")

class WeatherExtractor:
    """Extracts weather metrics from Open-Meteo REST API with resilient retries."""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.base_url = config["api"]["base_url"]
        self.cities = config["cities"]
        self.hourly_metrics = config["api"]["hourly_metrics"]
        self.timeout = config["api"].get("timeout_seconds", 15)
        self.raw_data_dir = Path(config["pipeline"].get("raw_data_dir", "data/raw"))
        self.raw_data_dir.mkdir(parents=True, exist_ok=True)

        self.session = self._create_resilient_session(
            max_retries=config["api"].get("max_retries", 3)
        )

    def _create_resilient_session(self, max_retries: int) -> requests.Session:
        session = requests.Session()
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("https://", adapter)
        session.mount("http://", adapter)
        return session

    def fetch_city_weather(self, city: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch hourly weather metrics for a single city configuration."""
        params = {
            "latitude": city["latitude"],
            "longitude": city["longitude"],
            "hourly": ",".join(self.hourly_metrics),
            "timezone": city["timezone"],
            "forecast_days": 2
        }

        logger.info(f"Extracting weather data for {city['name']} ({city['id']})...")
        import urllib3
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        response = self.session.get(self.base_url, params=params, timeout=self.timeout, verify=False)
        response.raise_for_status()
        
        data = response.json()
        data["city_id"] = city["id"]
        data["city_name"] = city["name"]
        data["country"] = city["country"]
        data["timezone"] = city["timezone"]
        return data

    def extract_all(self) -> List[Dict[str, Any]]:
        """Extract weather data across all configured cities and save raw dump."""
        extracted_payloads = []
        for city in self.cities:
            try:
                payload = self.fetch_city_weather(city)
                extracted_payloads.append(payload)
            except Exception as e:
                logger.error(f"Failed to extract weather for city {city['name']}: {e}")
                raise

        self._archive_raw_payload(extracted_payloads)
        return extracted_payloads

    def _archive_raw_payload(self, payloads: List[Dict[str, Any]]) -> str:
        timestamp_str = datetime.utcnow().strftime("%Y-%m-%d_%H%M%S")
        archive_path = self.raw_data_dir / f"weather_raw_{timestamp_str}.json"
        
        with open(archive_path, "w", encoding="utf-8") as f:
            json.dump(payloads, f, indent=2)
            
        logger.info(f"Successfully archived raw payload to {archive_path}")
        return str(archive_path)
