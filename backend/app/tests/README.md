# Test Requirements for Iteration 2

## Overview
This document outlines the test suite for Iteration 2 AI features of the CashFlow AI platform.

## Test Structure

### 1. Unit Tests (`test_ai_features.py`)
- **AI Entity Extraction**: Test Groq API integration for extracting vendor names
- **AI Categorization**: Test expense categorization accuracy
- **Batch Classification**: Test bulk transaction processing
- **Forecasting**: Test cashflow prediction algorithms
- **Anomaly Detection**: Test statistical anomaly identification
- **Weekly Summaries**: Test AI-generated narrative summaries
- **Alert System**: Test alert creation and management
- **Background Jobs**: Test Celery task triggering
- **Error Handling**: Test graceful failure scenarios

### 2. Background Task Tests (`test_background_tasks.py`)
- **CSV Import Processing**: Test async CSV processing pipeline
- **AI Classification Tasks**: Test background AI processing
- **Forecast Regeneration**: Test periodic forecast updates
- **Anomaly Detection Jobs**: Test scheduled anomaly checks
- **Weekly Summary Jobs**: Test automated summary generation
- **Task Error Handling**: Test task failure recovery
- **Task Progress Updates**: Test progress reporting
- **Task Chaining**: Test task dependencies

### 3. Integration Tests (`test_integration_ai.py`)
- **Complete Workflow**: CSV upload → AI classification → Insights
- **AI-Enhanced Dashboard**: Test dashboard with AI data
- **Forecast with Real Data**: Test forecasting with historical patterns
- **Anomaly Detection Integration**: Test end-to-end anomaly workflow
- **Cross-Feature Integration**: Test entity-transaction relationships
- **Performance Tests**: Test with large datasets
- **Concurrent Processing**: Test simultaneous AI tasks
- **Data Consistency**: Test counter updates and data integrity

## Test Categories

### Markers
- `@pytest.mark.unit`: Fast unit tests with mocks
- `@pytest.mark.integration`: Slower tests with real components
- `@pytest.mark.ai`: Tests specifically for AI features
- `@pytest.mark.slow`: Performance and load tests

### Coverage Areas

#### AI Features (Iteration 2)
1. **Groq API Integration**
   - Entity extraction accuracy
   - Category classification
   - API error handling
   - Rate limiting behavior

2. **Forecasting Engine**
   - Statistical model accuracy
   - Risk detection
   - Confidence scoring
   - Trend analysis

3. **Anomaly Detection**
   - Z-score calculations
   - False positive rates
   - Alert generation
   - Severity classification

4. **Background Processing**
   - Celery task execution
   - Task status tracking
   - Error recovery
   - Performance monitoring

5. **Insights Generation**
   - Weekly summaries
   - Recommendations
   - Narrative quality
   - Data aggregation

## Running Tests

### All Tests
```bash
cd backend
pytest -v
```

### Specific Categories
```bash
# Unit tests only
pytest -m unit -v

# AI feature tests
pytest -m ai -v

# Integration tests
pytest -m integration -v

# Performance tests
pytest -m slow -v
```

### Individual Test Files
```bash
# AI features
pytest app/tests/test_ai_features.py -v

# Background tasks
pytest app/tests/test_background_tasks.py -v

# Integration tests
pytest app/tests/test_integration_ai.py -v
```

## Test Data

### Fixtures
- `test_user_data`: Standard test user
- `sample_transactions`: Varied transaction patterns
- `sample_entities`: Customer/supplier data
- `sample_forecast`: Forecast data structure
- `sample_alerts`: Alert configurations

### Mock Services
- `mock_groq_client`: Simulated Groq API responses
- `mock_celery`: Simulated background task execution
- `mock_db_collections`: Database operation mocks

## Test Scenarios

### 1. Happy Path Tests
- CSV upload → AI classification → Insights generation
- Forecast generation with sufficient data
- Anomaly detection with clear outliers
- Weekly summary with meaningful patterns

### 2. Edge Cases
- Insufficient data for forecasting
- API service unavailability
- Empty transaction sets
- Malformed transaction descriptions

### 3. Error Scenarios
- Groq API rate limits
- Database connection failures
- Task execution timeouts
- Invalid data formats

### 4. Performance Tests
- 1000+ transaction processing
- Concurrent AI task execution
- Large CSV file handling
- Memory usage monitoring

## Success Criteria

### Functional Requirements
- [ ] All AI endpoints respond correctly
- [ ] Background tasks execute successfully
- [ ] Data integrity maintained across workflows
- [ ] Error scenarios handled gracefully

### Performance Requirements
- [ ] CSV processing < 30 seconds for 1000 rows
- [ ] AI classification < 5 seconds per 100 transactions
- [ ] Forecast generation < 10 seconds
- [ ] Concurrent task handling without conflicts

### Quality Requirements
- [ ] 90%+ test coverage for AI features
- [ ] All integration tests pass
- [ ] Mock services behave like real APIs
- [ ] Cleanup after each test run

## Environment Setup

### Test Dependencies
```bash
pip install pytest pytest-asyncio pytest-mock httpx
```

### Environment Variables
```bash
# For integration tests (optional)
GROQ_API_KEY=test_key
MONGODB_URL=mongodb://localhost:27017/test
REDIS_URL=redis://localhost:6379/1
```

### Test Database
- Separate test database instance
- Automatic cleanup between tests
- Seeded with test data fixtures

## Continuous Integration

### GitHub Actions (Example)
```yaml
name: Test Iteration 2
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11
      - name: Install dependencies
        run: pip install -r requirements.txt pytest pytest-asyncio
      - name: Run unit tests
        run: pytest -m unit
      - name: Run integration tests
        run: pytest -m integration
```

## Test Maintenance

### Regular Updates
- Update mock responses when API contracts change
- Add new test cases for feature additions
- Review and optimize slow tests
- Update fixtures for data model changes

### Test Documentation
- Document complex test scenarios
- Maintain test data specifications
- Update this README with new test types
- Track test coverage metrics
