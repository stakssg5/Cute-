Wallet Screenshot Helper

Features:
- Select any screen region and capture it as an image
- Run OCR (if Tesseract installed) to detect a profit string
- Copy detected profit to clipboard
- Save screenshot to PNG

Requirements (Windows/macOS/Linux):
- Python 3.10+
- Pillow
- pytesseract (Python wrapper)
- Tesseract OCR engine installed on the OS (optional but recommended)

Install packages:
  pip install -r requirements.txt

Install Tesseract (Windows):
- Download installer from: https://github.com/UB-Mannheim/tesseract/wiki
- After install, if the app cannot find tesseract, set environment variable TESSERACT_PATH to tesseract.exe path.

Run dev:
  python app/main.py

Build .exe (Windows, from project root):
  pip install pyinstaller
  pyinstaller app.spec
  # Output will be in dist/wallet-screenshot-helper/

If OCR is not detecting amounts well, try selecting a tighter area around the number. You can also switch the UI to light/dark backgrounds; the app automatically inverts low-luminance selections to help Tesseract.
