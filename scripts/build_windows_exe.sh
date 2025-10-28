#!/usr/bin/env bash
set -euo pipefail

# Build a Windows .exe using PyInstaller via wine/cross is complex. Instead, this
# script documents the steps for local Windows or WSL users.
# Usage on Windows (PowerShell):
#   python -m pip install -r requirements.txt pyinstaller
#   pyinstaller -F -n wallet-scanner scanner/cli.py
# The executable will be at dist/wallet-scanner.exe

echo "This script is a placeholder. Run on Windows with PyInstaller as noted in comments."