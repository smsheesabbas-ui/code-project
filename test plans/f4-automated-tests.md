# Feature 4: Conversational Assistant - Automated/AI Test Plan

## Overview
Automated test specifications for NLP query parsing, intent recognition, and notification APIs.

---

## API Endpoints Under Test

### POST /api/v1/chat/query
**Purpose:** Process natural language financial query

**Request:**
```json
{
  "query": "What was my revenue last month?",
  "session_id": "uuid",
  "context": {
    "previous_queries": ["What was my revenue in January?"],
    "previous_intent": "revenue_query"
  }
}
```

**Expected Response:**
```json
{
  "query_id": "uuid",
  "intent": {
    "type": "revenue_query",
    "confidence": 0.96,
    "entities": {
      "metric": "revenue",
      "time_period": "last_month",
      "date_range": {"start": "2024-01-01", "end": "2024-01-31"}
    }
  },
  "response": {
    "text": "Your revenue last month was $8,500. That's 12% higher than the month before.",
    "data": {
      "amount": 8500.00,
      "currency": "USD",
      "comparison": {
        "previous_period": "2023-12",
        "change_percent": 12,
        "direction": "increase"
      }
    }
  },
  "suggested_followups": [
    "What about the month before?",
    "How does that compare to expenses?",
    "Which customers contributed most?"
  ],
  "processing_time_ms": 450
}
```

**Automated Assertions:**
```javascript
// Response time
assert(response.processing_time_ms < 3000, "Response exceeded 3s");

// Intent confidence
assert(response.intent.confidence >= 0.90, 
  "Intent confidence below 90%");

// Required fields
assert(response.response.text).isNotEmpty();
assert(response.response.data.amount).isNumber();

// Follow-up suggestions
assert(response.suggested_followups.length >= 2);
```

---

### POST /api/v1/chat/query (Complex Intent)

**Request:**
```json
{
  "query": "Why was last month lower?",
  "session_id": "uuid",
  "context": {
    "previous_queries": ["What was my revenue last month?"],
    "previous_intent": "revenue_query"
  }
}
```

**Expected Response:**
```json
{
  "intent": {
    "type": "trend_analysis",
    "confidence": 0.88,
    "entities": {
      "analysis_type": "variance_explanation",
      "reference_period": "last_month"
    }
  },
  "response": {
    "text": "Revenue was lower because Client B made no purchases this month, accounting for a $3,000 drop.",
    "factors": [
      {"customer": "Client B", "impact": -3000, "description": "No purchases"}
    ]
  }
}
```

---

### GET /api/v1/notifications/alerts
**Purpose:** Get active alerts and notifications

**Expected Response:**
```json
{
  "alerts": [
    {
      "id": "alert-1",
      "type": "cashflow_risk",
      "severity": "high",
      "title": "Potential Cash Shortfall",
      "message": "You may run low on cash in 12 days",
      "explanation": "Based on current spending rate and upcoming expenses",
      "suggested_action": "Consider collecting outstanding invoices",
      "triggered_at": "2024-02-27T10:00:00Z",
      "dismissible": true
    }
  ],
  "unread_count": 1
}
```

---

### POST /api/v1/notifications/weekly-summary
**Purpose:** Generate and send weekly summary

**Expected Response:**
```json
{
  "summary_id": "uuid",
  "status": "generated",
  "channels": ["email", "dashboard"],
  "delivery_status": {
    "email": "sent",
    "dashboard": "posted"
  },
  "content": {
    "revenue": {"amount": 8500, "vs_last_week": -12},
    "expenses": {"amount": 3200, "vs_last_week": 5},
    "highlights": []
  }
}
```

---

## Automated Test Cases

### TC-AUTO-F4-001: Intent Recognition Accuracy
```python
def test_intent_recognition():
    """Verify system recognizes at least 20 core financial intents"""
    test_queries = {
        # Revenue queries
        "What was my revenue last month?": "revenue_query",
        "How much money did I make?": "revenue_query",
        "Show me income for January": "revenue_query",
        "Total sales this quarter": "revenue_query",
        "What did I earn?": "revenue_query",
        
        # Expense queries
        "What were my expenses?": "expense_query",
        "How much did I spend on marketing?": "expense_category_query",
        "Show me costs": "expense_query",
        "Total expenses this month": "expense_query",
        "Where did my money go?": "expense_query",
        
        # Customer queries
        "Who is my top customer?": "top_customer_query",
        "Which client pays the most?": "top_customer_query",
        "Customer revenue breakdown": "customer_breakdown",
        "Who owes me money?": "outstanding_revenue",
        
        # Cashflow queries
        "How is my cashflow?": "cashflow_query",
        "Will I run out of money?": "cashflow_risk_query",
        "Cash position": "cash_query",
        
        # Trend queries
        "Why was last month lower?": "variance_explanation",
        "How are we trending?": "trend_query",
        "Compare this month to last": "comparison_query",
        "Business performance": "performance_summary",
        
        # Follow-up context
        "What about the month before?": "followup_time_shift",
        "How does that compare?": "followup_comparison",
    }
    
    correct = 0
    for query, expected_intent in test_queries.items():
        result = process_query(query)
        if result.intent.type == expected_intent:
            correct += 1
        else:
            print(f"Failed: '{query}' -> {result.intent.type} (expected {expected_intent})")
    
    accuracy = correct / len(test_queries)
    assert accuracy >= 0.90, f"Intent recognition {accuracy} below 90%"
    assert len(set([r.intent.type for r in results])) >= 20, "Fewer than 20 intents recognized"
```

