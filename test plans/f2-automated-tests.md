# Feature 2: Business Entity Structuring - Automated/AI Test Plan

## Overview
Automated test specifications for entity recognition, classification, and dashboard APIs.

---

## API Endpoints Under Test

### POST /api/v1/entities/detect
**Purpose:** Auto-detect entity from transaction description

**Request:**
```json
{
  "transaction_id": "uuid",
  "description": "ACME Corp Payment Received - Invoice #1234",
  "amount": 5000.00,
  "direction": "income"
}
```

**Expected Response (Customer):**
```json
{
  "suggested_entity": {
    "name": "ACME Corp",
    "type": "customer",
    "confidence": 0.92,
    "is_new": true,
    "explanation": "Extracted from payment description"
  },
  "alternatives": [
    { "name": "ACME Corporation", "confidence": 0.15 }
  ],
  "requires_confirmation": false
}
```

**Expected Response (Supplier):**
```json
{
  "suggested_entity": {
    "name": "Amazon Web Services",
    "type": "supplier", 
    "confidence": 0.88,
    "is_new": false,
    "entity_id": "existing-uuid"
  },
  "requires_confirmation": false
}
```

**Automated Assertions:**
```javascript
// Confidence threshold
assert(response.suggested_entity.confidence >= 0.85, 
  "Entity detection confidence below 85%");

// Response time
assert(response.time < 2000, "Detection exceeded 2s limit");

// Entity name extracted
assert(response.suggested_entity.name).isNotEmpty();
assert(response.suggested_entity.type).isOneOf(["customer", "supplier"]);

// Ambiguous handling
if (response.suggested_entity.confidence < 0.70) {
  assert(response.requires_confirmation).equals(true);
}
```

---

### POST /api/v1/entities/confirm
**Purpose:** Confirm or correct entity assignment

**Request:**
```json
{
  "transaction_id": "uuid",
  "entity": {
    "name": "ACME Corporation",
    "type": "customer",
    "create_new": false,
    "entity_id": "existing-uuid"
  },
  "correction": {
    "ai_suggestion": "ACME Corp",
    "user_selection": "ACME Corporation",
    "is_correction": true
  }
}
```

**Expected Response:**
```json
{
  "success": true,
  "entity_id": "uuid",
  "transaction_updated": true,
  "learning_recorded": true
}
```

**Automated Assertions:**
```javascript
assert(response.success).equals(true);
assert(response.entity_id).matches(/^[0-9a-f-]{36}$/);
assert(response.learning_recorded).equals(true);

// Database verification
const tx = await db.query("SELECT entity_id FROM transactions WHERE id = ?", 
  request.transaction_id);
assert(tx.entity_id).equals(response.entity_id);
```

---

### GET /api/v1/entities/{entity_id}/transactions
**Purpose:** Get all transactions for an entity

**Expected Response:**
```json
{
  "entity": {
    "id": "uuid",
    "name": "ACME Corp",
    "type": "customer",
    "first_seen": "2024-01-15",
    "total_transactions": 15,
    "total_amount": 45000.00
  },
  "transactions": [
    {
      "id": "tx-uuid",
      "date": "2024-01-15",
      "description": "Payment",
      "amount": 5000.00,
      "tags": ["recurring"]
    }
  ]
}
```

---

### POST /api/v1/transactions/{id}/categorize
**Purpose:** Categorize transaction

**Request:**
```json
{
  "revenue_stream": "Consulting",
  "expense_category": null,
  "tags": ["Q1-2024", "priority-client"]
}
```

**Expected Response:**
```json
{
  "success": true,
  "ai_suggestions": {
    "revenue_stream": { "suggestion": "Consulting", "confidence": 0.89 },
    "category_confidence": 0.89
  }
}
```

---

### GET /api/v1/dashboard/top-entities
**Purpose:** Get top customers and suppliers

**Request:**
```json
{
  "period": "last_30_days",
  "limit": 5
}
```

**Expected Response:**
```json
{
  "customers": [
    {
      "entity_id": "uuid",
      "name": "ACME Corp",
      "total_revenue": 15000.00,
      "percentage": 45.5,
      "transaction_count": 5
    }
  ],
  "suppliers": [
    {
      "entity_id": "uuid", 
      "name": "AWS",
      "total_expense": 2500.00,
      "percentage": 30.2,
      "transaction_count": 3
    }
  ],
  "period": {
    "start": "2024-01-01",
    "end": "2024-01-31"
  }
}
```

**Automated Assertions:**
```javascript
// Limit enforced
assert(response.customers.length <= 5);
assert(response.suppliers.length <= 5);

// Sorted by amount (descending)
for (let i = 0; i < response.customers.length - 1; i++) {
  assert(response.customers[i].total_revenue >= 
         response.customers[i+1].total_revenue);
}

// Percentages sum to 100 (with tolerance)
const customerTotal = response.customers.reduce((s, c) => s + c.percentage, 0);
assert(customerTotal).between(99.9, 100.1);

// Response time
assert(response.time < 2000);
```

---

## Automated Test Cases

