#!/bin/bash
# run.sh - Quick start script for Maintenance Agent

set -e

echo "🚀 Maintenance Agent - Quick Start"
echo "=================================="
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+ first."
    exit 1
fi

echo "✅ Python found: $(python3 --version)"
echo ""

# Check if pip dependencies are installed
echo "📦 Checking dependencies..."
if ! python3 -c "import streamlit, fastapi, requests" 2>/dev/null; then
    echo "⚠️  Dependencies not found. Installing..."
    pip install -r requirements.txt
else
    echo "✅ Dependencies already installed"
fi

echo ""
echo "🎬 Starting Maintenance Agent..."
echo "=================================="
echo ""
echo "Deployment Option 2 (Recommended):"
echo "  - Streamlit: http://localhost:8501"
echo "  - FastAPI:   http://localhost:8001 (auto-started)"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Run the app
python3 -m streamlit run app_with_embedded_api.py

