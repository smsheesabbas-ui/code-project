# Feature 5: Clarity Dashboard - Automated/AI Test Plan

## Overview
Automated test specifications for dashboard APIs, KPI calculations, and visualization.

---

## API Endpoints Under Test

### GET /api/v1/dashboard/overview
**Purpose:** Get dashboard KPI data

**Request:**
```json
{
  "period": "last_30_days",
  "metrics": ["cash_balance", "revenue", "expenses", "top_customers", "top_suppliers"]
}
```

**Expected Response:**
```json
{
  "period": {
    "start": "2024-01-27",
    "end": "2024-02-27"
  },
  "cash_balance": {
    "current": 15400.00,
    "currency": "USD",
    "updated_at": "2024-02-27T10:00:00Z",
    "is_negative": false
  },
  "revenue": {
    "total": 28500.00,
    "vs_previous_period": {
      "change_percent": 12,
      "direction": "increase"
    }
  },
  "expenses": {
    "total": 13100.00,
    "vs_previous_period": {
      "change_percent": -5,
      "direction": "decrease"
    }
  },
  "net_position": 15400.00,
  "top_customers": [
    {
      "entity_id": "uuid",
      "name": "ACME Corp",
      "revenue": 15000.00,
      "percentage": 52.6,
      "transaction_count": 5
    }
  ],
  "top_suppliers": [
    {
      "entity_id": "uuid",
      "name": "AWS",
      "expense": 2500.00,
      "percentage": 19.1,
      "transaction_count": 3
    }
  ],
  "load_time_ms": 450
}
```

**Automated Assertions:**
```javascript
// Response time
assert(response.load_time_ms < 2000, "Dashboard load exceeded 2s");

// Math accuracy
assert(response.revenue.total - response.expenses.total)
  .equals(response.net_position);

// Percentages sum to ~100%
const customerTotal = response.top_customers.reduce((s, c) => s + c.percentage, 0);
assert(customerTotal).between(99.9, 100.1);

// Negative balance handling
if (response.cash_balance.current < 0) {
  assert(response.cash_balance.is_negative).equals(true);
}
```

---

### GET /api/v1/dashboard/charts/trends
**Purpose:** Get trend chart data

**Expected Response:**
```json
{
  "period": "last_6_months",
  "interval": "monthly",
  "data_points": [
    {
      "period": "2023-09",
      "revenue": 22000.00,
      "expenses": 12500.00,
      "net": 9500.00
    },
    {
      "period": "2023-10",
      "revenue": 24500.00,
      "expenses": 13100.00,
      "net": 11400.00
    }
  ],
  "chart_render_time_ms": 800
}
```

**Automated Assertions:**
```javascript
assert(response.chart_render_time_ms < 2000);
assert(response.data_points.length >= 2);

// Data integrity
response.data_points.forEach(dp => {
  assert(dp.revenue - dp.expenses).equals(dp.net);
  assert(dp.period).matches(/^\d{4}-\d{2}$/);
});
```

---

### GET /api/v1/dashboard/charts/cashflow
**Purpose:** Get cashflow timeline data

**Expected Response:**
```json
{
  "historical": [
    {"date": "2024-01-15", "balance": 12000.00},
    {"date": "2024-01-30", "balance": 14500.00},
    {"date": "2024-02-15", "balance": 15400.00}
  ],
  "projection": {
    "forecast_days": 30,
    "points": [
      {"date": "2024-02-27", "balance": 15400.00, "type": "current"},
      {"date": "2024-03-15", "balance": 8200.00, "type": "projected_low"},
      {"date": "2024-03-27", "balance": 11200.00, "type": "projected"}
    ],
    "confidence_range": [7500, 14000]
  }
}
```

---

### POST /api/v1/dashboard/layout/save
**Purpose:** Save user dashboard layout

**Request:**
```json
{
  "visible_metrics": ["cash_balance", "revenue", "top_customers"],
  "card_order": ["revenue", "expenses", "cashflow", "top_customers"],
  "filters": {
    "period": "last_30_days",
    "tags": ["Q1-2024"]
  }
}
```

**Expected Response:**
```json
{
  "success": true,
  "layout_id": "uuid",
  "saved_at": "2024-02-27T10:05:00Z"
}
```

---

## Automated Test Cases

### TC-AUTO-F5-001: Dashboard Calculation Accuracy
```python
def test_dashboard_calculations():
    """Verify all dashboard calculations are accurate"""
    # Seed known data
    seed_transactions([
        {"date": "2024-02", "amount": 5000, "type": "income", "customer": "A"},
        {"date": "2024-02", "amount": 3000, "type": "income", "customer": "B"},
        {"date": "2024-02", "amount": -2000, "type": "expense", "category": "Software"},
        {"date": "2024-02", "amount": -1500, "type": "expense", "category": "Office"},
    ])
    
    # Get dashboard
    dashboard = get_dashboard(period="2024-02")
    
    # Verify calculations
    assert dashboard.revenue.total == 8000  # 5000 + 3000
    assert dashboard.expenses.total == 3500  # 2000 + 1500
    assert dashboard.net_position == 4500  # 8000 - 3500
    
    # Top customers
    assert dashboard.top_customers[0].name == "A"
    assert dashboard.top_customers[0].revenue == 5000
    assert dashboard.top_customers[0].percentage == 62.5  # 5000/8000
    
    assert dashboard.top_customers[1].name == "B"
    assert dashboard.top_customers[1].revenue == 3000
```

