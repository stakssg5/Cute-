from PIL import Image, ImageDraw, ImageFont

W, H = 768, 1662
bg = (10, 16, 28)
panel = (23, 33, 53)
purple = (120, 97, 255)
accent = (89, 74, 255)
text_primary = (230, 235, 255)
text_muted = (170, 178, 199)
green = (54, 199, 89)

img = Image.new("RGB", (W, H), bg)
d = ImageDraw.Draw(img)

try:
    font_title = ImageFont.truetype("DejaVuSans.ttf", 56)
    font_big = ImageFont.truetype("DejaVuSans.ttf", 180)
    font_med = ImageFont.truetype("DejaVuSans.ttf", 40)
    font_small = ImageFont.truetype("DejaVuSans.ttf", 30)
except Exception:
    font_title = ImageFont.load_default()
    font_big = ImageFont.load_default()
    font_med = ImageFont.load_default()
    font_small = ImageFont.load_default()

# Header
header_text = "Crypto PR+"
w, h = d.textsize(header_text, font=font_title)
d.text(((W - w) / 2, 40), header_text, font=font_title, fill=text_primary)

# Checked wallets
d.text((40, 200), "Checked Wallets", font=font_med, fill=text_muted)
d.text((40, 270), "3 830 672", font=font_big, fill=purple)

# Profits card
card_x, card_y, card_w, card_h = 36, 520, W - 72, 220
d.rounded_rectangle((card_x, card_y, card_x + card_w, card_y + card_h), radius=24, fill=panel)
d.line((card_x + 16, card_y + 16, card_x + 16, card_y + card_h - 16), fill=accent, width=12)

d.text((card_x + 60, card_y + 28), "0.01035 BTC", font=font_med, fill=text_primary)
d.text((card_x + 60, card_y + 88), "$1,122.87", font=font_med, fill=green)
d.text((card_x + 60, card_y + 146), "pulp parent...", font=font_small, fill=text_muted)

# Start button
btn_x, btn_y, btn_w, btn_h = 36, 1200, W - 72, 100
d.rounded_rectangle((btn_x, btn_y, btn_x + btn_w, btn_y + btn_h), radius=50, fill=accent)
w2, _ = d.textsize("Start search", font=font_med)
d.text((btn_x + (btn_w - w2) / 2, btn_y + 28), "Start search", font=font_med, fill=(255, 255, 255))

# Footer tabs (simple placeholders)
for i, label in enumerate(["My profile", "Plans", "", "Support", "FAQ"]):
    if not label:
        # center search icon placeholder
        cx = W // 2
        cy = 1500
        d.ellipse((cx - 54, cy - 54, cx + 54, cy + 54), fill=purple)
        d.rectangle((cx - 12, cy - 28, cx + 12, cy + 28), fill=(255, 255, 255))
        d.rectangle((cx - 28, cy - 12, cx + 28, cy + 12), fill=(255, 255, 255))
        continue
    x = 60 + i * 160
    d.text((x, 1580), label, font=font_small, fill=text_muted)

img.save("/workspace/preview.png")
print("Saved /workspace/preview.png")
