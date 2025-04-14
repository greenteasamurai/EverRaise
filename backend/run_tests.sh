#!/bin/bash

# Install test requirements if needed
pip install -r requirements-test.txt

# Check for command line arguments
if [ "$1" == "performance" ]; then
    # Run performance tests
    echo "Running performance tests..."
    pytest -xvs tests/performance/
elif [ "$1" == "all" ]; then
    # Run all tests with coverage
    echo "Running all tests with coverage..."
    pytest --cov=app tests/ --cov-report=term --cov-report=html:coverage_report
else
    # Run regular tests with coverage
    echo "Running unit and integration tests with coverage..."
    pytest --cov=app tests/unit/ tests/integration/ --cov-report=term --cov-report=html:coverage_report
fi

echo "Test coverage report has been generated in coverage_report/index.html" 