from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from weather_agent.tempo_client import TempoRequestClient

logger = logging.getLogger(__name__)


class WeatherDataError(RuntimeError):
    """Raised when weather data is missing or malformed."""


def _unwrap_geocode_results(data: Any) -> list[Any]:
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("data", "results", "result", "body"):
            value = data.get(key)
            if isinstance(value, list):
                return value
            if isinstance(value, dict):
                nested = _unwrap_geocode_results(value)
                if nested:
                    return nested
    return []


def _unwrap_payload(data: Any) -> Any:
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    return data


@dataclass(frozen=True)
class WeatherClient:
    tempo: TempoRequestClient
    base_url: str

    def geocode(self, query: str) -> dict[str, Any]:
        logger.info("Calling OpenWeather MPP geocode query=%s", query)
        data = self.tempo.post_json(f"{self.base_url}/geocode", {"q": query, "limit": 1})
        logger.info("OpenWeather MPP geocode raw response=%s", data)
        results = _unwrap_geocode_results(data)
        if not results:
            raise WeatherDataError(f"No geocoding result returned for {query!r}")
        first = results[0]
        if not isinstance(first, dict) or "lat" not in first or "lon" not in first:
            raise WeatherDataError("Geocoding response did not include lat/lon")
        logger.info("OpenWeather MPP geocode completed query=%s", query)
        return first

    def current_weather(self, lat: float, lon: float, units: str, lang: str) -> dict[str, Any]:
        logger.info(
            "Calling OpenWeather MPP current-weather lat=%.4f lon=%.4f units=%s lang=%s",
            lat,
            lon,
            units,
            lang,
        )
        data = self.tempo.post_json(
            f"{self.base_url}/current-weather",
            {"lat": lat, "lon": lon, "units": units, "lang": lang},
        )
        data = _unwrap_payload(data)
        if not isinstance(data, dict):
            raise WeatherDataError("Current weather response was not a JSON object")
        logger.info("OpenWeather MPP current-weather completed")
        return data

    def get_hanoi_weather(self, city_query: str, units: str, lang: str) -> dict[str, Any]:
        location = self.geocode(city_query)
        weather = self.current_weather(float(location["lat"]), float(location["lon"]), units, lang)
        weather["_location"] = location
        return weather
