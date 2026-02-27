# Feature 3: AI Financial Intelligence - Automated/AI Test Plan

## Overview
Automated test specifications for classification, anomaly detection, forecasting, and insight APIs.

---

## API Endpoints Under Test

### POST /api/v1/ai/classify-batch
**Purpose:** Classify multiple transactions

**Request:**
```json
{
  "transaction_ids": ["uuid1", "uuid2", "uuid3"],
  "include_confidence": true
}
```

**Expected Response:**
```json
{
  "classifications": [
    {
      "transaction_id": "uuid1",
      "entity": { "name": "ACME Corp", "confidence": 0.92 },
      "category": { "name": "Consulting", "confidence": 0.89 },
      "tags": ["recurring"],
      "overall_confidence": 0.91
    }
  ],
  "processing_time_ms": 450
}
```

**Automated Assertions:**
```javascript
assert(response.processing_time_ms < 3000, "Classification exceeded 3s");

response.classifications.forEach(c => {
  assert(c.overall_confidence >= 0.85, 
    `Confidence ${c.overall_confidence} below 85%`);
  assert(c.entity.name).isNotEmpty();
  assert(c.category.name).isNotEmpty();
});
```

---

### GET /api/v1/ai/patterns/recurring
**Purpose:** Detect recurring payments

**Expected Response:**
```json
{
  "recurring_payments": [
    {
      "entity": "AWS",
      "amount_average": 245.50,
      "amount_range": [180.00, 320.00],
      "frequency": "monthly",
      "next_expected": "2024-03-15",
      "confidence": 0.94,
      "transactions": ["tx1", "tx2", "tx3"]
    }
  ],
  "detection_accuracy": 0.96
}
```

---

### GET /api/v1/ai/anomalies
**Purpose:** Detect spending and revenue anomalies

**Request:**
```json
{
  "period": "last_30_days",
  "sensitivity": "medium"
}
```

**Expected Response:**
```json
{
  "anomalies": [
    {
      "type": "spending_spike",
      "category": "Office Supplies",
      "current_amount": 850.00,
      "baseline_average": 200.00,
      "increase_percent": 325,
      "severity": "high",
      "confidence": 0.91,
      "explanation": "Office supplies spending 325% above typical"
    }
  ],
  "detection_accuracy": 0.92
}
```

**Automated Assertions:**
```javascript
assert(response.detection_accuracy >= 0.90, 
  "Anomaly detection accuracy below 90%");

response.anomalies.forEach(a => {
  assert(a.confidence >= 0.85);
  assert(a.severity).isOneOf(["low", "medium", "high"]);
  assert(a.explanation).isNotEmpty();
});
```

---

### GET /api/v1/ai/forecast/cashflow
**Purpose:** Generate cashflow forecast

**Request:**
```json
{
  "days": 30,
  "confidence_interval": 0.80
}
```

**Expected Response:**
```json
{
  "current_balance": 15400.00,
  "forecast": {
    "projected_low": {
      "amount": 8200.00,
      "date": "2024-03-15"
    },
    "projected_high": {
      "amount": 18500.00,
      "date": "2024-03-25"
    },
    "confidence_range": [7500.00, 21000.00]
  },
  "risk_alerts": [
    {
      "type": "low_cash",
      "threshold": 5000,
      "projected_minimum": 8200,
      "days_until": 15
    }
  ],
  "forecast_accuracy": 0.82
}
```

**Automated Assertions:**
```javascript
assert(response.forecast_accuracy >= 0.80, 
  "Forecast accuracy below 80%");

assert(response.forecast.projected_low.amount < 
       response.current_balance);

assert(response.processing_time_ms < 10000);
```

---

### GET /api/v1/ai/insights/weekly
**Purpose:** Generate weekly summary

**Expected Response:**
```json
{
  "week_start": "2024-02-19",
  "week_end": "2024-02-25",
  "summary": {
    "revenue": { "amount": 8500.00, "vs_last_week": -12 },
    "expenses": { "amount": 3200.00, "vs_last_week": 5 },
    "top_customer": { "name": "ACME Corp", "amount": 5000.00 },
    "top_expense": { "category": "Software", "amount": 800.00 }
  },
  "notable_changes": [
    "Revenue down 12% vs last week"
  ],
  "recommendations": [
    {
      "type": "revenue_recovery",
      "message": "Consider following up with inactive customers",
      "priority": "medium"
    }
  ]
}
```

---

### GET /api/v1/ai/recommendations
**Purpose:** Get actionable recommendations

**Expected Response:**
```json
{
  "recommendations": [
    {
      "id": "rec-1",
      "type": "customer_concentration",
      "title": "Customer Concentration Risk",
      "message": "ACME Corp represents 65% of your revenue",
      "action": "Consider diversifying your customer base",
      "priority": "high",
      "based_on": {
        "data_points": ["revenue_distribution"],
        "threshold_exceeded": 65
      }
    }
  ],
  "generated_at": "2024-02-27T10:00:00Z"
}
```

---

## Automated Test Cases

### TC-AUTO-F3-001: Classification Accuracy Benchmark
```python
def test_classification_accuracy():
    """Verify classification >= 85% accuracy on test set"""
    test_set = load_classification_test_set()  # 500+ labeled transactions
    
    correct = 0
    for tx in test_set:
        result = classify(tx.description, tx.amount)
        if (result.entity == tx.expected_entity and 
            result.category == tx.expected_category and
            result.confidence >= 0.85):
            correct += 1
    
    accuracy = correct / len(test_set)
    assert accuracy >= 0.85, f"Accuracy {accuracy} below 85%"
```

