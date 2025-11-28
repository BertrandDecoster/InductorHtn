@echo off
echo ====================================
echo InductorHTN IDE - Quick Start
echo ====================================
echo.

echo Checking Python...
python --version
if errorlevel 1 (
    echo ERROR: Python not found! Please install Python 3.7+
    pause
    exit /b 1
)

echo.
echo Checking Node.js...
node --version
if errorlevel 1 (
    echo ERROR: Node.js not found! Please install Node.js 18+
    pause
    exit /b 1
)

echo.
echo ====================================
echo Starting Backend Server...
echo ====================================
cd backend
start cmd /k "python app.py"
cd ..

echo.
echo Waiting 3 seconds for backend to start...
timeout /t 3 /nobreak > nul

echo.
echo ====================================
echo Starting Frontend Dev Server...
echo ====================================
cd frontend
start cmd /k "npm run dev"
cd ..

echo.
echo ====================================
echo InductorHTN IDE is starting!
echo.
echo Backend:  http://localhost:5000
echo Frontend: http://localhost:5173
echo.
echo The IDE should open in your browser automatically.
echo.
echo Press any key to close this window (servers will keep running)
echo ====================================
pause > nul
