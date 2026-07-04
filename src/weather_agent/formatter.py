from __future__ import annotations

from datetime import datetime
from typing import Any
from zoneinfo import ZoneInfo


def _weather_description(weather: dict[str, Any]) -> str:
    entries = weather.get("weather")
    if isinstance(entries, list) and entries:
        description = entries[0].get("description")
        if isinstance(description, str) and description:
            return description
    return "không rõ"


def format_weather_message(weather: dict[str, Any], summary: str | None = None) -> str:
    location = weather.get("_location", {})
    location_name = location.get("name", "Hà Nội") if isinstance(location, dict) else "Hà Nội"
    main = weather.get("main", {}) if isinstance(weather.get("main"), dict) else {}
    wind = weather.get("wind", {}) if isinstance(weather.get("wind"), dict) else {}
    timestamp = datetime.now(ZoneInfo("Asia/Ho_Chi_Minh")).strftime("%Y-%m-%d %H:%M")

    temp = main.get("temp", "N/A")
    feels_like = main.get("feels_like", "N/A")
    humidity = main.get("humidity", "N/A")
    wind_speed = wind.get("speed", "N/A")

    lines = [
        f"Thời tiết {location_name} - {timestamp} (Asia/Ho_Chi_Minh)",
        f"Nhiệt độ: {temp}°C, cảm giác như {feels_like}°C",
        f"Tình trạng: {_weather_description(weather)}",
        f"Độ ẩm: {humidity}%, gió: {wind_speed} m/s",
    ]
    if summary:
        lines.extend(["", summary])
    return "\n".join(lines)

