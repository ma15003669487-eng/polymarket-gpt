import logging
from typing import Optional

import requests

from bot.arbitrage import Opportunity

logger = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, token: Optional[str], chat_id: Optional[str]):
        self.token = token
        self.chat_id = chat_id

    def send_message(self, text: str) -> None:
        logger.info("Telegram message: %s", text)
        if not self.token or not self.chat_id:
            return
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        payload = {"chat_id": self.chat_id, "text": text}
        requests.post(url, json=payload, timeout=10)

    def prompt_confirmation(self, opportunity: Opportunity) -> bool:
        prompt = input(
            f"Execute arbitrage for {opportunity.market_id}? Combined {opportunity.combined:.4f} (y/n): "
        ).strip()
        return prompt.lower() in {"y", "yes"}
