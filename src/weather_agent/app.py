from __future__ import annotations

import logging
from time import perf_counter

from weather_agent.config import Settings
from weather_agent.formatter import format_weather_message
from weather_agent.gpt_client import GptSummaryClient
from weather_agent.mppx_weather_client import MppxWeatherClient
from weather_agent.telegram_client import TelegramClient
from weather_agent.tempo_client import TempoRequestClient
from weather_agent.timing import timed_step
from weather_agent.weather_client import WeatherClient

logger = logging.getLogger(__name__)


def run(settings: Settings) -> None:
    started_at = perf_counter()
    logger.info(
        "Weather Agent started city=%s units=%s lang=%s weather_payment_mode=%s gpt_summary=%s",
        settings.city_query,
        settings.units,
        settings.lang,
        settings.weather_payment_mode,
        settings.enable_gpt_summary,
    )

    tempo = None
    if settings.weather_payment_mode == "cli" or settings.enable_gpt_summary:
        tempo = TempoRequestClient(
            tempo_bin=settings.tempo_bin,
            max_spend_usd=settings.mpp_max_spend_usd,
        )
        with timed_step(logger, "check Tempo Wallet"):
            tempo.check_wallet_ready()

    if settings.weather_payment_mode == "mppx":
        weather_client = MppxWeatherClient(
            helper_dir=settings.mppx_helper_dir,
            timeout_seconds=settings.mppx_command_timeout_seconds,
        )
        with timed_step(logger, "fetch OpenWeather MPP weather via mppx"):
            weather = weather_client.get_hanoi_weather(
                city_query=settings.city_query,
                units=settings.units,
                lang=settings.lang,
            )
    else:
        if tempo is None:
            raise RuntimeError("Tempo client was not initialized for CLI weather mode")
        weather_client = WeatherClient(tempo=tempo, base_url=settings.weather_base_url)
        with timed_step(logger, "fetch OpenWeather MPP weather via Tempo CLI"):
            weather = weather_client.get_hanoi_weather(
                city_query=settings.city_query,
                units=settings.units,
                lang=settings.lang,
            )

    summary = None
    if settings.enable_gpt_summary:
        if tempo is None:
            raise RuntimeError("Tempo client was not initialized for GPT summary")
        with timed_step(logger, "generate GPT summary via OpenAI MPP"):
            summary = GptSummaryClient(
                tempo=tempo,
                base_url=settings.openai_base_url,
                model=settings.gpt_model,
            ).summarize(weather)
    else:
        logger.info("Skipping GPT summary because ENABLE_GPT_SUMMARY is false")

    with timed_step(logger, "format Telegram message"):
        message = format_weather_message(weather, summary=summary)

    with timed_step(logger, "send Telegram notification"):
        TelegramClient(
            bot_token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
        ).send_message(message)

    elapsed_ms = (perf_counter() - started_at) * 1000
    logger.info("Weather Agent completed duration_ms=%.2f", elapsed_ms)
