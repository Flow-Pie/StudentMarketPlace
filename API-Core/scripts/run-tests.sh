#!/bin/bash

# Test runner script with comprehensive coverage

set -e

echo "🧪 Running StudentMarketPlace Test Suite"
echo "========================================"

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✅ Virtual environment activated"
fi

# Install test dependencies
echo "📦 Installing test dependencies..."
pip install -r requirements.txt
pip install pytest-cov pytest-html pytest-xdist

# Set test environment variables
export FLASK_ENV=testing
export DATABASE_URL=sqlite:///test.db
export JWT_SECRET_KEY=test-secret-key
export REDIS_URL=redis://localhost:6379/1

# Create test database
echo "🗄️ Setting up test database..."
flask db upgrade

# Run security checks
echo "🔒 Running security checks..."
bandit -r app/ -f json -o reports/bandit-report.json || true
safety check --json --output reports/safety-report.json || true

# Run linting
echo "🧹 Running code quality checks..."
flake8 app/ --output-file=reports/flake8-report.txt || true
black --check app/ || true

# Run tests with coverage
echo "🧪 Running tests with coverage..."
mkdir -p reports

pytest \
    --cov=app \
    --cov-report=html:reports/coverage \
    --cov-report=xml:reports/coverage.xml \
    --cov-report=term-missing \
    --html=reports/test-report.html \
    --self-contained-html \
    --junitxml=reports/junit.xml \
    -v \
    tests/

# Run performance tests separately
echo "⚡ Running performance tests..."
pytest -m "not slow" tests/test_performance.py -v

# Generate test summary
echo "📊 Test Summary"
echo "==============="
echo "✅ Unit tests completed"
echo "✅ Security tests completed"
echo "✅ Performance tests completed"
echo ""
echo "📁 Reports generated in ./reports/"
echo "   - Test coverage: reports/coverage/index.html"
echo "   - Test results: reports/test-report.html"
echo "   - Security scan: reports/bandit-report.json"
echo ""

# Check coverage threshold
coverage report --fail-under=70

echo "🎉 All tests completed successfully!"