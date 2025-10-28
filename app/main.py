import os
import sys
import re
import time
import threading
from datetime import datetime
from typing import Optional, Tuple, Dict

try:
    # Pillow is required for screenshots and image loading
    from PIL import Image, ImageTk, ImageGrab, ImageOps, ImageFilter
except Exception as exc:  # pragma: no cover - helpful runtime message
    print("Pillow is required. Install with: pip install Pillow", file=sys.stderr)
    raise

# pytesseract is optional at runtime (requires Tesseract OCR binary)
try:
    import pytesseract  # type: ignore
    TESSERACT_AVAILABLE = True
except Exception:
    pytesseract = None  # type: ignore
    TESSERACT_AVAILABLE = False

import tkinter as tk
from tkinter import ttk, filedialog, messagebox

APP_TITLE = "Wallet Screenshot Helper"
CAPTURE_DIR = os.path.join(os.path.expanduser("~"), "Pictures", "wallet_captures")

# ---- Optional crypto libs (for mnemonic + balances) ----
try:
    from bip_utils import (
        Bip39MnemonicValidator,
        Bip39SeedGenerator,
        Bip44,
        Bip44Coins,
        Bip44Changes,
    )
    BIPUTILS_AVAILABLE = True
except Exception:
    BIPUTILS_AVAILABLE = False

try:
    import requests  # type: ignore
    REQUESTS_AVAILABLE = True
except Exception:
    REQUESTS_AVAILABLE = False

# Attempt to auto-configure Tesseract path on Windows if module is present
if TESSERACT_AVAILABLE:
    try:
        from tesseract_helper import find_tesseract_path  # type: ignore

        _tpath = find_tesseract_path()
        if _tpath:
            pytesseract.pytesseract.tesseract_cmd = _tpath  # type: ignore
    except Exception:
        pass


def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def normalize_text_for_profit(text: str) -> str:
    """Best-effort normalization of OCR text to a 'profit' string.

    Strategy:
    - Extract the first money-like amount with optional currency symbol (e.g., $1,234.56)
    - Or extract a crypto amount followed by ticker (e.g., 0.01035 BTC)
    - Prefer USD amount if present; otherwise fall back to crypto amount
    - Convert decimal commas to dots
    """
    if not text:
        return ""

    # Standardize decimal comma to dot for easier matching
    standardized = text.replace("\n", " ")
    standardized = re.sub(r"\s+", " ", standardized)
    standardized = standardized.replace(",", ".")

    usd_match = re.search(r"\$\s?([0-9]{1,3}(?:\.[0-9]{3})*|[0-9]+)(?:\.[0-9]{2})?", standardized)
    if usd_match:
        # Return with leading $ and normalized separators
        amount = usd_match.group(0)
        # Remove thousands separators if any mistakenly turned into dots
        amount = re.sub(r"(?<=\d)\.(?=\d{3}(?:\D|$))", "", amount)
        return amount

    # Crypto amount like 0.01035 BTC or 1.23 ETH
    crypto_match = re.search(r"([0-9]+(?:\.[0-9]+)?)\s*([A-Za-z]{3,5})", standardized)
    if crypto_match:
        number = crypto_match.group(1)
        ticker = crypto_match.group(2).upper()
        return f"{number} {ticker}"

    # If nothing matched, return a cleaned excerpt
    return standardized.strip()[:64]


class ScreenshotState:
    def __init__(self) -> None:
        self.last_image: Optional[Image.Image] = None
        self.last_path: Optional[str] = None
        self.last_text: str = ""


