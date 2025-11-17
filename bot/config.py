from dataclasses import dataclass
from os import getenv
from typing import Optional

from dotenv import load_dotenv


@dataclass
class Settings:
    api_base: str
    api_key: Optional[str]
    api_secret: Optional[str]
    private_key: Optional[str]
    telegram_token: Optional[str]
    telegram_chat_id: Optional[str]
    auto_trade: bool
    dry_run: bool
    max_combined_price: float
    min_liquidity: float
    poll_interval: int


def load_settings(auto_trade: bool, dry_run: bool, max_combined_price: float, min_liquidity: float, poll_interval: int) -> Settings:
    load_dotenv()
    return Settings(
        api_base=getenv("POLYMARKET_API_BASE", "https://clob.polymarket.com"),
        api_key=getenv("POLYMARKET_API_KEY"),
        api_secret=getenv("POLYMARKET_API_SECRET"),
        private_key=getenv("PRIVATE_KEY"),
        telegram_token=getenv("TELEGRAM_BOT_TOKEN"),
        telegram_chat_id=getenv("TELEGRAM_CHAT_ID"),
        auto_trade=auto_trade,
        dry_run=dry_run,
        max_combined_price=max_combined_price,
        min_liquidity=min_liquidity,
        poll_interval=poll_interval,
    )
