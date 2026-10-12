@echo off
rem Starts yapper-snip and opens it in the default browser.
cd /d "%~dp0"
uv run python -m app --open
if errorlevel 1 pause
