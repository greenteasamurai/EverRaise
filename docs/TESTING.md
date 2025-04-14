# EverRaise Testing Strategy

This document outlines the testing strategy for the EverRaise application, including setup instructions, test types, and best practices.

## Table of Contents

- [Overview](#overview)
- [Backend Testing](#backend-testing)
  - [Unit Tests](#backend-unit-tests)
  - [Integration Tests](#backend-integration-tests)
  - [End-to-End Tests](#backend-end-to-end-tests)
- [Frontend Testing](#frontend-testing)
  - [Component Tests](#frontend-component-tests)
  - [Service Tests](#frontend-service-tests)
  - [End-to-End Tests](#frontend-end-to-end-tests)
- [Running Tests](#running-tests)
- [Continuous Integration](#continuous-integration)
- [Test Coverage](#test-coverage)
- [Best Practices](#best-practices)

## Overview

EverRaise uses a comprehensive testing strategy that includes unit, integration, and end-to-end tests for both backend and frontend components. The testing frameworks used are:

- **Backend**: Pytest with pytest-asyncio for async support
- **Frontend**: Vitest for unit/component tests and Playwright for E2E tests

## Backend Testing

### Backend Unit Tests

Unit tests focus on testing individual functions, classes, or modules in isolation. These tests are located in the `backend/tests/unit` directory.

**Key unit test areas:**
- Security utilities (password hashing, JWT tokens)
- LLM service functionality
- Gmail service functionality
- Utility functions

**Example of running unit tests:**
```bash
cd backend
pytest tests/unit
```

### Backend Integration Tests

Integration tests verify that different parts of the application work together correctly. These tests are located in the `backend/tests/integration` directory.

**Key integration test areas:**
- API endpoints
- Database interactions
- External service integrations

**Example of running integration tests:**
```bash
cd backend
pytest tests/integration
```

### Backend End-to-End Tests

End-to-end tests verify complete user flows through the API. These tests are located in the `backend/tests/e2e` directory.

**Key E2E test areas:**
- Authentication flow
- Report generation flow
- User management flow

**Example of running E2E tests:**
```bash
cd backend
pytest tests/e2e
```

## Frontend Testing

### Frontend Component Tests

Component tests verify that UI components render and behave correctly. These tests are located in the `frontend/src/__tests__/components` directory.

**Key component test areas:**
- User interface components
- Form validation
- State management within components

**Example of running component tests:**
```bash
cd frontend
npm test
```

### Frontend Service Tests

Service tests verify that API clients and data services work correctly. These tests are located in the `frontend/src/__tests__/services` directory.

**Key service test areas:**
- API client methods
- Data transformation functions
- Authentication service

### Frontend End-to-End Tests

End-to-end tests for the frontend verify complete user journeys through the UI. These tests are located in the `frontend/e2e` directory.

**Key E2E test areas:**
- Authentication flow
- Dashboard functionality
- Report creation workflow

**Example of running E2E tests:**
```bash
cd frontend
npm run test:e2e
```

## Running Tests

### Running All Tests

To run all tests (backend and frontend):

**Linux/macOS:**
```bash
./run_all_tests.sh
```

**Windows:**
```powershell
.\run_all_tests.ps1
```

### Running Backend Tests with Coverage

**Linux/macOS:**
```bash
cd backend
./run_tests.sh
```

**Windows:**
```powershell
cd backend
.\run_tests.ps1
```

### Running Frontend Tests with Coverage

```bash
cd frontend
npm run test:coverage
```

## Continuous Integration

All tests should be run as part of the CI/CD pipeline. The recommended CI configuration includes:

1. Running unit tests for both backend and frontend
2. Running integration tests for the backend
3. Running E2E tests for both backend and frontend
4. Generating and publishing coverage reports
5. Failing the build if tests fail or coverage drops below thresholds

## Test Coverage

We track test coverage using:
- **Backend**: pytest-cov
- **Frontend**: Vitest's built-in coverage reporting (based on Istanbul)

**Coverage targets:**
- **Critical modules**: 80% or higher
- **Overall codebase**: 70% or higher

Coverage reports are generated in HTML format in the following locations:
- Backend: `backend/coverage_report/index.html`
- Frontend: `frontend/coverage/index.html`

## Best Practices

### Writing Tests

1. **Follow AAA pattern**: Arrange, Act, Assert
2. **Test behavior, not implementation**: Focus on what the code should do, not how it does it
3. **Keep tests fast**: Tests should run quickly to encourage frequent running
4. **Keep tests independent**: Tests should not depend on each other
5. **Use descriptive test names**: Names should describe what is being tested

### Test Data Management

1. **Use fixtures**: Use pytest fixtures for backend and setup functions for frontend
2. **Mock external dependencies**: Use mocking to isolate tests from external services
3. **Use factory functions**: Create reusable functions to generate test data
4. **Clean up after tests**: Ensure tests clean up any resources they create

### Mocking

1. **Mock at the boundary**: Mock external dependencies, not internal components
2. **Verify mock interactions**: Verify that mocks are called correctly
3. **Keep mocks simple**: Don't try to replicate the entire behavior of the dependency

### Test Coverage

1. **Don't chase 100% coverage**: Focus on critical paths and edge cases
2. **Identify uncovered code**: Use coverage reports to identify areas needing more tests
3. **Balance coverage types**: Ensure a good mix of unit, integration, and E2E tests 