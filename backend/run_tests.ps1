# PowerShell script to run tests with coverage

# Install test requirements if needed
pip install -r requirements-test.txt

# Check for command line arguments
param (
    [Parameter(Position=0, Mandatory=$false)]
    [string]$TestType
)

if ($TestType -eq "performance") {
    # Run performance tests
    Write-Host "Running performance tests..."
    pytest -xvs tests/performance/
}
elseif ($TestType -eq "all") {
    # Run all tests with coverage
    Write-Host "Running all tests with coverage..."
    pytest --cov=app tests/ --cov-report=term --cov-report=html:coverage_report
}
else {
    # Run regular tests with coverage
    Write-Host "Running unit and integration tests with coverage..."
    pytest --cov=app tests/unit/ tests/integration/ --cov-report=term --cov-report=html:coverage_report
}

Write-Host "Test coverage report has been generated in coverage_report/index.html" 