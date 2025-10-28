from __future__ import annotations

from typing import Optional

import requests

from . import register


class _SimpleExplorer:
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")

    def get_native_balance(self, address: str, field: str = "result", path: str = "api") -> Optional[float]:
        try:
            r = requests.get(f"{self.base_url}/{path}", params={"module": "account", "action": "balance", "address": address}, timeout=20)
            r.raise_for_status()
            data = r.json()
            raw = data.get(field)
            if raw is None:
                return None
            # value is wei-like integer string; convert to ether-like 18 decimals
            value = int(str(raw)) / 10**18
            return float(value)
        except Exception:
            return None


@register("ETH")
class Ethereum:
    symbol = "ETH"

    def get_address_balance(self, address: str) -> Optional[float]:
        # Using a public fallback explorer (Blockscout-like) with rate limits
        # Users should swap to own API key services for reliability.
        explorer = _SimpleExplorer("https://eth.blockscout.com")
        return explorer.get_native_balance(address, field="result")


@register("BNB")
class BnbSmartChain:
    symbol = "BNB"

    def get_address_balance(self, address: str) -> Optional[float]:
        explorer = _SimpleExplorer("https://bsc.blockscout.com")
        return explorer.get_native_balance(address)


@register("OP")
class Optimism:
    symbol = "OP"

    def get_address_balance(self, address: str) -> Optional[float]:
        explorer = _SimpleExplorer("https://optimism.blockscout.com")
        return explorer.get_native_balance(address)


@register("MATIC")
class Polygon:
    symbol = "MATIC"

    def get_address_balance(self, address: str) -> Optional[float]:
        explorer = _SimpleExplorer("https://polygon.blockscout.com")
        return explorer.get_native_balance(address)
