import logging
from dataclasses import dataclass
from typing import Iterable, List, Optional

from bot.polymarket_client import Market, PolymarketClient
from bot.telegram_notifier import TelegramNotifier
from bot.trader import Trader

logger = logging.getLogger(__name__)


@dataclass
class Opportunity:
    market_id: str
    question: str
    yes_token: Optional[str]
    no_token: Optional[str]
    yes_price: float
    no_price: float
    yes_available: float
    no_available: float
    combined: float
    margin: float


class ArbitrageBot:
    def __init__(
        self,
        client: PolymarketClient,
        trader: Trader,
        notifier: TelegramNotifier,
        max_combined_price: float,
        min_liquidity: float,
        auto_trade: bool,
        dry_run: bool,
    ):
        self.client = client
        self.trader = trader
        self.notifier = notifier
        self.max_combined_price = max_combined_price
        self.min_liquidity = min_liquidity
        self.auto_trade = auto_trade
        self.dry_run = dry_run

    def scan(self) -> List[Opportunity]:
        markets = self.client.fetch_markets()
        return list(self._find_opportunities(markets))

    def _find_opportunities(self, markets: Iterable[Market]) -> Iterable[Opportunity]:
        for market in markets:
            book = market.orderbook
            if book.yes_best_ask is None or book.no_best_ask is None:
                continue
            if book.yes_available < self.min_liquidity or book.no_available < self.min_liquidity:
                continue
            combined = book.yes_best_ask + book.no_best_ask
            if combined >= self.max_combined_price:
                continue
            margin = 1 - combined
            yield Opportunity(
                market_id=market.id,
                question=market.question,
                yes_token=market.yes_token,
                no_token=market.no_token,
                yes_price=book.yes_best_ask,
                no_price=book.no_best_ask,
                yes_available=book.yes_available,
                no_available=book.no_available,
                combined=combined,
                margin=margin,
            )

    def handle_opportunity(self, opportunity: Opportunity) -> None:
        message = (
            f"⚡️ Arbitrage: {opportunity.question}\n"
            f"Yes ask: {opportunity.yes_price:.4f} (liq {opportunity.yes_available:.2f})\n"
            f"No ask: {opportunity.no_price:.4f} (liq {opportunity.no_available:.2f})\n"
            f"Combined: {opportunity.combined:.4f} | Margin: {opportunity.margin:.4f}"
        )
        self.notifier.send_message(message)

        if not self.auto_trade:
            confirmed = self.notifier.prompt_confirmation(opportunity)
            if not confirmed:
                logger.info("Opportunity skipped after manual review")
                return

        if self.dry_run:
            logger.info("Dry run enabled; skipping execution")
            return

        self._execute_bet(opportunity)

    def _execute_bet(self, opportunity: Opportunity) -> None:
        if not opportunity.yes_token or not opportunity.no_token:
            raise ValueError("Missing outcome token ids for trade execution")

        yes_result = self.trader.buy_outcome(opportunity.yes_token, opportunity.yes_price, self.min_liquidity, "buy")
        no_result = self.trader.buy_outcome(opportunity.no_token, opportunity.no_price, self.min_liquidity, "sell")

        summary = (
            f"✅ Trade sent for {opportunity.market_id}\n"
            f"Yes order: {yes_result}\n"
            f"No order: {no_result}"
        )
        self.notifier.send_message(summary)
