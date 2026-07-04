import pytest

from weather_agent.config import ConfigError, Settings


def test_settings_requires_telegram_secrets(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("TELEGRAM_BOT_TOKEN", raising=False)
    monkeypatch.delenv("TELEGRAM_CHAT_ID", raising=False)

    with pytest.raises(ConfigError):
        Settings.from_env()


def test_settings_defaults(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat")

    settings = Settings.from_env()

    assert settings.city_query == "Hanoi,VN"
    assert settings.units == "metric"
    assert settings.lang == "vi"
    assert settings.weather_payment_mode == "cli"
    assert settings.enable_gpt_summary is False


def test_settings_accepts_mppx_weather_payment_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat")
    monkeypatch.setenv("WEATHER_PAYMENT_MODE", "mppx")

    settings = Settings.from_env()

    assert settings.weather_payment_mode == "mppx"


def test_settings_rejects_invalid_weather_payment_mode(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("TELEGRAM_CHAT_ID", "chat")
    monkeypatch.setenv("WEATHER_PAYMENT_MODE", "invalid")

    with pytest.raises(ConfigError):
        Settings.from_env()