class WalletScreenshotApp(ttk.Frame):
    def __init__(self, master: tk.Tk) -> None:
        super().__init__(master, padding=16)
        self.master = master
        self.state = ScreenshotState()
        self.selection_overlay: Optional[SelectionOverlay] = None
        self.keyword_var = tk.StringVar(value="")
        self.interval_var = tk.StringVar(value="1000")  # ms
        self.is_live: bool = False
        self.live_bbox: Optional[Tuple[int, int, int, int]] = None

        master.title(APP_TITLE)
        master.minsize(520, 420)
        master.protocol("WM_DELETE_WINDOW", self.on_quit)

        self._build_styles()
        self._build_ui()
        self._update_controls()

    def _build_styles(self) -> None:
        style = ttk.Style()
        # Use built-in themes if available
        try:
            style.theme_use("clam")
        except Exception:
            pass
        style.configure("TFrame", background="#0f1220")
        style.configure("TLabel", background="#0f1220", foreground="#e5e7eb")
        style.configure("Header.TLabel", font=("SF Pro Display", 16, "bold"))
        style.configure("Result.TLabel", foreground="#a78bfa", font=("SF Pro Display", 12))
        style.configure("TButton", padding=(10, 6))

    def _build_ui(self) -> None:
        # Header
        header = ttk.Label(self, text="Screenshot + Profit Copy", style="Header.TLabel")
        header.grid(row=0, column=0, columnspan=7, sticky="w", pady=(0, 8))

        # Buttons row
        self.btn_select = ttk.Button(self, text="Select area", command=self._start_selection)
        self.btn_open = ttk.Button(self, text="Open image…", command=self._open_image)
        self.btn_save = ttk.Button(self, text="Save screenshot", command=self._save_last)
        self.btn_copy = ttk.Button(self, text="Copy profit", command=self._copy_profit)
        self.btn_live = ttk.Button(self, text="Start live", command=self._toggle_live)

        self.btn_select.grid(row=1, column=0, sticky="ew", padx=(0, 8))
        self.btn_open.grid(row=1, column=1, sticky="ew", padx=(0, 8))
        self.btn_save.grid(row=1, column=2, sticky="ew", padx=(0, 8))
        self.btn_copy.grid(row=1, column=3, sticky="ew")
        
        ttk.Label(self, text="Interval ms:").grid(row=1, column=4, sticky="e", padx=(16, 4))
        self.entry_interval = ttk.Entry(self, width=8, textvariable=self.interval_var)
        self.entry_interval.grid(row=1, column=5, sticky="w")
        self.btn_live.grid(row=1, column=6, sticky="ew", padx=(8, 0))

        self.columnconfigure(0, weight=1)
        self.columnconfigure(1, weight=1)
        self.columnconfigure(2, weight=1)
        self.columnconfigure(3, weight=1)
        self.columnconfigure(4, weight=0)
        self.columnconfigure(5, weight=0)
        self.columnconfigure(6, weight=0)

        # Preview canvas
        self.preview_label = ttk.Label(self, text="No screenshot yet")
        self.preview_label.grid(row=2, column=0, columnspan=7, sticky="nsew", pady=(16, 8))
        self.rowconfigure(2, weight=1)

        # OCR result
        self.result_var = tk.StringVar(value="")
        self.result_label = ttk.Label(self, textvariable=self.result_var, style="Result.TLabel")
        self.result_label.grid(row=3, column=0, columnspan=7, sticky="w", pady=(8, 0))

        # Keyword filter row
        ttk.Label(self, text="Find word:").grid(row=4, column=0, sticky="w", pady=(8, 4))
        self.entry_keyword = ttk.Entry(self, textvariable=self.keyword_var)
        self.entry_keyword.grid(row=4, column=1, columnspan=3, sticky="ew", pady=(8, 4))
        self.btn_find = ttk.Button(self, text="Find", command=self._update_matches)
        self.btn_find.grid(row=4, column=4, sticky="ew", padx=(8, 8), pady=(8, 4))
        self.btn_copy_match = ttk.Button(self, text="Copy match", command=self._copy_selected_match)
        self.btn_copy_match.grid(row=4, column=5, sticky="ew", pady=(8, 4))

        # Matches list
        self.matches_list = tk.Listbox(self, height=5)
        self.matches_list.grid(row=5, column=0, columnspan=7, sticky="nsew")
        self.rowconfigure(5, weight=1)
        self.entry_keyword.bind("<Return>", lambda _e: self._update_matches())
        self.entry_keyword.bind("<KeyRelease>", lambda _e: self._update_matches())

        # Mnemonic detection + balances
        self.mnemonic_var = tk.StringVar(value="")
        self.mnemonic_label = ttk.Label(self, textvariable=self.mnemonic_var)
        self.mnemonic_label.grid(row=6, column=0, columnspan=7, sticky="w", pady=(8, 0))

        self.balance_var = tk.StringVar(value="")
        self.balance_label = ttk.Label(self, textvariable=self.balance_var)
        self.balance_label.grid(row=7, column=0, columnspan=7, sticky="w", pady=(4, 0))

        # Footer
        self.footer = ttk.Label(
            self,
            text=(
                "Tip: Use Select area on the profits card, then Copy profit. "
                + ("(Tesseract not detected)" if not TESSERACT_AVAILABLE else "")
            ),
        )
        self.footer.grid(row=8, column=0, columnspan=7, sticky="w", pady=(12, 0))

        self.pack(fill="both", expand=True)

    def _update_controls(self) -> None:
        has_image = self.state.last_image is not None
        self.btn_save.configure(state=("normal" if has_image else "disabled"))
        self.btn_copy.configure(state=("normal" if has_image else "disabled"))

    def _start_selection(self) -> None:
        # Hide the main window while selecting to avoid capturing it
        self.master.withdraw()
        self.selection_overlay = SelectionOverlay(
            on_capture=self._on_area_captured,
            on_cancel=self._on_selection_cancel,
        )
        self.selection_overlay.show()

    def _on_selection_cancel(self) -> None:
        self.master.deiconify()

    def _on_area_captured(self, img: Image.Image, bbox: Tuple[int, int, int, int]) -> None:
        # Optional preprocess for better OCR contrast
        processed = ImageOps.grayscale(img)
        processed = processed.filter(ImageFilter.MedianFilter(size=3))
        self.state.last_image = processed
        self.state.last_path = None
        self.live_bbox = bbox
        self._set_preview(processed)
        self._try_ocr(processed)
        self.master.deiconify()
        self._update_controls()

    def _set_preview(self, img: Image.Image) -> None:
        max_w, max_h = 800, 360
        preview = img.copy()
        preview.thumbnail((max_w, max_h), Image.Resampling.LANCZOS)
        self._tk_preview = ImageTk.PhotoImage(preview)
        self.preview_label.configure(image=self._tk_preview, text="")

    def _open_image(self) -> None:
        filetypes = [
            ("Image files", "*.png *.jpg *.jpeg *.webp *.bmp"),
            ("All files", "*.*"),
        ]
        path = filedialog.askopenfilename(title="Open image", filetypes=filetypes)
        if not path:
            return
        try:
            img = Image.open(path)
        except Exception as exc:
            messagebox.showerror("Open image failed", str(exc))
            return
        self.state.last_image = img
        self.state.last_path = path
        self._set_preview(img)
        self._try_ocr(img)
        self._update_controls()

    def _save_last(self) -> None:
        if not self.state.last_image:
            return
        ensure_dir(CAPTURE_DIR)
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_name = f"capture_{ts}.png"
        path = filedialog.asksaveasfilename(
            title="Save screenshot",
            initialdir=CAPTURE_DIR,
            initialfile=default_name,
            defaultextension=".png",
            filetypes=[("PNG image", ".png")],
        )
        if not path:
            return
        try:
            self.state.last_image.save(path, format="PNG")
        except Exception as exc:
            messagebox.showerror("Save failed", str(exc))
            return
        self.state.last_path = path
        messagebox.showinfo("Saved", f"Saved to\n{path}")

    def _try_ocr(self, img: Image.Image) -> None:
        if not TESSERACT_AVAILABLE:
            self.result_var.set("OCR unavailable (install Tesseract). You can still save screenshot.")
            return
        try:
            # Some UIs use light-on-dark; invert to help OCR if average is dark
            grayscale = ImageOps.grayscale(img)
            avg = sum(grayscale.getdata()) / (grayscale.width * grayscale.height)
            ocr_img = ImageOps.invert(grayscale) if avg < 96 else grayscale
            text = pytesseract.image_to_string(ocr_img, config="--psm 6")  # type: ignore
        except Exception as exc:
            self.result_var.set(f"OCR failed: {exc}")
            return
        self.state.last_text = text
        profit = normalize_text_for_profit(text)
        if profit:
            self.result_var.set(f"Detected: {profit}")
        else:
            self.result_var.set("No profit text detected. Try selecting tighter around the number.")
        # Update keyword matches after OCR completes
        self._update_matches()
        # Attempt mnemonic detection and, if possible, check balances
        self._detect_mnemonic_and_maybe_fetch()

    def _copy_profit(self) -> None:
        if not self.state.last_image:
            return
        if not self.state.last_text and TESSERACT_AVAILABLE:
            self._try_ocr(self.state.last_image)
        profit = normalize_text_for_profit(self.state.last_text)
        if not profit:
            profit = ""
        try:
            # Use Tk clipboard for portability
            self.master.clipboard_clear()
            self.master.clipboard_append(profit)
            self.master.update()  # keep it after window closes
        except Exception as exc:
            messagebox.showerror("Clipboard error", str(exc))
            return
        self.result_var.set(f"Copied: {profit if profit else '[empty]'}")

    def on_quit(self) -> None:
        self.master.destroy()

    # --- Keyword filtering helpers ---
    def _update_matches(self) -> None:
        """Update the matches list with lines from OCR text containing the keyword."""
        keyword = (self.keyword_var.get() or "").strip()
        self.matches_list.delete(0, tk.END)
        if not self.state.last_text:
            return
        lines = [ln.strip() for ln in self.state.last_text.splitlines() if ln.strip()]
        if not keyword:
            return
        keyword_lower = keyword.lower()
        for ln in lines:
            if keyword_lower in ln.lower():
                self.matches_list.insert(tk.END, ln)

    def _copy_selected_match(self) -> None:
        selection = self.matches_list.curselection()
        if not selection:
            messagebox.showinfo("Copy match", "No match selected.")
            return
        value = self.matches_list.get(selection[0])
        try:
            self.master.clipboard_clear()
            self.master.clipboard_append(value)
            self.master.update()
        except Exception as exc:
            messagebox.showerror("Clipboard error", str(exc))
            return
        self.result_var.set(f"Copied match: {value[:48]}{'…' if len(value) > 48 else ''}")

    # --- Live capture ---
    def _toggle_live(self) -> None:
        if self.is_live:
            self.is_live = False
            self.btn_live.configure(text="Start live")
            return
        if not self.live_bbox:
            messagebox.showinfo("Live", "Select an area first.")
            return
        self.is_live = True
        self.btn_live.configure(text="Stop live")
        self._schedule_next_live()

    def _schedule_next_live(self) -> None:
        if not self.is_live:
            return
        try:
            interval_ms = max(200, int(self.interval_var.get().strip() or "1000"))
        except Exception:
            interval_ms = 1000
        self.after(interval_ms, self._live_tick)

    def _live_tick(self) -> None:
        if not self.is_live or not self.live_bbox:
            return
        try:
            img = ImageGrab.grab(bbox=self.live_bbox)
        except Exception as exc:
            self.is_live = False
            self.btn_live.configure(text="Start live")
            messagebox.showerror("Live capture failed", str(exc))
            return
        processed = ImageOps.grayscale(img)
        processed = processed.filter(ImageFilter.MedianFilter(size=3))
        self.state.last_image = processed
        self.state.last_path = None
        self._set_preview(processed)
        self._try_ocr(processed)
        self._schedule_next_live()

    # --- Mnemonic + balance detection ---
    def _detect_mnemonic_and_maybe_fetch(self) -> None:
        if not BIPUTILS_AVAILABLE:
            self.mnemonic_var.set("Mnemonic detection unavailable (install bip-utils).")
            return
        text = (self.state.last_text or "").lower()
        tokens = re.findall(r"[a-z]+", text)
        detected: Optional[str] = None
        for i in range(0, max(0, len(tokens) - 11)):
            candidate = " ".join(tokens[i : i + 12])
            try:
                if Bip39MnemonicValidator(candidate).Validate():
                    detected = candidate
                    break
            except Exception:
                continue
        if not detected:
            self.mnemonic_var.set("")
            self.balance_var.set("")
            return
        masked = self._mask_mnemonic(detected)
        self.mnemonic_var.set(f"12-word phrase detected: {masked}")
        # Fetch balances in background
        if REQUESTS_AVAILABLE:
            threading.Thread(target=self._fetch_balances_thread, args=(detected,), daemon=True).start()
        else:
            self.balance_var.set("Install requests to check balances.")

    def _mask_mnemonic(self, mnemonic: str) -> str:
        parts = mnemonic.split()
        if len(parts) != 12:
            return mnemonic
        # mask middle words
        masked = [parts[0], parts[1]] + ["•••"] * 8 + [parts[-2], parts[-1]]
        return " ".join(masked)

    def _fetch_balances_thread(self, mnemonic: str) -> None:
        addresses = self._derive_addresses(mnemonic)
        balances: Dict[str, str] = {}
        if "BTC" in addresses:
            try:
                balances["BTC"] = self._get_btc_balance(addresses["BTC"]) or "?"
            except Exception:
                balances["BTC"] = "error"
        if "ETH" in addresses:
            try:
                balances["ETH"] = self._get_eth_balance(addresses["ETH"]) or "?"
            except Exception:
                balances["ETH"] = "error"

        def update_label() -> None:
            lines = []
            if "BTC" in addresses:
                lines.append(f"BTC {addresses['BTC']}: {balances.get('BTC', '?')}")
            if "ETH" in addresses:
                lines.append(f"ETH {addresses['ETH']}: {balances.get('ETH', '?')}")
            self.balance_var.set("\n".join(lines))

        self.master.after(0, update_label)

    def _derive_addresses(self, mnemonic: str) -> Dict[str, str]:
        res: Dict[str, str] = {}
        try:
            seed = Bip39SeedGenerator(mnemonic).Generate()
            # BTC m/44'/0'/0'/0/0
            btc_ctx = (
                Bip44.FromSeed(seed, Bip44Coins.BITCOIN)
                .Purpose()
                .Coin()
                .Account(0)
                .Change(Bip44Changes.CHAIN_EXT)
                .AddressIndex(0)
            )
            res["BTC"] = btc_ctx.PublicKey().ToAddress()
        except Exception:
            pass
        try:
            eth_ctx = (
                Bip44.FromSeed(seed, Bip44Coins.ETHEREUM)
                .Purpose()
                .Coin()
                .Account(0)
                .Change(Bip44Changes.CHAIN_EXT)
                .AddressIndex(0)
            )
            res["ETH"] = eth_ctx.PublicKey().ToAddress()
        except Exception:
            pass
        return res

    def _get_eth_balance(self, address: str) -> Optional[str]:
        # Cloudflare public RPC
        url = "https://cloudflare-eth.com"
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "eth_getBalance",
            "params": [address, "latest"],
        }
        r = requests.post(url, json=payload, timeout=10)
        r.raise_for_status()
        data = r.json()
        if "result" not in data:
            return None
        wei = int(data["result"], 16)
        eth = wei / 10**18
        return f"{eth:.6f} ETH"

    def _get_btc_balance(self, address: str) -> Optional[str]:
        # Blockstream API
        r = requests.get(f"https://blockstream.info/api/address/{address}", timeout=10)
        r.raise_for_status()
        data = r.json()
        chain = data.get("chain_stats", {})
        mempool = data.get("mempool_stats", {})
        funded = int(chain.get("funded_txo_sum", 0)) + int(mempool.get("funded_txo_sum", 0))
        spent = int(chain.get("spent_txo_sum", 0)) + int(mempool.get("spent_txo_sum", 0))
        sats = funded - spent
        btc = sats / 10**8
        return f"{btc:.8f} BTC"


