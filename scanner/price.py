from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Dict, Optional

import requests


@dataclass
class PriceQuote:
    symbol: str
    price: float
    ts: float


class PriceOracle:
    def __init__(self, cache_seconds: int = 60):
        self.cache_seconds = cache_seconds
        self._cache: Dict[str, PriceQuote] = {}

    def get_price_usd(self, symbol: str) -> Optional[float]:
        symbol = symbol.upper()
        cached = self._cache.get(symbol)
        if cached and time.time() - cached.ts < self.cache_seconds:
            return cached.price
        price = self._fetch_price_usd(symbol)
        if price is not None:
            self._cache[symbol] = PriceQuote(symbol, price, time.time())
        return price

    def _fetch_price_usd(self, symbol: str) -> Optional[float]:
        # Minimal CoinGecko free endpoint
        mapping = {
            "BTC": "bitcoin",
            "ETH": "ethereum",
            "BNB": "binancecoin",
            "SOL": "solana",
            "AVAX": "avalanche-2",
            "LTC": "litecoin",
            "OP": "optimism",
            "MATIC": "matic-network",
            "TON": "the-open-network",
            "TRX": "tron",
        }
        coin = mapping.get(symbol)
        if not coin:
            return None
        try:
            r = requests.get(
                "https://api.coingecko.com/api/v3/simple/price",
                params={"ids": coin, "vs_currencies": "usd"},
                timeout=20,
            )
            r.raise_for_status()
            data = r.json()
            return float(data.get(coin, {}).get("usd"))
        except Exception:
            return None
