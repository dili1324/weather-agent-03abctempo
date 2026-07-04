from typing import Any

import pytest

from weather_agent.weather_client import WeatherClient, WeatherDataError


class FakeTempo:
    def __init__(self, responses: list[Any]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, Any]]] = []

    def post_json(self, url: str, payload: dict[str, Any]) -> Any:
        self.calls.append((url, payload))
        return self.responses.pop(0)


def test_get_hanoi_weather_uses_geocode_then_current_weather() -> None:
    tempo = FakeTempo(
        [
            [{"name": "Hanoi", "lat": 21.0285, "lon": 105.8542}],
            {"main": {"temp": 30}, "weather": [{"description": "clear"}]},
        ]
    )
    client = WeatherClient(tempo=tempo, base_url="https://example.test/openweather")  # type: ignore[arg-type]

    weather = client.get_hanoi_weather("Hanoi,VN", "metric", "vi")

    assert weather["_location"]["name"] == "Hanoi"
    assert tempo.calls[0][0].endswith("/geocode")
    assert tempo.calls[0][1] == {"q": "Hanoi,VN", "limit": 1}
    assert tempo.calls[1][0].endswith("/current-weather")


def test_geocode_rejects_empty_response() -> None:
    client = WeatherClient(tempo=FakeTempo([[]]), base_url="https://example.test")  # type: ignore[arg-type]

    with pytest.raises(WeatherDataError):
        client.geocode("Hanoi,VN")


def test_geocode_accepts_locus_success_data_wrapper() -> None:
    client = WeatherClient(
        tempo=FakeTempo(
            [
                {
                    "success": True,
                    "data": [
                        {
                            "name": "Hà Nội",
                            "lat": 21.0283334,
                            "lon": 105.854041,
                            "country": "VN",
                        }
                    ],
                }
            ]
        ),
        base_url="https://example.test",
    )  # type: ignore[arg-type]

    location = client.geocode("Ha Noi,VN")

    assert location["name"] == "Hà Nội"
    assert location["lat"] == 21.0283334


def test_current_weather_accepts_locus_success_data_wrapper() -> None:
    client = WeatherClient(
        tempo=FakeTempo(
            [
                {
                    "success": True,
                    "data": {
                        "main": {"temp": 32.14},
                        "weather": [{"description": "mây đen u ám"}],
                    },
                }
            ]
        ),
        base_url="https://example.test",
    )  # type: ignore[arg-type]

    weather = client.current_weather(21.0283334, 105.854041, "metric", "vi")

    assert weather["main"]["temp"] == 32.14