class SelectionOverlay:
    """Full-screen semi-transparent overlay for selecting a rectangular area."""

    def __init__(self, on_capture, on_cancel) -> None:
        self.on_capture = on_capture
        self.on_cancel = on_cancel
        self.overlay = tk.Toplevel()
        self.overlay.withdraw()
        self.overlay.attributes("-fullscreen", True)
        # Make click-through disabled: we want to receive events
        self.overlay.attributes("-alpha", 0.25)
        self.overlay.configure(bg="black")
        self.overlay.bind("<Escape>", self._cancel)

        self.canvas = tk.Canvas(self.overlay, cursor="cross", highlightthickness=0, bg="black")
        self.canvas.pack(fill="both", expand=True)

        self.start_x: Optional[int] = None
        self.start_y: Optional[int] = None
        self.rect_id: Optional[int] = None

        self.canvas.bind("<ButtonPress-1>", self._on_press)
        self.canvas.bind("<B1-Motion>", self._on_motion)
        self.canvas.bind("<ButtonRelease-1>", self._on_release)

    def show(self) -> None:
        # Bring overlay to front
        self.overlay.deiconify()
        self.overlay.lift()
        self.overlay.focus_set()

    def _cancel(self, _evt=None) -> None:
        try:
            self.overlay.destroy()
        finally:
            self.on_cancel()

    def _on_press(self, event) -> None:
        self.start_x, self.start_y = event.x, event.y
        if self.rect_id is not None:
            self.canvas.delete(self.rect_id)
            self.rect_id = None

    def _on_motion(self, event) -> None:
        if self.start_x is None or self.start_y is None:
            return
        cur_x, cur_y = event.x, event.y
        if self.rect_id is None:
            self.rect_id = self.canvas.create_rectangle(
                self.start_x,
                self.start_y,
                cur_x,
                cur_y,
                outline="#a78bfa",
                width=2,
            )
        else:
            self.canvas.coords(self.rect_id, self.start_x, self.start_y, cur_x, cur_y)

    def _on_release(self, event) -> None:
        if self.start_x is None or self.start_y is None:
            self._cancel()
            return
        x1, y1 = self.start_x, self.start_y
        x2, y2 = event.x, event.y
        self.overlay.withdraw()
        self.overlay.update_idletasks()
        # Compute screen-coordinates bbox
        # The canvas is full-screen, so its origin is (0, 0) of the screen
        left, top = min(x1, x2), min(y1, y2)
        right, bottom = max(x1, x2), max(y1, y2)
        bbox = (left, top, right, bottom)
        try:
            img = ImageGrab.grab(bbox=bbox)
        except Exception as exc:
            messagebox.showerror("Screenshot failed", str(exc))
            self._cancel()
            return
        finally:
            try:
                self.overlay.destroy()
            except Exception:
                pass
        self.on_capture(img, bbox)


def main() -> None:
    root = tk.Tk()
    app = WalletScreenshotApp(root)
    app.mainloop()


if __name__ == "__main__":
    main()
