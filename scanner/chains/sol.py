from __future__ import annotations

from typing import Optional

import requests

from . import register


@register("SOL")
class Solana:
    symbol = "SOL"

    def get_address_balance(self, address: str) -> Optional[float]:
        try:
            r = requests.post(
                "https://api.mainnet-beta.solana.com",
                json={"jsonrpc": "2.0", "id": 1, "method": "getBalance", "params": [address]},
                timeout=20,
            )
            r.raise_for_status()
            lamports = int(r.json().get("result", {}).get("value", 0))
            return float(lamports) / 1e9
        except Exception:
            return None
