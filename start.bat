@echo off
chcp 65001 >nul
title Monkey Bot

echo =========================================
echo    MONKEY BOT - Zapusk
echo =========================================
echo.

python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [OSHIBKA] Python ne naiden!
    echo Skachayte Python: https://www.python.org/downloads/
    echo Postavte galochku Add to PATH pri ustanovke
    pause
    exit /b 1
)
echo [OK] Python naiden
echo.

if not exist .env (
    echo [OSHIBKA] Fajl .env ne najden!
    echo Sozdajte .env i zapolnite BOT_TOKEN i OWNER_ID
    pause
    exit /b 1
)
echo [OK] Fajl .env najden
echo.

echo Ustanavlivayu zavisimosti...
pip install -r requirements.txt --quiet
if %errorlevel% neq 0 (
    echo [OSHIBKA] Ne udalos ustanovit zavisimosti!
    pause
    exit /b 1
)
echo [OK] Zavisimosti ustanovleny
echo.

echo =========================================
echo  Bot zapuskaetsya... Ctrl+C chtoby ostanovit
echo =========================================
echo.
python bot.py

echo.
echo Bot ostanovlen.
pause
