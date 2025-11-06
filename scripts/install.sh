#!/bin/bash

# LocalAI Chat Installation Script

set -e

echo "🚀 Installing LocalAI Chat..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.8 or higher."
    exit 1
fi

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Found Python $PYTHON_VERSION"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
cd backend
pip install -r requirements.txt
cd ..

# Create necessary directories
mkdir -p models conversations

echo "✅ Installation complete!"
echo ""
echo "📖 Next steps:"
echo "1. Download some models: python models/download_models.py"
echo "2. Start the application: python backend/start.py"
echo "3. Open http://localhost:8000 in your browser"
