import os
import sys
import random
import time
from tkinter import Tk, Frame, Label, Button, StringVar, IntVar, BooleanVar, Scale, HORIZONTAL

try:
    import pyperclip  # type: ignore
except Exception:  # pragma: no cover
    pyperclip = None


def format_int_with_spaces(value: int) -> str:
    s = f"{value:,}".replace(",", " ")
    return s


class CryptoPRApp(Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Crypto PR+ — Desktop")
        self.configure(bg="#0e1525")
        self.geometry("460x820")
        self.minsize(420, 720)

        self.wallets_checked = IntVar(value=3830672)
        self.searching = BooleanVar(value=False)
        self.speed = IntVar(value=10)  # 1..10, default to fastest

        self._build_header()
        self._build_counters()
        self._build_profits()
        self._build_chain_grid()
        self._build_controls()
        self._build_bottom_nav()

        # Kick off UI pulse
        self.after(200, self._tick)

    # UI Builders
    def _build_header(self) -> None:
        bar = Frame(self, bg="#111a2e")
        bar.pack(fill="x", pady=(0, 8))
        Label(bar, text="Crypto PR+", fg="#dbe3ff", bg="#111a2e", font=("Inter", 16, "bold")).pack(pady=8)
        Label(bar, text="mini app", fg="#8aa0ff", bg="#111a2e", font=("Inter", 10)).pack(pady=(0, 10))

    def _build_counters(self) -> None:
        block = Frame(self, bg="#0e1525")
        block.pack(fill="x", padx=20, pady=(4, 12))
        Label(block, text="Checked Wallets", fg="#8b97b1", bg="#0e1525", font=("Inter", 16)).pack(anchor="w")
        self.checked_label = Label(
            block,
            text=format_int_with_spaces(self.wallets_checked.get()),
            fg="#6b79ff",
            bg="#0e1525",
            font=("Inter", 48, "bold"),
        )
        self.checked_label.pack(anchor="w", pady=(8, 6))

    def _build_profits(self) -> None:
        container = Frame(self, bg="#0e1525")
        container.pack(fill="x", padx=20, pady=(0, 12))
        Label(container, text="Profits", fg="#dbe3ff", bg="#0e1525", font=("Inter", 22, "bold")).pack(anchor="w", pady=(0, 10))

        # Single profit item (BTC) as a sample
        card = Frame(container, bg="#1a2238", bd=0, highlightthickness=0)
        card.pack(fill="x", pady=(0, 6))
        left_bar = Frame(card, bg="#ff7b1d", width=6, height=64)
        left_bar.pack(side="left", fill="y")

        body = Frame(card, bg="#1a2238")
        body.pack(side="left", fill="both", expand=True, padx=(10, 8), pady=10)

        self.btc_amount = StringVar(value="0,01035 BTC")
        self.btc_usd = StringVar(value="$1122.87")
        self.btc_addr = "pulp parent design secret..."

        Label(body, textvariable=self.btc_amount, fg="#dbe3ff", bg="#1a2238", font=("Inter", 16, "bold")).pack(anchor="w")
        Label(body, textvariable=self.btc_usd, fg="#3bc46b", bg="#1a2238", font=("Inter", 16)).pack(anchor="w")
        Label(body, text=self.btc_addr, fg="#8b97b1", bg="#1a2238", font=("Inter", 12)).pack(anchor="w", pady=(2,0))

        self.copy_btn = Button(card, text="Copy", command=self._copy_btc, bg="#2a3352", fg="#dbe3ff", activebackground="#354169", relief="flat")
        self.copy_btn.pack(side="right", padx=10)

        self.profits_container = container

    def _build_chain_grid(self) -> None:
        wrap = Frame(self, bg="#0e1525")
        wrap.pack(fill="x", padx=20, pady=(6, 10))

        chains = [
            ("BTC", "#ff9900"),
            ("ETH", "#627eea"),
            ("BNB", "#f3ba2f"),
            ("SOL", "#00ffa3"),
            ("AVAX", "#e84142"),
            ("LTC", "#345c9c"),
            ("OP", "#ff0420"),
            ("MATIC", "#8247e5"),
            ("TON", "#50a7f9"),
            ("TRX", "#ff002f"),
        ]

        grid = Frame(wrap, bg="#0e1525")
        grid.pack()

        self.selected_chains = {name: BooleanVar(value=True if name in {"BTC", "ETH", "MATIC"} else False) for name, _ in chains}
        r = c = 0
        for name, color in chains:
            btn = Button(
                grid,
                text=name,
                width=6,
                bg="#1a2238",
                fg=color,
                activebackground="#2a3352",
                relief="flat",
                command=lambda n=name: self._toggle_chain(n),
            )
            btn.grid(row=r, column=c, padx=8, pady=8)
            c += 1
            if c == 4:
                r += 1
                c = 0

    def _build_controls(self) -> None:
        wrap = Frame(self, bg="#0e1525")
        wrap.pack(fill="x", padx=20, pady=(10, 10))

        # Speed slider
        slider_row = Frame(wrap, bg="#0e1525")
        slider_row.pack(fill="x", pady=(0, 10))
        Label(slider_row, text="Search speed", fg="#8b97b1", bg="#0e1525").pack(anchor="w")
        Scale(
            slider_row,
            from_=1,
            to=10,
            orient=HORIZONTAL,
            bg="#0e1525",
            troughcolor="#1a2238",
            highlightthickness=0,
            fg="#dbe3ff",
            variable=self.speed,
        ).pack(fill="x")

        # Start/Stop button
        self.start_button = Button(
            wrap,
            text="Start search",
            command=self._toggle_search,
            bg="#6b79ff",
            fg="#0e1525",
            activebackground="#7d8bff",
            relief="flat",
            height=2,
        )
        self.start_button.pack(fill="x", pady=(6, 0))

    def _build_bottom_nav(self) -> None:
        nav = Frame(self, bg="#0e1525")
        nav.pack(side="bottom", fill="x", pady=(8, 12))
        for label in ("My profile", "Plans", "Support", "FAQ"):
            Button(nav, text=label, bg="#1a2238", fg="#dbe3ff", relief="flat").pack(side="left", expand=True, fill="x", padx=6)

    # Interactions
    def _toggle_chain(self, name: str) -> None:
        var = self.selected_chains[name]
        var.set(not var.get())

    def _toggle_search(self) -> None:
        self.searching.set(not self.searching.get())
        self.start_button.configure(text="Stop" if self.searching.get() else "Start search")

    def _copy_btc(self) -> None:
        text = self.btc_addr
        copied = False
        try:
            if pyperclip is not None:
                pyperclip.copy(text)
                copied = True
        except Exception:
            copied = False
        if not copied:
            try:
                self.clipboard_clear()
                self.clipboard_append(text)
                copied = True
            except Exception:
                copied = False
        # Provide small visual hint by briefly changing the button state
        try:
            self.copy_btn.configure(text="Copied", state="disabled")
            # revert after 1200ms
            self.after(1200, lambda: self.copy_btn.configure(text="Copy", state="normal"))
        except Exception:
            pass

    def _tick(self) -> None:
        # Update counters if searching
        if self.searching.get():
            increment = max(1, int(self.speed.get())) * random.randint(20, 60)
            self.wallets_checked.set(self.wallets_checked.get() + increment)
            self.checked_label.configure(text=format_int_with_spaces(self.wallets_checked.get()))

            # Tiny random walk for the USD value
            usd = float(self.btc_usd.get().replace("$", ""))
            usd += random.uniform(-2.0, 3.0)
            self.btc_usd.set(f"${usd:,.2f}")

        # Schedule next tick based on speed (higher speed => shorter delay)
        delay_ms = int(max(40, 600 - (self.speed.get() * 50)))
        self.after(delay_ms, self._tick)


def main() -> None:
    app = CryptoPRApp()
    app.mainloop()


if __name__ == "__main__":
    main()
