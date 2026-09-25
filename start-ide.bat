@echo off
rem Double-click to start the InductorHTN web IDE: backend, frontend, then the browser.
rem Close the two server windows to stop it.

set ROOT=%~dp0

if not exist "%ROOT%.venv\Scripts\python.exe" (
    echo Python venv not found at %ROOT%.venv - create it first, see BUILD.md.
    pause
    exit /b 1
)

start "InductorHTN IDE - backend (port 5001)" /D "%ROOT%gui\backend" cmd /k ""%ROOT%.venv\Scripts\python.exe" app.py"
start "InductorHTN IDE - frontend (port 5173)" /D "%ROOT%gui\frontend" cmd /k "npm run dev"

rem Give the servers a few seconds, then open the editor.
timeout /t 6 /nobreak >nul
start "" http://localhost:5173
