#!/bin/bash

# Development environment setup script

set -e

echo "🚀 Setting up StudentMarketPlace Development Environment"
echo "======================================================="

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "🐍 Python version: $python_version"

# Create virtual environment
if [ ! -d ".venv" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv .venv
fi

# Activate virtual environment
source .venv/bin/activate
echo "✅ Virtual environment activated"

# Upgrade pip
echo "⬆️ Upgrading pip..."
pip install --upgrade pip

# Install dependencies
echo "📦 Installing dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "📦 Installing development dependencies..."
pip install \
    pytest \
    pytest-cov \
    pytest-html \
    pytest-xdist \
    black \
    flake8 \
    isort \
    bandit \
    safety \
    pre-commit

# Setup pre-commit hooks
echo "🪝 Setting up pre-commit hooks..."
pre-commit install

# Create necessary directories
echo "📁 Creating project directories..."
mkdir -p logs
mkdir -p uploads
mkdir -p reports
mkdir -p app/static
mkdir -p app/templates

# Copy environment file if it doesn't exist
if [ ! -f ".env" ]; then
    echo "📄 Creating .env file from template..."
    cp .env.example .env
    echo "⚠️  Please update .env with your configuration"
fi

# Initialize database
echo "🗄️ Initializing database..."
export FLASK_APP=run.py
flask db upgrade

# Start Redis if available
if command -v redis-server &> /dev/null; then
    echo "🧠 Starting Redis server..."
    redis-server --daemonize yes --port 6379
else
    echo "⚠️  Redis not found. Install Redis for caching functionality."
fi

# Run initial tests
echo "🧪 Running initial tests..."
pytest tests/test_auth.py -v

echo ""
echo "🎉 Development environment setup complete!"
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. Run 'flask run' to start the development server"
echo "3. Visit http://localhost:5000 to see the API documentation"
echo "4. Run 'pytest' to execute the test suite"
echo ""
echo "Useful commands:"
echo "- flask run --debug    # Start development server"
echo "- pytest --cov=app     # Run tests with coverage"
echo "- black app/           # Format code"
echo "- flake8 app/          # Check code style"
echo "- pre-commit run --all-files  # Run all pre-commit hooks"