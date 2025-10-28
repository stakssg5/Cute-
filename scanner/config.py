from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import yaml


@dataclass
class ChainConfig:
    symbol: str
    addresses: List[str]


@dataclass
class AppConfig:
    chains: Dict[str, ChainConfig]
    quote_currency: str = "USD"
    price_source: str = "coingecko"


DEFAULT_CONFIG = {
    "quote_currency": "USD",
    "chains": {
        # Fill with your own addresses; examples are invalid/demo
        "BTC": {"symbol": "BTC", "addresses": []},
        "ETH": {"symbol": "ETH", "addresses": []},
        "BNB": {"symbol": "BNB", "addresses": []},
        "SOL": {"symbol": "SOL", "addresses": []},
        "AVAX": {"symbol": "AVAX", "addresses": []},
        "LTC": {"symbol": "LTC", "addresses": []},
        "OP": {"symbol": "OP", "addresses": []},
        "MATIC": {"symbol": "MATIC", "addresses": []},
        "TON": {"symbol": "TON", "addresses": []},
        "TRX": {"symbol": "TRX", "addresses": []},
    },
}


def load_config(path: Optional[str]) -> AppConfig:
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    else:
        raw = DEFAULT_CONFIG

    chains: Dict[str, ChainConfig] = {}
    for key, cfg in (raw.get("chains") or {}).items():
        symbol = cfg.get("symbol", key)
        addresses = [a.strip() for a in (cfg.get("addresses") or []) if a and a.strip()]
        chains[key.upper()] = ChainConfig(symbol=symbol.upper(), addresses=addresses)

    return AppConfig(
        chains=chains,
        quote_currency=(raw.get("quote_currency") or "USD").upper(),
        price_source=(raw.get("price_source") or "coingecko"),
    )
