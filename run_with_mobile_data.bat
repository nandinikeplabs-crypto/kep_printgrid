@echo off
title KEP PrintGrid - Mobile Data + Printer Spooler
cd /d "%~dp0"
echo ======================================================================
echo    KEP PRINTGRID - MOBILE DATA (4G/5G) QR SCANNER + PRINTER ENGINE
echo ======================================================================
echo.
python run_app.py --tunnel
pause
