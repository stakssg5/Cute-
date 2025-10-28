from __future__ import annotations

from typing import Optional

import requests

from . import register


@register("TON")
class Ton:
    symbol = "TON"

    def get_address_balance(self, address: str) -> Optional[float]:
        try:
            r = requests.get(
                f"https://toncenter.com/api/v2/getAddressBalance?address={address}",
                timeout=20,
            )
            r.raise_for_status()
            data = r.json()
            raw = data.get("result")
            if raw is None:
                return None
            return float(int(str(raw))) / 1e9
        except Exception:
            return None
