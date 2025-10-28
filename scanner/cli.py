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
def scan(
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to YAML config with addresses"),
    interval: float = typer.Option(3.0, help="Seconds between address polls per chain"),
    stop_on_profit: bool = typer.Option(False, help="Stop automatically when profit is found"),
    profit_min_usd: float = typer.Option(0.01, help="Minimum USD value to count as profit"),
    fast: bool = typer.Option(False, help="Shortcut: set interval to 0.3s for faster scanning"),
):
    cfg = load_config(config)
    oracle = PriceOracle()
    if fast:
        interval = min(interval, 0.3)
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
                if bal * price >= profit_min_usd:
                    # Copy best-so-far on each positive detection
                    best = max(ui._profits, key=lambda x: x.value_usd) if ui._profits else None
                    if best:
                        payload = {"chain": best.chain, "address": best.address, "balance": best.balance, "usd": best.value_usd}
                        try:
                            pyperclip.copy(json.dumps(payload))
                        except Exception:
                            pass
                    if stop_on_profit:
                        ui.stop()
                        break
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


@app.command()
def snapshot(
    config: Optional[str] = typer.Option(None, "--config", "-c", help="Path to YAML config with addresses"),
    duration: float = typer.Option(8.0, help="Seconds to scan before capturing"),
    output: str = typer.Option("snapshot", help="Output file prefix (HTML and SVG)"),
    interval: float = typer.Option(2.0, help="Seconds between polls per chain during snapshot run"),
):
    """Run a short scan and save a UI snapshot to HTML/SVG."""
    cfg = load_config(config)
    oracle = PriceOracle()
    ui = ScannerUI()

    def worker(symbol: str, addresses: List[str]):
        adapter = get_adapter(symbol)
        if not adapter:
            return
        price = oracle.get_price_usd(symbol) or 0.0
        start_ts = time.time()
        while time.time() - start_ts < duration and not ui.should_stop():
            price = oracle.get_price_usd(symbol) or price
            for addr in addresses:
                if ui.should_stop() or time.time() - start_ts >= duration:
                    break
                bal = adapter.get_address_balance(addr)
                if bal is None:
                    continue
                ui.record_result(WalletResult(chain=symbol, address=addr, balance=bal, price_usd=price))
            time.sleep(interval)

    threads: List[threading.Thread] = []
    for symbol, chain_cfg in cfg.chains.items():
        if not chain_cfg.addresses:
            continue
        t = threading.Thread(target=worker, args=(symbol, chain_cfg.addresses), daemon=True)
        threads.append(t)
    for t in threads:
        t.start()

    # Use a recording console to export the final render
    rec_console = Console(record=True)
    with Live(ui.render(), console=rec_console, refresh_per_second=6) as live:
        start = time.time()
        while time.time() - start < duration:
            live.update(ui.render())
            time.sleep(0.3)
    ui.stop()
    for t in threads:
        t.join(timeout=1)

    # Print once to the recording console and export artifacts
    rec_console.print(ui.render())
    html_path = f"{output}.html"
    svg_path = f"{output}.svg"
    try:
        rec_console.save_html(html_path, inline_styles=True)
        console.print(f"Saved [bold]{html_path}[/]")
    except Exception:
        console.print("Could not save HTML snapshot")
    try:
        rec_console.save_svg(svg_path)
        console.print(f"Saved [bold]{svg_path}[/]")
    except Exception:
        console.print("Could not save SVG snapshot")
