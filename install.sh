#!/bin/bash
set -e

echo "🏆 Installing SoccerPredictor..."

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
echo "✅ Python version: $python_version"

# Install system dependencies if needed
if command -v apt-get >/dev/null 2>&1; then
    echo "📦 Installing system dependencies..."
    sudo apt-get update
    sudo apt-get install -y python3-venv python3-pip sqlite3
fi

# Create virtual environment
echo "🔧 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "🚀 Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install requirements
echo "📚 Installing Python dependencies..."
pip install -r requirements.txt

# Install package in development mode
echo "🔗 Installing SoccerPredictor package..."
pip install -e .

echo "✅ Installation complete!"
echo ""
echo "🎯 To get started:"
echo "  1. source venv/bin/activate"
echo "  2. cp .env.example .env"
echo "  3. Edit .env with your API keys"
echo "  4. python main.py --help"
echo ""
echo "📖 For more information, see README.md"