### TC-AUTO-F3-002: Recurring Detection Accuracy
```python
def test_recurring_detection():
    """Verify recurring payment detection >= 85% accuracy"""
    # Known recurring payments
    known_recurring = [
        {"entity": "AWS", "freq": "monthly", "variance": 0.15},
        {"entity": "Rent", "freq": "monthly", "variance": 0.0},
        {"entity": "Adobe", "freq": "monthly", "variance": 0.0},
    ]
    
    detected = detect_recurring_payments()
    
    # Match detected to known
    matches = 0
    for known in known_recurring:
        match = find_in_detected(detected, known)
        if match and match.frequency == known["freq"]:
            matches += 1
    
    accuracy = matches / len(known_recurring)
    assert accuracy >= 0.85
```

### TC-AUTO-F3-003: Anomaly Detection Precision
```python
def test_anomaly_detection():
    """Verify anomaly detection >= 90% accuracy, < 10% false positive"""
    # Dataset with labeled anomalies
    test_data = load_anomaly_test_set()
    
    true_positives = 0
    false_positives = 0
    false_negatives = 0
    
    for item in test_data:
        detected = detect_anomaly(item)
        
        if detected and item.is_true_anomaly:
            true_positives += 1
        elif detected and not item.is_true_anomaly:
            false_positives += 1
        elif not detected and item.is_true_anomaly:
            false_negatives += 1
    
    precision = true_positives / (true_positives + false_positives)
    recall = true_positives / (true_positives + false_negatives)
    
    assert precision >= 0.90, f"Precision {precision} below 90%"
    assert recall >= 0.90, f"Recall {recall} below 90%"
```

### TC-AUTO-F3-004: Forecast Accuracy
```python
def test_forecast_accuracy():
    """Verify 30-day forecast within 80% accuracy"""
    # Generate forecasts for historical periods
    # Compare to actual outcomes
    
    errors = []
    for period in historical_periods:
        forecast = generate_cashflow_forecast(period.start, days=30)
        actual = get_actual_cashflow(period.start, days=30)
        
        # Calculate mean absolute percentage error
        mape = calculate_mape(forecast, actual)
        errors.append(mape)
    
    avg_accuracy = 1 - (sum(errors) / len(errors))
    assert avg_accuracy >= 0.80, f"Forecast accuracy {avg_accuracy} below 80%"
```

### TC-AUTO-F3-005: Customer Concentration Calculation
```python
def test_customer_concentration():
    """Verify customer concentration calculation"""
    # Seed data
    seed_transactions([
        {"customer": "A", "amount": 6000, "date": "2024-01"},
        {"customer": "B", "amount": 3000, "date": "2024-01"},
        {"customer": "C", "amount": 1000, "date": "2024-01"},
    ])
    
    # Calculate
    concentration = calculate_customer_concentration()
    
    # Verify: A = 60%, B = 30%, C = 10%
    assert concentration.top_customer.percentage == 60.0
    assert concentration.risk_level == "high"  # > 50%
    
    # Verify alert triggered
    alerts = get_risk_alerts()
    assert any(a.type == "customer_concentration" for a in alerts)
```

### TC-AUTO-F3-006: Response Time Under Load
```python
def test_response_time_under_load():
    """Verify AI endpoints respond < 3s under load"""
    import asyncio
    
    async def make_request():
        start = time.time()
        await classify_batch(sample_transactions)
        return time.time() - start
    
    # 50 concurrent requests
    tasks = [make_request() for _ in range(50)]
    times = await asyncio.gather(*tasks)
    
    avg_time = sum(times) / len(times) * 1000
    max_time = max(times) * 1000
    p95_time = np.percentile(times, 95) * 1000
    
    assert avg_time < 3000, f"Avg time {avg_time}ms exceeded 3s"
    assert p95_time < 5000, f"P95 time {p95_time}ms exceeded 5s"
```

### TC-AUTO-F3-007: Recommendation Relevance
```python
def test_recommendation_relevance():
    """Verify recommendations based on actual data patterns"""
    # Scenario: High customer concentration
    seed_high_concentration_data()
    
    recs = generate_recommendations()
    
    # Should have customer concentration recommendation
    concentration_rec = find_rec_by_type(recs, "customer_concentration")
    assert concentration_rec is not None
    assert "concentration" in concentration_rec.message.lower()
    assert concentration_rec.priority == "high"
    
    # Scenario: Rising expenses
    seed_rising_expense_data()
    
    recs = generate_recommendations()
    expense_rec = find_rec_by_type(recs, "expense_trend")
    assert expense_rec is not None
    assert "expense" in expense_rec.message.lower()
```

### TC-AUTO-F3-008: Learning from Corrections
```python
def test_learning_from_corrections():
    """Verify system improves after user corrections"""
    # Initial classification
    tx1 = {"description": "AMZN Purchase", "amount": 50}
    result1 = classify(tx1)
    initial_entity = result1.entity
    
    # User correction
    correct_classification(tx1, entity="Amazon")
    
    # Retrain/update model
    trigger_model_update()
    
    # Similar transaction should now classify correctly
    tx2 = {"description": "AMZN MKTP", "amount": 75}
    result2 = classify(tx2)
    
    assert result2.entity == "Amazon"
    assert result2.confidence > result1.confidence
```

---

## Load Test Specifications

### AI Classification Load Test
- **Concurrent Users:** 50
- **Batch Size:** 100 transactions per request
- **Duration:** 10 minutes
- **Success Criteria:**
  - 95% of requests < 3s
  - p99 < 5s
  - Accuracy maintained ≥85%
  - No memory leaks

### Forecast Generation Load Test
- **Concurrent Requests:** 20
- **Forecast Days:** 30
- **Duration:** 10 minutes
- **Success Criteria:**
  - 95% of requests < 10s
  - p99 < 15s
  - Accuracy maintained ≥80%

---

**Test Plan Version:** 1.0
**Last Updated:** 2026-02-27
