import hashlib
import hmac
import json
import time
from dataclasses import dataclass
from typing import Dict, List, Optional

import requests


@dataclass
class OrderBook:
    yes_best_ask: Optional[float]
    no_best_ask: Optional[float]
    yes_available: float
    no_available: float


@dataclass
class Market:
    id: str
    question: str
    yes_token: Optional[str]
    no_token: Optional[str]
    orderbook: OrderBook


class PolymarketClient:
    def __init__(self, api_base: str, api_key: Optional[str] = None, api_secret: Optional[str] = None):
        self.api_base = api_base.rstrip("/")
        self.api_key = api_key
        self.api_secret = api_secret

    def fetch_markets(self, limit: int = 200, offset: int = 0, active: bool = True) -> List[Market]:
        params = {"limit": limit, "offset": offset}
        if active is not None:
            params["active"] = str(active).lower()

        response = requests.get(f"{self.api_base}/markets", params=params, timeout=15)
        response.raise_for_status()
        payload = response.json()
        return self._parse_markets(payload)

    def fetch_all_markets(self, page_size: int = 200, active: bool = True) -> List[Market]:
        markets: List[Market] = []
        offset = 0

        while True:
            batch = self.fetch_markets(limit=page_size, offset=offset, active=active)
            if not batch:
                break
            markets.extend(batch)
            offset += page_size
            if len(batch) < page_size:
                break

        return markets

    def _parse_markets(self, payload: Dict[str, object]) -> List[Market]:
        markets: List[Market] = []
        for raw in payload.get("markets", payload):
            yes_token, no_token = self._outcome_tokens(raw)
            orderbook = self._parse_orderbook(raw)
            markets.append(
                Market(
                    id=raw.get("id") or raw.get("slug", "unknown"),
                    question=raw.get("question") or raw.get("title", ""),
                    yes_token=yes_token,
                    no_token=no_token,
                    orderbook=orderbook,
                )
            )
        return markets

    def place_order(self, token_id: str, price: float, size: float, side: str, wallet_address: str) -> Dict[str, str]:
        if not self.api_key or not self.api_secret:
            raise ValueError("API key/secret required for trading")
        timestamp = int(time.time() * 1000)
        payload = {
            "token_id": token_id,
            "price": price,
            "size": size,
            "side": side,
            "wallet_address": wallet_address,
            "timestamp": timestamp,
        }
        signature = self._sign_payload(payload)
        headers = {
            "X-API-KEY": self.api_key,
            "X-SIGNATURE": signature,
            "Content-Type": "application/json",
        }
        response = requests.post(f"{self.api_base}/orders", headers=headers, data=json.dumps(payload), timeout=15)
        response.raise_for_status()
        return response.json()

    def _sign_payload(self, payload: Dict[str, object]) -> str:
        message = json.dumps(payload, separators=(",", ":"), sort_keys=True)
        digest = hmac.new(self.api_secret.encode(), msg=message.encode(), digestmod=hashlib.sha256)
        return digest.hexdigest()

    def _outcome_tokens(self, raw: Dict[str, object]) -> (Optional[str], Optional[str]):
        tokens = raw.get("tokens") or raw.get("outcomes") or []
        yes_token = None
        no_token = None
        for token in tokens:
            outcome = token.get("outcome") or token.get("name") or ""
            if outcome.lower().startswith("yes"):
                yes_token = token.get("id") or token.get("token_id")
            if outcome.lower().startswith("no"):
                no_token = token.get("id") or token.get("token_id")
        return yes_token, no_token

    def _parse_orderbook(self, raw: Dict[str, object]) -> OrderBook:
        yes_best_ask = None
        no_best_ask = None
        yes_available = 0.0
        no_available = 0.0
        tokens = raw.get("tokens") or raw.get("outcomes") or []
        for token in tokens:
            outcome = token.get("outcome") or token.get("name") or ""
            best_ask = token.get("best_ask") or token.get("bestAsk") or token.get("bestAskPrice")
            available = token.get("available") or token.get("availableLiquidity") or token.get("liquidity") or 0
            if best_ask is not None:
                best_ask = float(best_ask)
            available = float(available or 0)
            if outcome.lower().startswith("yes"):
                yes_best_ask = best_ask
                yes_available = available
            if outcome.lower().startswith("no"):
                no_best_ask = best_ask
                no_available = available
        return OrderBook(
            yes_best_ask=yes_best_ask,
            no_best_ask=no_best_ask,
            yes_available=yes_available,
            no_available=no_available,
        )
