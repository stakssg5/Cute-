from __future__ import annotations

import json
import threading
import time
from typing import List, Optional

import pyperclip
import typer
from rich.console import Console
from rich.live import Live

from .config import load_config
from .price import PriceOracle
from .chains import get_adapter
from .ui import ScannerUI, WalletResult

app = typer.Typer(add_completion=False, help="Multi-chain wallet scanner (balances only).")
console = Console()


@app.command()
def scan(config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to YAML config with addresses"), interval: float = typer.Option(3.0, help="Seconds between address polls per chain")):
    cfg = load_config(config)
    oracle = PriceOracle()
    ui = ScannerUI()

    def worker(symbol: str, addresses: List[str]):
        adapter = get_adapter(symbol)
        if not adapter:
            return
        while not ui.should_stop():
            price = oracle.get_price_usd(symbol) or 0.0
            for addr in addresses:
                if ui.should_stop():
                    break
                bal = adapter.get_address_balance(addr)
                if bal is None:
                    continue
                ui.record_result(WalletResult(chain=symbol, address=addr, balance=bal, price_usd=price))
                if bal * price > 0:
                    # Copy best-so-far on each positive detection
                    best = max(ui._profits, key=lambda x: x.value_usd) if ui._profits else None
                    if best:
                        payload = {"chain": best.chain, "address": best.address, "balance": best.balance, "usd": best.value_usd}
                        try:
                            pyperclip.copy(json.dumps(payload))
                        except Exception:
                            pass
            time.sleep(interval)

    threads: List[threading.Thread] = []
    for symbol, chain_cfg in cfg.chains.items():
        if not chain_cfg.addresses:
            continue
        t = threading.Thread(target=worker, args=(symbol, chain_cfg.addresses), daemon=True)
        threads.append(t)

    for t in threads:
        t.start()

    console.print("Press Ctrl+C to stop.")
    try:
        with Live(ui.render(), refresh_per_second=6) as live:
            while True:
                live.update(ui.render())
                time.sleep(0.5)
                if ui.should_stop():
                    break
    except KeyboardInterrupt:
        pass
    finally:
        ui.stop()
        for t in threads:
            t.join(timeout=1)


if __name__ == "__main__":
    app()  # pragma: no cover
