@echo off
REM run.bat - Quick start script for Maintenance Agent (Windows)

echo 🚀 Maintenance Agent - Quick Start
echo ==================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python not found. Please install Python 3.8+ first.
    pause
    exit /b 1
)

echo ✅ Python found: 
python --version
echo.

REM Check if pip dependencies are installed
echo 📦 Checking dependencies...
python -c "import streamlit, fastapi, requests" >nul 2>&1
if errorlevel 1 (
    echo ⚠️  Dependencies not found. Installing...
    pip install -r requirements.txt
) else (
    echo ✅ Dependencies already installed
)

echo.
echo 🎬 Starting Maintenance Agent...
echo ==================================
echo.
echo Deployment Option 2 (Recommended):
echo   - Streamlit: http://localhost:8501
echo   - FastAPI:   http://localhost:8001 (auto-started)
echo.
echo Press Ctrl+C to stop
echo.

REM Run the app
python -m streamlit run app_with_embedded_api.py
pause
