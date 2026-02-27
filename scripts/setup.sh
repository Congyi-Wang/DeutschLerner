#!/usr/bin/env bash
set -euo pipefail

echo "=== DeutschLerner Setup ==="

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv .venv
fi

echo "Activating virtual environment..."
source .venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt
pip install -e ".[dev]"

# Create .env from example if not exists
if [ ! -f ".env" ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please edit .env and add your API keys."
fi

# Create data directory
mkdir -p data

# Run migrations
echo "Running database migrations..."
python main.py migrate

echo ""
echo "✅ Setup complete!"
echo ""
echo "Next steps:"
echo "  1. Edit .env and add your API keys"
echo "  2. Edit config.yaml to configure your preferences"
echo "  3. Run: python main.py serve   (API server)"
echo "     Or:  python main.py cli     (interactive CLI)"
