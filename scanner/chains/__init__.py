from __future__ import annotations

from typing import Protocol, Optional


class ChainAdapter(Protocol):
    symbol: str

    def get_address_balance(self, address: str) -> Optional[float]:
        """Return balance in native units for an address, or None on error."""
        ...


# Factory helper
ADAPTERS_REGISTRY = {}


def register(symbol: str):
    def _wrap(cls):
        ADAPTERS_REGISTRY[symbol.upper()] = cls
        return cls

    return _wrap


def get_adapter(symbol: str) -> Optional[ChainAdapter]:
    cls = ADAPTERS_REGISTRY.get(symbol.upper())
    return cls() if cls else None
