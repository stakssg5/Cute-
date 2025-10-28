@echo off
REM Build Windows .exe for Wallet Screenshot Helper
SETLOCAL ENABLEEXTENSIONS ENABLEDELAYEDEXPANSION

python --version || (echo Python not found & exit /b 1)

pip install -r requirements.txt || exit /b 1
pip install pyinstaller || exit /b 1

pyinstaller app.spec || exit /b 1

echo Build complete. See dist\wallet-screenshot-helper\wallet-screenshot-helper.exe
