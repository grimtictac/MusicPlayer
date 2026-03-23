@echo off
REM Check Python version and guide user to correct version

echo Checking Python version...
python --version

echo.
echo ============================================
echo PYTHON VERSION CHECK
echo ============================================
echo.
echo This project requires Python 3.11 or 3.12
echo (pygame does not support Python 3.14 yet)
echo.
echo Current Python version shown above.
echo.
echo If you see Python 3.14:
echo   1. Download Python 3.12 from:
echo      https://www.python.org/downloads/release/python-3120/
echo   2. Install it (check "Add to PATH")
echo   3. Use "python3.12" instead of "python" in commands
echo.
echo If you see Python 3.11 or 3.12:
echo   Run: python -m venv .venv
echo   Then: .venv\Scripts\activate
echo   Then: python -m pip install -r requirements.txt
echo.
pause
