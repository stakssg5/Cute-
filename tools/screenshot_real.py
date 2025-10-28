import time
from pathlib import Path

from app.main import CryptoPRApp

try:
    import mss
    import mss.tools
except Exception as exc:  # pragma: no cover
    raise SystemExit("mss is required: pip install mss") from exc


def capture_window(app: CryptoPRApp, out_path: Path) -> None:
    # Ensure layout is computed
    app.update_idletasks()
    app.update()
    # Wait a tick for final size
    time.sleep(0.15)
    app.update()

    x = app.winfo_rootx()
    y = app.winfo_rooty()
    w = app.winfo_width()
    h = app.winfo_height()

    with mss.mss() as sct:
        monitor = {"top": int(y), "left": int(x), "width": int(w), "height": int(h)}
        img = sct.grab(monitor)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        mss.tools.to_png(img.rgb, img.size, output=str(out_path))


def main() -> None:
    app = CryptoPRApp()
    app.deiconify()

    # Overview
    capture_window(app, Path("screenshots/real_overview.png"))

    # Copy state
    app._copy_btc()  # type: ignore[attr-defined]
    app.update()
    time.sleep(0.2)
    capture_window(app, Path("screenshots/real_copied.png"))

    app.destroy()


if __name__ == "__main__":
    main()
