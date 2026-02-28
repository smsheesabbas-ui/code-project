# CashFlow AI - Iteration 1 Test Suite

## Overview

This comprehensive test suite validates all functionality implemented in Iteration 1 of the CashFlow AI platform. The tests cover authentication, CSV ingestion, transaction management, dashboard analytics, and integration workflows.

## Test Structure

### Test Categories

1. **Authentication Tests** (`TestIteration1Authentication`)
   - User registration and login
   - JWT token generation and validation
   - Protected endpoint access
   - Token refresh functionality

2. **CSV Ingestion Tests** (`TestIteration1CSVIngestion`)
   - File upload validation
   - Column detection and mapping
   - Import preview functionality
   - Transaction creation from CSV
   - Error handling for invalid files

3. **Transaction Management Tests** (`TestIteration1Transactions`)
   - CRUD operations for transactions
   - Pagination and filtering
   - Data validation
   - Duplicate detection

4. **Dashboard Analytics Tests** (`TestIteration1Dashboard`)
   - KPI calculations
   - Revenue and expense aggregation
   - Top customers/suppliers analysis
   - Monthly trend data

5. **Integration Tests** (`TestIteration1Integration`)
   - End-to-end workflows
   - Complete CSV import pipeline
   - Error handling across components

6. **Performance Tests** (`TestIteration1Performance`)
   - API response time validation
   - Load testing for critical endpoints

## Running Tests

### Prerequisites

1. **MongoDB Running**: Ensure MongoDB is accessible
   ```bash
   docker-compose up -d mongo
   ```

2. **Dependencies Installed**: Install test dependencies
   ```bash
   pip install -r requirements.txt
   ```

### Quick Start

Run all tests with the test runner:
```bash
python run_tests.py
```

### Running Individual Test Suites

```bash
# Authentication tests only
python -m pytest test_iteration_1.py::TestIteration1Authentication -v

# CSV ingestion tests only
python -m pytest test_iteration_1.py::TestIteration1CSVIngestion -v

# Transaction tests only
python -m pytest test_iteration_1.py::TestIteration1Transactions -v

# Dashboard tests only
python -m pytest test_iteration_1.py::TestIteration1Dashboard -v

# Integration tests only
python -m pytest test_iteration_1.py::TestIteration1Integration -v

# Performance tests only
python -m pytest test_iteration_1.py::TestIteration1Performance -v
```

### Running with Specific Markers

```bash
# Run only authentication tests
python -m pytest -m auth -v

# Run only CSV tests
python -m pytest -m csv -v

# Run all tests except slow ones
python -m pytest -m "not slow" -v
```

## Test Data

Sample CSV files are provided in the `test_data/` directory:

- `sample_transactions.csv`: Standard format with Date, Description, Amount, Balance
- `complex_format.csv`: Debit/Credit format for testing column detection

## Expected Results

### Success Criteria

All tests should pass with the following expectations:

1. **Authentication**: 8/8 tests pass
   - User registration works correctly
   - Login generates valid JWT tokens
   - Protected endpoints require authentication
   - Token refresh functions properly

2. **CSV Ingestion**: 7/7 tests pass
   - File upload validates file type and size
   - Column detection works with confidence scoring
   - Preview generates correct data
   - Import creates transactions successfully
   - Error handling works for invalid inputs

3. **Transaction Management**: 6/6 tests pass
   - CRUD operations work correctly
   - Pagination and filtering function
   - Data validation prevents invalid entries
   - Duplicate detection works

4. **Dashboard Analytics**: 4/4 tests pass
   - KPI calculations are accurate
   - Revenue/expense aggregation works
   - Top entities analysis functions
   - Trend data is properly formatted

5. **Integration**: 2/2 tests pass
   - Complete CSV workflow functions
   - Error handling works across components

6. **Performance**: 1/1 test pass
   - API response times within limits
   - Health endpoint < 100ms
   - Auth endpoints < 500ms
   - Dashboard endpoints < 1s

### Performance Benchmarks

- **Health Endpoint**: < 100ms
- **Authentication Endpoints**: < 500ms
- **Dashboard Endpoints**: < 1 second
- **CSV Upload**: < 10 seconds for 10k rows

## Troubleshooting

### Common Issues

1. **MongoDB Connection Failed**
   - Ensure MongoDB is running: `docker-compose up -d mongo`
   - Check connection string in settings

2. **Test Database Cleanup**
   - Tests automatically clean up created data
   - If tests fail, manually clean with:
   ```python
   from app.core.database import get_database
   db = get_database()
   await db.users.delete_many({"email": {"$regex": "test|csv|txn|dash|integration|perf"}})
   ```

3. **Import Errors**
   - Ensure all dependencies are installed
   - Check Python version (3.11+ recommended)

4. **Timeout Errors**
   - Increase timeout in run_tests.py if needed
   - Check system resources

### Debug Mode

Run tests with verbose output and debugging:
```bash
python -m pytest test_iteration_1.py -v -s --tb=long
```

## Test Coverage

The test suite covers:

- ✅ All API endpoints
- ✅ Authentication flows
- ✅ Data validation
- ✅ Error handling
- ✅ Business logic
- ✅ Integration scenarios
- ✅ Performance requirements

## Continuous Integration

These tests are designed to run in CI/CD pipelines. The test runner returns appropriate exit codes:

- `0`: All tests passed
- `1`: One or more tests failed

## Next Steps

After all tests pass:

1. Review test coverage reports
2. Add any missing edge cases
3. Proceed to Iteration 2 development
4. Set up automated test runs in CI/CD

---

**Note**: This test suite validates the Iteration 1 implementation against the development plan requirements. All tests should pass before proceeding to Iteration 2.
