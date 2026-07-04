from __future__ import annotations

import json
import subprocess
from pathlib import Path
from typing import Any

import pytest

from weather_agent.mppx_weather_client import MppxWeatherClient
from weather_agent.weather_client import WeatherDataError


def test_mppx_weather_client_parses_helper_json(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    payload = {
        "ok": True,
        "run": {
            "geocode": {
                "success": True,
                "data": [{"name": "Hà Nội", "lat": 21.0283334, "lon": 105.854041}],
            },
            "currentWeather": {
                "success": True,
                "data": {
                    "main": {"temp": 31.2},
                    "weather": [{"description": "mây đen u ám"}],
                },
            },
        },
    }
    calls: list[dict[str, Any]] = []

    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        calls.append({"args": args, "kwargs": kwargs})
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout=json.dumps(payload),
            stderr="[mppx-helper] ok",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    client = MppxWeatherClient(helper_dir=str(tmp_path), timeout_seconds=10)
    weather = client.get_hanoi_weather("Hanoi,VN", "metric", "vi")

    assert weather["main"]["temp"] == 31.2
    assert weather["_location"]["name"] == "Hà Nội"
    assert calls[0]["args"][0][1:] == ["run", "--silent", "weather:once"]
    assert Path(calls[0]["args"][0][0]).name == "npm"
    assert calls[0]["kwargs"]["cwd"] == tmp_path
    assert calls[0]["kwargs"]["env"]["WEATHER_CITY_QUERY"] == "Hanoi,VN"


def test_mppx_weather_client_rejects_dirty_stdout(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    def fake_run(*args: Any, **kwargs: Any) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args=args[0],
            returncode=0,
            stdout="npm noise\n{}",
            stderr="",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    client = MppxWeatherClient(helper_dir=str(tmp_path), timeout_seconds=10)

    with pytest.raises(WeatherDataError):
        client.get_hanoi_weather("Hanoi,VN", "metric", "vi")