### TC-AUTO-F5-002: Period Filtering Accuracy
```python
def test_period_filtering():
    """Verify dashboard updates correctly for different periods"""
    # Seed data across months
    seed_transactions([
        {"date": "2024-01-15", "amount": 5000, "type": "income"},
        {"date": "2024-02-15", "amount": 7000, "type": "income"},
        {"date": "2024-03-15", "amount": 6000, "type": "income"},
    ])
    
    # Test January only
    jan = get_dashboard(period="2024-01")
    assert jan.revenue.total == 5000
    
    # Test Q1 (Jan-Mar)
    q1 = get_dashboard(period="2024-Q1")
    assert q1.revenue.total == 18000  # 5000 + 7000 + 6000
    
    # Test Feb only
    feb = get_dashboard(period="2024-02")
    assert feb.revenue.total == 7000
```

### TC-AUTO-F5-003: Trend Calculation Accuracy
```python
def test_trend_calculations():
    """Verify period-over-period trends calculated correctly"""
    # Seed month-over-month data
    seed_transactions([
        {"date": "2024-01", "amount": 10000, "type": "income"},  # Jan baseline
        {"date": "2024-02", "amount": 12000, "type": "income"},  # Feb +20%
    ])
    
    # Get February dashboard (compares to Jan)
    feb = get_dashboard(period="2024-02")
    
    assert feb.revenue.vs_previous_period.change_percent == 20
    assert feb.revenue.vs_previous_period.direction == "increase"
    
    # Test decrease scenario
    seed_transactions([
        {"date": "2024-03", "amount": 9000, "type": "income"},  # Mar -25% vs Feb
    ])
    
    mar = get_dashboard(period="2024-03")
    assert mar.revenue.vs_previous_period.change_percent == -25
    assert mar.revenue.vs_previous_period.direction == "decrease"
```

### TC-AUTO-F5-004: Dashboard Load Performance
```python
def test_dashboard_performance():
    """Verify dashboard loads within 2 seconds"""
    import time
    
    # Large dataset
    seed_large_dataset(transactions=50000)
    
    start = time.time()
    dashboard = get_dashboard()
    duration = (time.time() - start) * 1000
    
    assert duration < 2000, f"Dashboard load {duration}ms exceeded 2s"
```

### TC-AUTO-F5-005: Chart Data Accuracy
```python
def test_chart_data_accuracy():
    """Verify trend chart data matches dashboard totals"""
    # Seed monthly data
    seed_transactions([
        {"date": "2024-01-15", "amount": 5000, "type": "income"},
        {"date": "2024-01-20", "amount": -2000, "type": "expense"},
        {"date": "2024-02-15", "amount": 7000, "type": "income"},
        {"date": "2024-02-20", "amount": -3000, "type": "expense"},
    ])
    
    # Get chart data
    chart_data = get_chart_data(period="last_3_months")
    
    # Verify sums match
    jan_data = find_period(chart_data, "2024-01")
    assert jan_data.revenue == 5000
    assert jan_data.expenses == 2000
    assert jan_data.net == 3000
    
    feb_data = find_period(chart_data, "2024-02")
    assert feb_data.revenue == 7000
    assert feb_data.expenses == 3000
    assert feb_data.net == 4000
```

### TC-AUTO-F5-006: Layout Persistence
```python
def test_layout_persistence():
    """Verify dashboard layout saves and loads correctly"""
    user_id = "test-user"
    
    # Save custom layout
    custom_layout = {
        "visible_metrics": ["revenue", "expenses", "top_customers"],
        "card_order": ["top_customers", "revenue", "expenses"],
        "filters": {"period": "last_30_days"}
    }
    
    save_layout(user_id, custom_layout)
    
    # Load layout
    loaded = get_layout(user_id)
    
    assert loaded.visible_metrics == custom_layout["visible_metrics"]
    assert loaded.card_order == custom_layout["card_order"]
    assert loaded.filters.period == "last_30_days"
```

### TC-AUTO-F5-007: Tag Filtering
```python
def test_tag_filtering():
    """Verify tag filters work correctly"""
    # Seed tagged transactions
    seed_transactions([
        {"amount": 5000, "tags": ["Q1", "Priority"], "type": "income"},
        {"amount": 3000, "tags": ["Q2"], "type": "income"},
        {"amount": -2000, "tags": ["Q1", "Software"], "type": "expense"},
    ])
    
    # Filter by Q1 tag
    q1_dashboard = get_dashboard(tags=["Q1"])
    
    assert q1_dashboard.revenue.total == 5000  # Only Q1 revenue
    assert q1_dashboard.expenses.total == 2000  # Only Q1 expenses
    
    # Filter by multiple tags (OR logic)
    multi_dashboard = get_dashboard(tags=["Q1", "Q2"])
    assert multi_dashboard.revenue.total == 8000  # 5000 + 3000
```

### TC-AUTO-F5-008: Mobile Responsive API
```python
def test_mobile_dashboard():
    """Verify dashboard API returns mobile-optimized data"""
    # Request with mobile flag
    mobile_dashboard = get_dashboard(device="mobile")
    
    # Should return simplified data
    assert mobile_dashboard.top_customers.length <= 5
    assert "chart_svg" in mobile_dashboard or "chart_data" in mobile_dashboard
    assert mobile_dashboard.layout == "single_column"
```

---

## Load Test Specifications

### Dashboard Load Test
- **Concurrent Users:** 100
- **Request Mix:**
  - 60% overview requests
  - 25% chart data requests
  - 15% filter/refresh requests
- **Duration:** 10 minutes
- **Success Criteria:**
  - 95% of requests < 2s
  - p99 < 3s
  - No data inconsistency
  - All calculations accurate under load

---

**Test Plan Version:** 1.0
**Last Updated:** 2026-02-27
