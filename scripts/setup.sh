#!/bin/bash
# Setup script for Slack RAG Assistant

set -e

echo "Setting up Slack RAG Assistant..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $python_version"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Copy environment file
if [ ! -f .env ]; then
    echo "Creating .env file from template..."
    cp .env.example .env
    echo "Please edit .env file with your credentials"
fi

# Create config directories
echo "Creating config directories..."
mkdir -p config/channels config/templates data

# Initialize pre-commit hooks
echo "Setting up pre-commit hooks..."
pre-commit install

# Run database migrations
echo "Running database migrations..."
alembic upgrade head

echo ""
echo "Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env file with your credentials"
echo "2. Configure channels in config/channels.yaml"
echo "3. Run the bot with: python -m src.main"
echo ""
