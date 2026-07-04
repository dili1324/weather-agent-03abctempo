from __future__ import annotations

import argparse
import logging
import os
import sys

from weather_agent.config import Settings
from weather_agent.gpt_client import GptSummaryClient
from weather_agent.logging_config import configure_logging
from weather_agent.telegram_client import TelegramClient
from weather_agent.tempo_client import TempoRequestClient
from weather_agent.weather_client import WeatherClient


def _tempo_from_env() -> TempoRequestClient:
    return TempoRequestClient(
        tempo_bin=os.getenv("TEMPO_BIN", "tempo"),
        max_spend_usd=os.getenv("MPP_MAX_SPEND_USD", "0.05"),
    )


def check_tempo() -> None:
    _tempo_from_env().check_wallet_ready()


def check_weather() -> None:
    tempo = _tempo_from_env()
    client = WeatherClient(
        tempo=tempo,
        base_url=os.getenv(
            "OPENWEATHER_MPP_BASE_URL",
            "https://openweather.mpp.paywithlocus.com/openweather",
        ).rstrip("/"),
    )
    weather = client.get_hanoi_weather(
        city_query=os.getenv("WEATHER_CITY_QUERY", "Hanoi,VN"),
        units=os.getenv("WEATHER_UNITS", "metric"),
        lang=os.getenv("WEATHER_LANG", "vi"),
    )
    location = weather.get("_location", {})
    main = weather.get("main", {})
    logging.info("Weather check OK location=%s temp=%s", location.get("name"), main.get("temp"))


def check_gpt() -> None:
    tempo = _tempo_from_env()
    summary = GptSummaryClient(
        tempo=tempo,
        base_url=os.getenv("OPENAI_MPP_BASE_URL", "https://openai.mpp.tempo.xyz").rstrip("/"),
        model=os.getenv("GPT_MODEL", "gpt-4o"),
    ).summarize(
        {
            "_location": {"name": "Hanoi"},
            "main": {"temp": 30, "feels_like": 33, "humidity": 75},
            "wind": {"speed": 2.0},
            "weather": [{"description": "mây rải rác"}],
        }
    )
    logging.info("GPT check OK summary=%s", summary)


def check_telegram() -> None:
    settings = Settings.from_env()
    TelegramClient(
        bot_token=settings.telegram_bot_token,
        chat_id=settings.telegram_chat_id,
    ).send_message("Weather Agent debug check: Telegram is working.")


def main() -> int:
    parser = argparse.ArgumentParser(description="Run MVP debug checks for Weather Agent.")
    parser.add_argument(
        "check",
        choices=["tempo", "weather", "telegram", "gpt", "all"],
        help="Which integration to check.",
    )
    args = parser.parse_args()

    configure_logging()
    try:
        if args.check in {"tempo", "all"}:
            check_tempo()
        if args.check in {"weather", "all"}:
            check_weather()
        gpt_enabled = os.getenv("ENABLE_GPT_SUMMARY", "").strip().lower() in {"1", "true", "yes", "on"}
        if args.check == "gpt" or (args.check == "all" and gpt_enabled):
            check_gpt()
        elif args.check == "all":
            logging.info("Skipping GPT check because ENABLE_GPT_SUMMARY is not true")
        if args.check in {"telegram", "all"}:
            check_telegram()
    except Exception:
        logging.exception("Debug check failed")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
