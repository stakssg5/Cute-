from __future__ import annotations

from typing import Optional

import requests

from . import register


@register("AVAX")
class Avalanche:
    symbol = "AVAX"

    def get_address_balance(self, address: str) -> Optional[float]:
        # C-Chain (EVM) via blockscout style
        try:
            r = requests.get(
                "https://avalanche.blockscout.com/api",
                params={"module": "account", "action": "balance", "address": address},
                timeout=20,
            )
            r.raise_for_status()
            data = r.json()
            raw = data.get("result")
            if raw is None:
                return None
            return float(int(str(raw)) / 10**18)
        except Exception:
            return None