### TC-AUTO-F4-002: Time Expression Parsing
```python
def test_time_parsing():
    """Verify time expressions correctly parsed"""
    time_tests = [
        ("last month", ("2024-01-01", "2024-01-31")),  # Assuming current = Feb 2024
        ("this month", ("2024-02-01", "2024-02-29")),
        ("January", ("2024-01-01", "2024-01-31")),
        ("Q1 2024", ("2024-01-01", "2024-03-31")),
        ("last 3 months", ("2023-11-01", "2024-01-31")),
        ("2023", ("2023-01-01", "2023-12-31")),
        ("yesterday", ("2024-02-26", "2024-02-26")),
        ("today", ("2024-02-27", "2024-02-27")),
    ]
    
    for expression, expected_range in time_tests:
        result = parse_time_expression(expression)
        assert result.start == expected_range[0], f"Failed: {expression}"
        assert result.end == expected_range[1], f"Failed: {expression}"
```

### TC-AUTO-F4-003: Context Maintenance
```python
def test_context_maintenance():
    """Verify context maintained across follow-up questions"""
    session_id = create_session()
    
    # First query establishes context
    r1 = query("What was my revenue last month?", session_id)
    assert r1.intent.entities.metric == "revenue"
    assert r1.intent.entities.time_period == "last_month"
    
    # Follow-up should inherit metric
    r2 = query("What about the month before?", session_id)
    assert r2.intent.entities.metric == "revenue"  # Inherited
    assert r2.intent.entities.time_period == "month_before_last"
    
    # Third follow-up should inherit metric and allow comparison
    r3 = query("How does that compare to expenses?", session_id)
    assert r3.intent.entities.metric == "comparison"
    assert r3.intent.entities.compare_a == "revenue"
    assert r3.intent.entities.compare_b == "expenses"
```

### TC-AUTO-F4-004: Plain Language Validation
```python
def test_plain_language():
    """Verify responses contain no accounting jargon"""
    prohibited_terms = [
        "variance", "standard deviation", "regression", 
        "correlation coefficient", "debit", "credit",
        "accounts payable", "accounts receivable",
        "general ledger", "journal entry", "accrual"
    ]
    
    test_queries = [
        "What are my trends?",
        "Analyze my performance",
        "How am I doing financially?",
        "Why did revenue change?"
    ]
    
    for query in test_queries:
        response = query_chat(query)
        response_lower = response.text.lower()
        
        for term in prohibited_terms:
            assert term not in response_lower, f"Prohibited term '{term}' found in response"
```

### TC-AUTO-F4-005: Response Time Under Load
```python
def test_chat_response_time():
    """Verify chat responses < 3s under load"""
    import asyncio
    
    async def make_query():
        start = time.time()
        await query_async("What was my revenue?")
        return (time.time() - start) * 1000
    
    # 50 concurrent queries
    times = await asyncio.gather(*[make_query() for _ in range(50)])
    
    avg_time = sum(times) / len(times)
    max_time = max(times)
    p95 = np.percentile(times, 95)
    
    assert avg_time < 3000, f"Avg response time {avg_time}ms exceeded 3s"
    assert p95 < 5000, f"P95 response time {p95}ms exceeded 5s"
```

### TC-AUTO-F4-006: Notification Delivery Reliability
```python
def test_notification_delivery():
    """Verify notification delivery >= 99%"""
    # Trigger 100 notifications
    success_count = 0
    
    for i in range(100):
        result = send_notification(
            type="weekly_summary",
            channel="email"
        )
        if result.status == "delivered":
            success_count += 1
    
    delivery_rate = success_count / 100
    assert delivery_rate >= 0.99, f"Delivery rate {delivery_rate} below 99%"
```

### TC-AUTO-F4-007: Follow-up Suggestion Quality
```python
def test_followup_suggestions():
    """Verify follow-up suggestions are contextually relevant"""
    r1 = query("What was my revenue last month?")
    
    # Check suggestions are relevant to revenue/time
    suggestions = r1.suggested_followups
    assert len(suggestions) >= 2
    
    relevant_keywords = ["month", "expense", "customer", "compare"]
    has_relevant = any(
        any(kw in sug.lower() for kw in relevant_keywords)
        for sug in suggestions
    )
    assert has_relevant, "No relevant follow-up suggestions"
```

### TC-AUTO-F4-008: Graceful Fallback
```python
def test_graceful_fallback():
    """Verify unknown queries handled gracefully"""
    unknown_queries = [
        "What's the weather today?",
        "Tell me about my stuff",
        "What's 2+2?",
        "Who won the game?"
    ]
    
    for query_text in unknown_queries:
        result = query(query_text)
        
        # Should not error
        assert result.intent.confidence < 0.70 or result.intent.type == "unknown"
        
        # Should provide helpful response
        assert "not sure" in result.response.text.lower() or \
               "help" in result.response.text.lower() or \
               "revenue" in result.response.text.lower() or \
               "expense" in result.response.text.lower()
        
        # Should not crash
        assert result.response.text is not None
```

---

## Load Test Specifications

### Chat Query Load Test
- **Concurrent Users:** 100
- **Duration:** 10 minutes
- **Query Mix:**
  - 40% simple queries (revenue, expenses)
  - 30% complex queries (trends, comparisons)
  - 20% follow-up queries (context-dependent)
  - 10% edge case queries
- **Success Criteria:**
  - 95% of queries < 3s
  - p99 < 5s
  - Intent recognition accuracy maintained ≥90%
  - No conversation state corruption

---

**Test Plan Version:** 1.0
**Last Updated:** 2026-02-27
