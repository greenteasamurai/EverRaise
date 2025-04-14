#!/bin/bash

# Set error handling
set -e

# Function to handle errors
handle_error() {
  echo -e "\033[0;31mError: $1\033[0m"
  exit 1
}

# Run tests with error handling
run_tests() {
  echo -e "\033[0;32m===== Running Backend Unit Tests =====\033[0m"
  cd backend
  python -m pytest tests/unit -v || handle_error "Backend unit tests failed"
  cd ..

  echo -e "\n\033[0;32m===== Running Backend Integration Tests =====\033[0m"
  cd backend
  python -m pytest tests/integration -v || handle_error "Backend integration tests failed"
  cd ..

  echo -e "\n\033[0;32m===== Running Backend E2E Tests =====\033[0m"
  cd backend
  python -m pytest tests/e2e -v || handle_error "Backend E2E tests failed"
  cd ..

  echo -e "\n\033[0;32m===== Running Frontend Unit Tests =====\033[0m"
  cd frontend
  npm test || handle_error "Frontend unit tests failed"
  cd ..

  echo -e "\n\033[0;32m===== Running Frontend E2E Tests =====\033[0m"
  cd frontend
  npm run test:e2e || handle_error "Frontend E2E tests failed"
  cd ..

  echo -e "\n\033[0;32mAll tests completed successfully!\033[0m"
}

# Run the tests
run_tests 