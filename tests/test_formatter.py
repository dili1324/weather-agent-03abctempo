from weather_agent.formatter import format_weather_message


def test_format_weather_message_contains_core_fields() -> None:
    weather = {
        "_location": {"name": "Hanoi"},
        "main": {"temp": 28.5, "feels_like": 31.2, "humidity": 80},
        "wind": {"speed": 2.4},
        "weather": [{"description": "mây rải rác"}],
    }

    message = format_weather_message(weather, summary="Mang áo mưa mỏng nếu ra ngoài.")

    assert "Thời tiết Hanoi" in message
    assert "28.5°C" in message
    assert "mây rải rác" in message
    assert "Mang áo mưa" in message

