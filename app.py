import argparse
import logging
import time

from bot.arbitrage import ArbitrageBot
from bot.config import load_settings
from bot.polymarket_client import PolymarketClient
from bot.telegram_notifier import TelegramNotifier
from bot.trader import Trader

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Polymarket arbitrage bot")
    parser.add_argument("--auto", dest="auto", action="store_true", help="Enable automatic execution")
    parser.add_argument("--no-auto", dest="auto", action="store_false", help="Disable automatic execution")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", help="Do not place real orders")
    parser.add_argument("--poll-interval", type=int, default=60, help="Seconds between scans")
    parser.add_argument(
        "--max-combined", type=float, default=0.99, help="Maximum combined yes+no ask to qualify as arbitrage"
    )
    parser.add_argument(
        "--min-liquidity", type=float, default=10.0, help="Minimum available size on each side before trading"
    )
    parser.set_defaults(auto=False, dry_run=True)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    settings = load_settings(
        auto_trade=args.auto,
        dry_run=args.dry_run,
        max_combined_price=args.max_combined,
        min_liquidity=args.min_liquidity,
        poll_interval=args.poll_interval,
    )

    client = PolymarketClient(settings.api_base, settings.api_key, settings.api_secret)
    notifier = TelegramNotifier(settings.telegram_token, settings.telegram_chat_id)
    trader = Trader(client, settings.private_key)

    bot = ArbitrageBot(
        client=client,
        trader=trader,
        notifier=notifier,
        max_combined_price=settings.max_combined_price,
        min_liquidity=settings.min_liquidity,
        auto_trade=settings.auto_trade,
        dry_run=settings.dry_run,
    )

    logger.info("Starting scan loop (auto=%s dry_run=%s)", settings.auto_trade, settings.dry_run)
    while True:
        try:
            opportunities = bot.scan()
            if not opportunities:
                logger.info("No arbitrage found")
            for opp in opportunities:
                bot.handle_opportunity(opp)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Error during scan: %s", exc)
        time.sleep(settings.poll_interval)


if __name__ == "__main__":
    main()