### TC-AUTO-F2-001: Entity Classification Accuracy
```python
def test_entity_classification_accuracy():
    """Verify entity detection >= 85% accuracy"""
    test_cases = [
        ("ACME Corp Payment", "customer", "ACME Corp"),
        ("AWS Invoice #1234", "supplier", "AWS"),
        ("Stripe Transfer", "customer", "Stripe"),
        ("Office Depot Purchase", "supplier", "Office Depot"),
        # ... 100+ test cases
    ]
    
    correct = 0
    for description, expected_type, expected_name in test_cases:
        result = detect_entity(description)
        if (result.type == expected_type and 
            result.name == expected_name and
            result.confidence >= 0.85):
            correct += 1
    
    accuracy = correct / len(test_cases)
    assert accuracy >= 0.85, f"Accuracy {accuracy} below 85%"
```

### TC-AUTO-F2-002: Learning System Validation
```python
def test_learning_system():
    """Verify corrections improve future classifications"""
    # Initial prediction
    result1 = detect_entity("AMZN MKTP Purchase")
    initial_confidence = result1.confidence
    
    # User correction
    correct_entity("AMZN MKTP Purchase", "Amazon")
    
    # Re-trigger learning
    trigger_learning_update()
    
    # Second prediction should be better
    result2 = detect_entity("AMZN Purchase")
    assert result2.name == "Amazon"
    assert result2.confidence > initial_confidence
```

### TC-AUTO-F2-003: Category Classification Accuracy
```python
def test_category_classification():
    """Verify expense category >= 85% accuracy"""
    test_transactions = [
        ("AWS Invoice", "Software/Tech"),
        ("Office Depot - Supplies", "Office Expenses"),
        ("Starbucks", "Meals & Entertainment"),
        ("Uber Ride", "Travel & Transport"),
        # ... 100+ cases
    ]
    
    correct = sum(1 for desc, cat in test_transactions 
                  if categorize(desc) == cat)
    accuracy = correct / len(test_transactions)
    assert accuracy >= 0.85
```

### TC-AUTO-F2-004: Dashboard Ranking Accuracy
```python
def test_dashboard_rankings():
    """Verify top customer/supplier rankings are correct"""
    # Seed test data
    seed_transactions([
        {"entity": "Customer A", "amount": 5000, "direction": "income"},
        {"entity": "Customer B", "amount": 3000, "direction": "income"},
        {"entity": "Customer C", "amount": 2000, "direction": "income"},
    ])
    
    # Get rankings
    dashboard = get_dashboard_top_entities()
    
    # Verify order
    assert dashboard.customers[0].name == "Customer A"
    assert dashboard.customers[0].total_revenue == 5000
    assert dashboard.customers[1].name == "Customer B"
    assert dashboard.customers[2].name == "Customer C"
    
    # Verify percentages
    total = 5000 + 3000 + 2000
    assert dashboard.customers[0].percentage == (5000/total*100)
```

### TC-AUTO-F2-005: Tag System Functionality
```python
def test_tag_system():
    """Verify tag CRUD and filtering"""
    tx_id = create_test_transaction()
    
    # Add tags
    add_tags(tx_id, ["Tax-Deductible", "Q1-2024"])
    
    # Verify stored
    tx = get_transaction(tx_id)
    assert "Tax-Deductible" in tx.tags
    assert "Q1-2024" in tx.tags
    
    # Filter by tag
    filtered = filter_by_tag("Tax-Deductible")
    assert tx_id in [t.id for t in filtered]
    
    # Remove tag
    remove_tag(tx_id, "Q1-2024")
    tx = get_transaction(tx_id)
    assert "Q1-2024" not in tx.tags
```

### TC-AUTO-F2-006: Entity Merge Data Integrity
```python
def test_entity_merge():
    """Verify merge preserves all transaction data"""
    # Setup: Two similar entities
    entity_a = create_entity("ACME Corp", transactions=5)
    entity_b = create_entity("ACME Corporation", transactions=3)
    
    # Merge
    merge_entities(entity_a, entity_b)
    
    # Verify
    merged = get_entity(entity_a)
    assert merged.transaction_count == 8
    assert "ACME Corporation" not in get_all_entity_names()
    
    # All transactions point to merged entity
    for tx_id in get_transaction_ids_for_entity(entity_b):
        tx = get_transaction(tx_id)
        assert tx.entity_id == entity_a
```

### TC-AUTO-F2-007: Period Filtering Accuracy
```python
def test_period_filtering():
    """Verify dashboard updates correctly for different periods"""
    # January data
    seed_transaction(date="2024-01-15", amount=1000, entity="Customer A")
    
    # February data
    seed_transaction(date="2024-02-15", amount=2000, entity="Customer A")
    
    # Test January only
    jan_dashboard = get_dashboard(period="2024-01")
    assert jan_dashboard.customers[0].total_revenue == 1000
    
    # Test full period
    all_dashboard = get_dashboard(period="2024-01-01_to_2024-02-29")
    assert all_dashboard.customers[0].total_revenue == 3000
```

---

## Load Test Specifications

### Entity Detection Load Test
- **Concurrent Requests:** 100
- **Request Mix:**
  - 70% detection requests
  - 20% confirmation requests
  - 10% dashboard queries
- **Duration:** 10 minutes
- **Success Criteria:**
  - 95% success rate
  - Average response < 2s
  - p95 < 3s
  - No accuracy degradation under load

---

**Test Plan Version:** 1.0
**Last Updated:** 2026-02-27
