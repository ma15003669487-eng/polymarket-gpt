import logging
from dataclasses import dataclass
from typing import Dict, Optional

from eth_account import Account
from eth_account.signers.local import LocalAccount

from bot.polymarket_client import PolymarketClient

logger = logging.getLogger(__name__)


@dataclass
class Wallet:
    private_key: str
    address: str


class Trader:
    def __init__(self, client: PolymarketClient, private_key: Optional[str]):
        self.client = client
        self.wallet = self._load_wallet(private_key)

    def _load_wallet(self, private_key: Optional[str]) -> Wallet:
        if private_key:
            account: LocalAccount = Account.from_key(private_key)
            return Wallet(private_key=private_key, address=account.address)
        account: LocalAccount = Account.create()
        logger.warning("Generated new private key: %s", account.key.hex())
        return Wallet(private_key=account.key.hex(), address=account.address)

    def buy_outcome(self, token_id: str, price: float, size: float, side: str) -> Dict[str, str]:
        logger.info("Placing %s order: token=%s price=%.4f size=%.4f", side, token_id, price, size)
        return self.client.place_order(token_id=token_id, price=price, size=size, side=side, wallet_address=self.wallet.address)
