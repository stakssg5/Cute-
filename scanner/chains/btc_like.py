from __future__ import annotations

from typing import Optional

import requests

from . import register


class _MempoolSpace:
    def __init__(self, base: str = "https://mempool.space/api"):
        self.base = base.rstrip("/")

    def get_balance(self, address: str) -> Optional[float]:
        try:
            r = requests.get(f"{self.base}/address/{address}", timeout=20)
            r.raise_for_status()
            data = r.json()
            funded = int(data.get("chain_stats", {}).get("funded_txo_sum", 0))
            spent = int(data.get("chain_stats", {}).get("spent_txo_sum", 0))
            sat = funded - spent
            return float(sat) / 1e8
        except Exception:
            return None


@register("BTC")
class Bitcoin:
    symbol = "BTC"

    def get_address_balance(self, address: str) -> Optional[float]:
        return _MempoolSpace().get_balance(address)


class _SoChain:
    def __init__(self, network: str):
            self.network = network

    def get_balance(self, address: str) -> Optional[float]:
        try:
            r = requests.get(f"https://sochain.com/api/v2/get_address_balance/{self.network}/{address}", timeout=20)
            r.raise_for_status()
            data = r.json().get("data", {})
            return float(data.get("confirmed_balance", 0.0))
        except Exception:
            return None


@register("LTC")
class Litecoin:
    symbol = "LTC"

    def get_address_balance(self, address: str) -> Optional[float]:
        return _SoChain("LTC").get_balance(address)
