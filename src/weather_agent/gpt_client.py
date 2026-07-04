from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any

from weather_agent.tempo_client import TempoRequestClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class GptSummaryClient:
    tempo: TempoRequestClient
    base_url: str
    model: str

    def summarize(self, weather: dict[str, Any]) -> str:
        logger.info("Calling GPT summary through OpenAI MPP model=%s", self.model)
        prompt = (
            "Tóm tắt thời tiết Hà Nội bằng tiếng Việt trong tối đa 3 câu. "
            "Nêu nhiệt độ, cảm giác thực tế, tình trạng trời, độ ẩm/gió nếu có, "
            "và một lời khuyên ngắn. Dữ liệu JSON:\n"
            f"{weather}"
        )
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": "Bạn là trợ lý thời tiết ngắn gọn, chính xác."},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        }
        response = self.tempo.post_json(f"{self.base_url}/v1/chat/completions", payload)
        if not isinstance(response, dict):
            raise RuntimeError("OpenAI MPP response was not a JSON object")
        choices = response.get("choices")
        if not isinstance(choices, list) or not choices:
            raise RuntimeError("OpenAI MPP response did not contain choices")
        message = choices[0].get("message", {})
        content = message.get("content")
        if not isinstance(content, str) or not content.strip():
            raise RuntimeError("OpenAI MPP response did not contain message content")
        logger.info("GPT summary completed through OpenAI MPP")
        return content.strip()
