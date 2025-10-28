Crypto PR+ Desktop (Sample)

A small Windows desktop app that mimics the Telegram mini app UI with:
- Start/Stop infinite search simulation
- Profits list with Copy buttons
- Chain selector grid
- Speed slider

Build to Windows .exe with PyInstaller.

Quick start (Linux/macOS):
1. python3 -m venv .venv && source .venv/bin/activate
2. pip install -r requirements.txt
3. python app/main.py

Build Windows .exe (on Windows):
1. py -m venv .venv && .venv\\Scripts\\activate
2. pip install -r requirements.txt
3. pyinstaller build.spec

