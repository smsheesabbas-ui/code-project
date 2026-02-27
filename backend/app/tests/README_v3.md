# Test Requirements for Iteration 3

## Overview
This document outlines the comprehensive test suite for Iteration 3 features of the CashFlow AI platform, including conversational assistant, email notifications, and advanced dashboard.

## Test Structure

### 1. Chat Assistant Tests (`test_chat_assistant.py`)
- **Session Management**: Create, list, retrieve chat sessions
- **Intent Classification**: Test AI intent recognition for 8+ supported intents
- **Message Processing**: Test end-to-end chat message handling
- **Context Management**: Test conversation context across messages
- **Tool Execution**: Test data retrieval tools for chat responses
- **Error Handling**: Test ambiguous queries and error scenarios
- **Performance**: Test concurrent chat sessions

### 2. Email Notifications Tests (`test_email_notifications.py`)
- **Notification Preferences**: Get/update user notification settings
- **Email Sending**: Test weekly summaries and alert emails
- **Scheduled Tasks**: Test Celery Beat scheduled email tasks
- **Email Templates**: Test HTML template rendering
- **Resend.com Integration**: Test external email service API
- **Rate Limiting**: Test email rate limiting behavior
- **Multi-channel**: Test email and in-app notifications

### 3. Advanced Dashboard Tests (`test_dashboard_v3.py`)
- **Trends Data**: Test multi-period trend analysis
- **Cashflow Timeline**: Test historical + projected cashflow
- **Anomaly Display**: Test anomaly visualization on dashboard
- **Layout Management**: Test drag-drop dashboard customization
- **Widget Data**: Test individual dashboard widget endpoints
- **Mobile Responsiveness**: Test mobile-optimized layouts
- **Performance**: Test dashboard loading with large datasets

### 4. Integration Tests (`test_integration_v3.py`)
- **Complete User Journey**: End-to-end workflow across all features
- **Cross-Feature Context**: Test chat context with dashboard interactions
- **Data Consistency**: Verify consistent data across features
- **Concurrent Usage**: Test multiple users using all features
- **Error Recovery**: Test system behavior when features fail
- **Security**: Test data isolation between users

## Test Categories

### Markers
- `@pytest.mark.chat`: Chat assistant specific tests
- `@pytest.mark.notifications`: Email notification tests
- `@pytest.mark.dashboard`: Advanced dashboard tests
- `@pytest.mark.v3`: All Iteration 3 feature tests
- `@pytest.mark.integration`: Cross-feature integration tests
- `@pytest.mark.performance`: Performance and load tests

### Coverage Areas

#### Chat Assistant (Feature 4)
1. **Intent Classification**
   - Revenue queries: "What was my revenue?"
   - Expense queries: "What did I spend?"
   - Entity queries: "Show me Amazon transactions"
   - Forecast queries: "Will I run out of cash?"
   - Comparison queries: "Compare this month to last"
   - Trend queries: "How are we trending?"

2. **Tool Execution**
   - Revenue summary aggregation
   - Expense summary aggregation
   - Entity breakdown retrieval
   - Top customers/suppliers
   - Forecast data access

3. **Context Management**
   - Multi-turn conversations
   - Reference resolution ("it", "that", "compared to")
   - Session persistence
   - Context timeout handling

#### Email Notifications (Feature 4 continuation)
1. **Notification Types**
   - Weekly summary emails
   - Alert emails for anomalies
   - Cashflow risk notifications
   - In-app notifications

2. **Email Service Integration**
   - Resend.com API integration
   - Template rendering
   - HTML email formatting
   - Delivery tracking

3. **Scheduled Tasks**
   - Celery Beat configuration
   - Weekly summary scheduling
   - Alert digest scheduling
   - Task failure handling

#### Advanced Dashboard (Feature 5)
1. **Interactive Features**
   - Drag-and-drop layout customization
   - Date range filtering
   - Entity/category filtering
   - Real-time data updates

2. **Visualizations**
   - Revenue/expense trend charts
   - Cashflow timeline with projections
   - Anomaly highlighting
   - Mobile-responsive charts

3. **Performance**
   - Large dataset handling
   - Concurrent user support
   - Caching strategies
   - Load time optimization

## Running Tests

### All Iteration 3 Tests
```bash
cd backend
pytest -m v3 -v
```

