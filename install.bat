@echo off
REM Ollama OS Assistant - Installation and Setup Script

echo.
echo ========================================
echo   Ollama OS Assistant Installer
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python is not installed or not in PATH
    echo.
    echo Please install Python from: https://www.python.org
    pause
    exit /b 1
)

echo [✓] Python detected
echo.

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not available
    pause
    exit /b 1
)

echo [✓] pip detected
echo.

REM Install requirements
echo Installing dependencies...
echo.

pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo [✓] Dependencies installed successfully
echo.

REM Check if Ollama is installed
where ollama >nul 2>&1
if errorlevel 1 (
    echo.
    echo [WARNING] Ollama is not installed or not in PATH
    echo.
    echo Please install Ollama from: https://ollama.ai
    echo.
    pause
) else (
    echo [✓] Ollama detected
    echo.
)

echo.
echo ========================================
echo   Setup Complete!
echo ========================================
echo.
echo To start using the assistant:
echo.
echo 1. Start Ollama in a new terminal:
echo    ollama serve
echo.
echo 2. In another terminal, run:
echo    python gui.py              (Graphical User Interface)
echo    OR
echo    python main.py             (Command Line Interface)
echo.
echo ========================================
echo.
pause
