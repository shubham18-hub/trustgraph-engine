#!/bin/bash
# Run all tests with coverage

echo "Running TrustGraph Engine Test Suite"
echo "====================================="

# Backend tests
echo "[1/4] Running backend unit tests..."
pytest tests/ -v --cov=src --cov-report=html --cov-report=term

# API integration tests
echo "[2/4] Running API integration tests..."
pytest tests/test_api.py -v

# Frontend tests
echo "[3/4] Running frontend UI tests..."
npx playwright test tests/test_frontend.spec.js

# Performance tests
echo "[4/4] Running Lighthouse performance audit..."
npx lighthouse http://localhost:3000 --config-path=lighthouse-config.json --output=html --output-path=./lighthouse-report.html

echo ""
echo "Test Results:"
echo "- Coverage report: htmlcov/index.html"
echo "- Lighthouse report: lighthouse-report.html"
echo ""
echo "Done!"
