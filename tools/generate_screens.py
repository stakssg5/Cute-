from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

WIDTH, HEIGHT = 828, 1792  # iPhone-like resolution for crisp preview
BG = (14, 21, 37)  # #0e1525
PANEL = (26, 34, 56)  # #1a2238
TEXT = (219, 227, 255)
SUBTLE = (139, 151, 177)
PRIMARY = (107, 121, 255)
SUCCESS = (59, 196, 107)
ORANGE = (255, 123, 29)

# Try to use DejaVu if available for nicer typography
FONT_PATHS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
]

def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    # Fallback to default bitmap font if TTF not present
    try:
        if bold and len(FONT_PATHS) > 1 and Path(FONT_PATHS[1]).exists():
            return ImageFont.truetype(FONT_PATHS[1], size)
        if Path(FONT_PATHS[0]).exists():
            return ImageFont.truetype(FONT_PATHS[0], size)
    except Exception:
        pass
    return ImageFont.load_default()


def rounded_rectangle(draw: ImageDraw.ImageDraw, xy, radius: int, fill):
    x0, y0, x1, y1 = xy
    draw.rounded_rectangle(xy, radius=radius, fill=fill)


def draw_header(draw: ImageDraw.ImageDraw):
    title_font = load_font(48, bold=True)
    sub_font = load_font(28)
    draw.text((WIDTH // 2, 80), "Jonathanzoes", font=title_font, fill=TEXT, anchor="ma")
    draw.text((WIDTH // 2, 135), "mini app", font=sub_font, fill=(138, 160, 255), anchor="ma")


def draw_checked_wallets(draw: ImageDraw.ImageDraw, value: str):
    label_font = load_font(40)
    num_font = load_font(140, bold=True)
    draw.text((64, 240), "Checked Wallets", font=label_font, fill=SUBTLE)
    draw.text((64, 330), value, font=num_font, fill=PRIMARY)


def draw_profit_card(draw: ImageDraw.ImageDraw, top: int, usd: str, copied: bool = False):
    # Card background
    card_margin = 32
    card_height = 200
    rounded_rectangle(draw, (card_margin, top, WIDTH - card_margin, top + card_height), 24, PANEL)
    # Left accent
    draw.rectangle((card_margin, top, card_margin + 10, top + card_height), fill=ORANGE)

    # Texts
    title_font = load_font(44, bold=True)
    usd_font = load_font(44)
    addr_font = load_font(32)

    draw.text((card_margin + 30, top + 24), "0,01035 BTC", font=title_font, fill=TEXT)
    draw.text((card_margin + 30, top + 80), usd, font=usd_font, fill=SUCCESS)
    addr = "pulp parent design secret..."
    draw.text((card_margin + 30, top + 130), addr, font=addr_font, fill=SUBTLE)

    # Copy button
    btn_w, btn_h = 140, 64
    btn_x = WIDTH - card_margin - btn_w - 20
    btn_y = top + (card_height - btn_h) // 2
    rounded_rectangle(draw, (btn_x, btn_y, btn_x + btn_w, btn_y + btn_h), 18, (42, 51, 82))
    btn_text = "Copied" if copied else "Copy"
    draw.text((btn_x + btn_w // 2, btn_y + btn_h // 2), btn_text, font=load_font(32, bold=True), fill=TEXT, anchor="mm")


def draw_chain_grid(draw: ImageDraw.ImageDraw, top: int):
    names = ["BTC", "ETH", "BNB", "SOL", "AVAX", "LTC", "OP", "MATIC", "TON", "TRX"]
    cols = 4
    cell_w = 160
    cell_h = 100
    start_x = 52
    gap = 26
    for idx, name in enumerate(names):
        r, c = divmod(idx, cols)
        x = start_x + c * (cell_w + gap)
        y = top + r * (cell_h + gap)
        rounded_rectangle(draw, (x, y, x + cell_w, y + cell_h), 18, PANEL)
        draw.text((x + cell_w // 2, y + cell_h // 2), name, font=load_font(36, bold=True), fill=TEXT, anchor="mm")


def draw_start_button(draw: ImageDraw.ImageDraw, y: int):
    # Simple gradient-like bar
    x0, x1 = 32, WIDTH - 32
    h = 110
    rounded_rectangle(draw, (x0, y, x1, y + h), 28, (107, 121, 255))
    draw.text(((x0 + x1) // 2, y + h // 2), "Start search", font=load_font(44, bold=True), fill=BG, anchor="mm")


def render(out_path: Path, wallets: str, usd: str, copied: bool):
    img = Image.new("RGB", (WIDTH, HEIGHT), BG)
    d = ImageDraw.Draw(img)

    draw_header(d)
    draw_checked_wallets(d, wallets)
    draw_profit_card(d, top=520, usd=usd, copied=copied)
    draw_chain_grid(d, top=770)
    draw_start_button(d, y=HEIGHT - 200)

    out_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(out_path)


if __name__ == "__main__":
    base = Path("screenshots")
    render(base / "overview.png", wallets="3 830 672", usd="$1122.87", copied=False)
    render(base / "profit_copied.png", wallets="3 834 210", usd="$1120.73", copied=True)
    print("Screens saved to:", base.resolve())
