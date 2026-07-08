@echo off
REM Local viewer: fetch('data/prices.json') is blocked when opening the HTML via
REM file://, so serve the folder over localhost instead. Ctrl+C to stop.
cd /d "%~dp0"
start "" "http://localhost:8123/regime-board.html"
python -m http.server 8123 2>nul || py -m http.server 8123