### Specific Feature Tests
```bash
# Chat assistant only
pytest -m chat -v

# Email notifications only
pytest -m notifications -v

# Advanced dashboard only
pytest -m dashboard -v

# Integration tests only
pytest -m integration -v
```

### Individual Test Files
```bash
# Chat assistant
pytest app/tests/test_chat_assistant.py -v

# Email notifications
pytest app/tests/test_email_notifications.py -v

# Advanced dashboard
pytest app/tests/test_dashboard_v3.py -v

# Integration tests
pytest app/tests/test_integration_v3.py -v
```

### Performance Tests
```bash
# Run all performance tests
pytest -m performance -v

# Specific performance test
pytest app/tests/test_integration_v3.py::test_large_dataset_performance -v
```

## Test Data

### Fixtures
- `test_user`: Authenticated test user
- `sample_transactions`: 60 days of transaction data
- `sample_entities`: Customer/supplier entities
- `sample_alerts`: Anomaly and cashflow risk alerts
- `setup_full_v3_data`: Complete dataset for integration tests

### Mock Services
- `mock_groq_client`: Simulated Groq API for chat
- `mock_resend`: Simulated Resend.com email service
- `mock_agent`: Simulated chat agent processing
- `mock_forecast`: Simulated forecasting service

## Test Scenarios

### 1. Happy Path Workflows
- Complete user journey: Login → Dashboard → Chat → Notifications
- Chat conversation with context maintenance
- Dashboard customization and persistence
- Email notification delivery and tracking

### 2. Edge Cases
- Ambiguous chat queries
- Empty dashboard data
- Email service failures
- Large dataset performance
- Mobile viewport constraints

### 3. Error Scenarios
- Chat AI service unavailable
- Email API rate limits
- Dashboard data inconsistencies
- Concurrent user conflicts
- Network timeouts

### 4. Performance Tests
- 1000+ transaction processing
- 10+ concurrent chat sessions
- Dashboard loading under load
- Email batch processing
- Memory usage monitoring

## Success Criteria

### Functional Requirements
- [ ] Chat supports 8+ intents with correct data grounding
- [ ] Chat maintains context across 5+ message conversations
- [ ] Weekly emails sent automatically with correct data
- [ ] Dashboard customizable with drag-drop persistence
- [ ] Mobile-responsive design works on all screen sizes
- [ ] All integration workflows complete successfully

### Performance Requirements
- [ ] Chat response time < 2 seconds
- [ ] Dashboard loading < 3 seconds with 1000+ transactions
- [ ] Email delivery < 10 seconds
- [ ] Concurrent 10+ users without degradation
- [ ] Memory usage < 500MB for typical workload

### Quality Requirements
- [ ] 95%+ test coverage for Iteration 3 features
- [ ] All integration tests pass
- [ ] Mock services accurately simulate real APIs
- [ ] Error scenarios handled gracefully
- [ ] Data isolation enforced between users

## Environment Setup

### Test Dependencies
```bash
pip install pytest pytest-asyncio pytest-mock httpx aiohttp
```

### Environment Variables
```bash
# For integration tests
GROQ_API_KEY=test_key
RESEND_API_KEY=test_key
MONGODB_URL=mongodb://localhost:27017/test
REDIS_URL=redis://localhost:6379/1
```

### External Services
- Mock Groq API for chat testing
- Mock Resend.com for email testing
- Test MongoDB instance for data persistence
- Test Redis for caching/scheduled tasks

## Continuous Integration

### GitHub Actions (Example)
```yaml
name: Test Iteration 3
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
        run: pytest -m "unit and v3"
      - name: Run integration tests
        run: pytest -m "integration and v3"
      - name: Run performance tests
        run: pytest -m "performance and v3"
```

## Test Maintenance

### Regular Updates
- Update intent patterns for new chat capabilities
- Add new email template tests
- Update dashboard widget tests for new features
- Review and optimize slow integration tests

### Test Documentation
- Document new test scenarios for features
- Maintain test data specifications
- Update this README with new test types
- Track test coverage metrics across iterations

### Known Limitations
- Chat AI responses are mocked (real AI testing requires API keys)
- Email delivery is simulated (real delivery requires Resend.com account)
- Performance tests use synthetic data
- Mobile testing uses viewport simulation, not real devices
