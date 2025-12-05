@echo off
echo ================================
echo   Klipster - AI Video Clipper
echo ================================
echo.

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found!
    echo Please run: python -m venv venv
    echo Then run: pip install -r requirements.txt
    pause
    exit /b 1
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate

REM Check if .env file exists
if not exist ".env" (
    echo.
    echo WARNING: .env file not found!
    echo Please create .env and add your OPENAI_API_KEY
    echo You can copy .env.example to .env and edit it
    echo.
    pause
)

REM Start the application
echo.
echo Starting Klipster...
echo Open your browser to: http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo.
python run.py

pause
