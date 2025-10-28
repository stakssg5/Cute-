from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from rich.align import Align
from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table


console = Console()


@dataclass
class WalletResult:
    chain: str
    address: str
    balance: float
    price_usd: float

    @property
    def value_usd(self) -> float:
        return self.balance * self.price_usd


class ScannerUI:
    def __init__(self) -> None:
        self._stop_event = threading.Event()
        self._latest_results: List[WalletResult] = []
        self._checked_count: int = 0
        self._profits: List[WalletResult] = []

    def stop(self) -> None:
        self._stop_event.set()

    def should_stop(self) -> bool:
        return self._stop_event.is_set()

    def record_result(self, result: WalletResult) -> None:
        self._checked_count += 1
        self._latest_results.append(result)
        if result.value_usd > 0:
            self._profits.append(result)

    def render(self) -> Panel:
        header = f"Checked Wallets: [bold violet]{self._checked_count}[/]"

        table = Table(expand=True)
        table.add_column("Chain", no_wrap=True)
        table.add_column("Address")
        table.add_column("Balance", justify="right")
        table.add_column("Price USD", justify="right")
        table.add_column("Value USD", justify="right")

        for r in self._latest_results[-10:]:
            table.add_row(r.chain, r.address[:10] + "...", f"{r.balance:.8f}", f"${r.price_usd:,.2f}", f"${r.value_usd:,.2f}")

        profit_panel = None
        if self._profits:
            best = max(self._profits, key=lambda x: x.value_usd)
            profit_panel = Panel(
                f"[bold green]Profit found![/] {best.chain} {best.balance:.8f} ≈ [bold]${best.value_usd:,.2f}[/]\n{best.address}",
                border_style="green",
            )

        body = Group(
            Align.left(header),
            table,
            profit_panel or Panel("No profits yet", border_style="gray"),
        )
        return Panel(body, title="Wallet Scanner", border_style="purple")
