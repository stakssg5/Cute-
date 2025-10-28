from __future__ import annotations

from typing import Optional

import requests

from . import register


@register("TRX")
class Tron:
    symbol = "TRX"

    def get_address_balance(self, address: str) -> Optional[float]:
        try:
            r = requests.get(
                f"https://apilist.tronscanapi.com/api/account?address={address}",
                timeout=20,
            )
            r.raise_for_status()
            data = r.json()
            return float(data.get("balance", 0)) / 1_000_000
        except Exception:
            return None
