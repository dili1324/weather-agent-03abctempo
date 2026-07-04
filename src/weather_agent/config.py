from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


class ConfigError(RuntimeError):
    """Raised when required runtime configuration is missing or invalid."""


def _get_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    telegram_chat_id: str
    tempo_bin: str
    mpp_max_spend_usd: str
    weather_base_url: str
    weather_payment_mode: str
    mppx_helper_dir: str
    mppx_command_timeout_seconds: int
    openai_base_url: str
    city_query: str
    units: str
    lang: str
    enable_gpt_summary: bool
    gpt_model: str

    @classmethod
    def from_env(cls) -> "Settings":
        telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
        telegram_chat_id = os.getenv("TELEGRAM_CHAT_ID", "").strip()

        missing = [
            name
            for name, value in {
                "TELEGRAM_BOT_TOKEN": telegram_bot_token,
                "TELEGRAM_CHAT_ID": telegram_chat_id,
            }.items()
            if not value
        ]
        if missing:
            raise ConfigError(f"Missing required environment variables: {', '.join(missing)}")

        weather_payment_mode = os.getenv("WEATHER_PAYMENT_MODE", "cli").strip().lower() or "cli"
        if weather_payment_mode not in {"cli", "mppx"}:
            raise ConfigError("WEATHER_PAYMENT_MODE must be either 'cli' or 'mppx'")

        default_mppx_helper_dir = Path(__file__).resolve().parents[2] / "node_mppx"
        timeout_raw = os.getenv("MPPX_COMMAND_TIMEOUT_SECONDS", "120").strip() or "120"
        try:
            mppx_command_timeout_seconds = int(timeout_raw)
        except ValueError as exc:
            raise ConfigError("MPPX_COMMAND_TIMEOUT_SECONDS must be an integer") from exc
        if mppx_command_timeout_seconds <= 0:
            raise ConfigError("MPPX_COMMAND_TIMEOUT_SECONDS must be greater than zero")

        return cls(
            telegram_bot_token=telegram_bot_token,
            telegram_chat_id=telegram_chat_id,
            tempo_bin=os.getenv("TEMPO_BIN", "tempo").strip() or "tempo",
            mpp_max_spend_usd=os.getenv("MPP_MAX_SPEND_USD", "0.05").strip() or "0.05",
            weather_base_url=os.getenv(
                "OPENWEATHER_MPP_BASE_URL",
                "https://openweather.mpp.paywithlocus.com/openweather",
            ).rstrip("/"),
            weather_payment_mode=weather_payment_mode,
            mppx_helper_dir=os.getenv(
                "MPPX_HELPER_DIR",
                str(default_mppx_helper_dir),
            ).strip()
            or str(default_mppx_helper_dir),
            mppx_command_timeout_seconds=mppx_command_timeout_seconds,
            openai_base_url=os.getenv(
                "OPENAI_MPP_BASE_URL",
                "https://openai.mpp.tempo.xyz",
            ).rstrip("/"),
            city_query=os.getenv("WEATHER_CITY_QUERY", "Hanoi,VN").strip() or "Hanoi,VN",
            units=os.getenv("WEATHER_UNITS", "metric").strip() or "metric",
            lang=os.getenv("WEATHER_LANG", "vi").strip() or "vi",
            enable_gpt_summary=_get_bool("ENABLE_GPT_SUMMARY", default=False),
            gpt_model=os.getenv("GPT_MODEL", "gpt-4o").strip() or "gpt-4o",
        )
