#!/bin/bash
# Ollama OS Assistant - Installation and Setup Script

echo ""
echo "========================================"
echo "  Ollama OS Assistant Installer"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python is not installed"
    echo ""
    echo "Please install Python 3 first"
    exit 1
fi

echo "[✓] Python detected"
echo ""

# Check if pip is available
if ! command -v pip3 &> /dev/null; then
    echo "[ERROR] pip3 is not available"
    exit 1
fi

echo "[✓] pip3 detected"
echo ""

# Install requirements
echo "Installing dependencies..."
echo ""

pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Failed to install dependencies"
    exit 1
fi

echo ""
echo "[✓] Dependencies installed successfully"
echo ""

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo ""
    echo "[WARNING] Ollama is not installed"
    echo ""
    echo "Please install Ollama from: https://ollama.ai"
    echo ""
else
    echo "[✓] Ollama detected"
    echo ""
fi

echo ""
echo "========================================"
echo "   Setup Complete!"
echo "========================================"
echo ""
echo "To start using the assistant:"
echo ""
echo "1. Start Ollama in a new terminal:"
echo "   ollama serve"
echo ""
echo "2. In another terminal, run:"
echo "   python3 gui.py              (Graphical User Interface)"
echo "   OR"
echo "   python3 main.py             (Command Line Interface)"
echo ""
echo "========================================"
echo ""
