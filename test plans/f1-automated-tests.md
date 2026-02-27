# Feature 1: Smart Data Ingestion Engine - Automated/AI Test Plan

## Overview
This document contains specifications for automated testing of Feature 1, including API contracts, assertion patterns, and expected behaviors for AI/ML testers and automation frameworks.

---

## API Endpoints Under Test

### POST /api/v1/import/upload
**Purpose:** File upload endpoint

**Request:**
```json
{
  "file": "<multipart/form-data>",
  "user_id": "string"
}
```

**Expected Responses:**

| Scenario | Status | Response |
|----------|--------|----------|
| Valid CSV | 200 | `{ "upload_id": "uuid", "status": "uploaded", "file_size": 1024 }` |
| Invalid file type | 400 | `{ "error": "INVALID_FILE_TYPE", "message": "Only CSV files supported" }` |
| File too large (>10MB) | 400 | `{ "error": "FILE_TOO_LARGE", "message": "Max 10MB", "max_size": 10485760 }` |
| Empty file | 400 | `{ "error": "EMPTY_FILE", "message": "File is empty" }` |
| Auth error | 401 | `{ "error": "UNAUTHORIZED" }` |

**Automated Assertions:**
```javascript
// Response time < 10s for 10k rows
assert(response.time < 10000, "Upload exceeded 10s limit");

// Schema validation
assert(response.upload_id).matches(/^[0-9a-f-]{36}$/);
assert(response.status).isOneOf(["uploaded", "processing", "error"]);

// Error format consistency
assert(error_response).hasKeys(["error", "message"]);
```

---

### POST /api/v1/import/detect-columns
**Purpose:** Auto-detect column mappings

**Request:**
```json
{
  "upload_id": "uuid",
  "sample_rows": 20
}
```

**Expected Response (Success):**
```json
{
  "detection_confidence": 0.92,
  "columns": {
    "date": { "source_column": "Date", "confidence": 0.98, "format": "MM/DD/YYYY" },
    "description": { "source_column": "Description", "confidence": 0.95 },
    "amount": { "source_column": "Amount", "confidence": 0.94 },
    "balance": { "source_column": "Balance", "confidence": 0.85 }
  },
  "detected_format": "single_amount",
  "unmapped_columns": ["Reference"]
}
```

**Expected Response (Ambiguous):**
```json
{
  "detection_confidence": 0.62,
  "columns": {
    "date": { "source_column": "Date", "confidence": 0.89, "format": "MM/DD/YYYY" },
    "amount": null
  },
  "requires_manual_input": true,
  "suggestions": ["Multiple amount columns detected - please select"]
}
```

**Automated Assertions:**
```javascript
// Confidence threshold
assert(response.detection_confidence >= 0.85, 
  "Detection confidence below 85% threshold");

// Required columns present when confidence high
if (response.detection_confidence >= 0.85) {
  assert(response.columns).hasKeys(["date", "description", "amount"]);
}

// Amount detection variants
assert(response.columns.amount || 
       (response.columns.debit && response.columns.credit),
  "Must detect either Amount or Debit/Credit");

// Response time
assert(response.time < 2000, "Detection exceeded 2s limit");
```

---

### POST /api/v1/import/preview
**Purpose:** Generate preview of parsed data

**Request:**
```json
{
  "upload_id": "uuid",
  "column_mapping": {
    "date": "Date",
    "description": "Description", 
    "amount": "Amount"
  },
  "row_limit": 20
}
```

**Expected Response:**
```json
{
  "preview_id": "uuid",
  "rows": [
    {
      "row_number": 1,
      "date": "2024-01-15",
      "description": "ACME Corp Payment",
      "amount": 1250.00,
      "balance": 15400.00,
      "is_duplicate": false,
      "validation_errors": []
    }
  ],
  "total_rows": 100,
  "validation_summary": {
    "valid_rows": 95,
    "error_rows": 5,
    "duplicate_rows": 3
  }
}
```

**Automated Assertions:**
```javascript
// Row limit enforcement
assert(response.rows.length <= 20, "Preview exceeds row limit");

// ISO date format
response.rows.forEach(row => {
  assert(row.date).matches(/^\d{4}-\d{2}-\d{2}$/);
});

// Numeric amount
response.rows.forEach(row => {
  assert(typeof row.amount).equals("number");
});

// Duplicate flag present
response.rows.forEach(row => {
  assert(typeof row.is_duplicate).equals("boolean");
});

// Response time
assert(response.time < 2000, "Preview exceeded 2s limit");
```

---

### POST /api/v1/import/confirm
**Purpose:** Commit transactions to database

**Request:**
```json
{
  "upload_id": "uuid",
  "preview_id": "uuid",
  "duplicate_action": "skip", // skip, overwrite, import_anyway
  "invalid_action": "skip" // skip, edit_first
}
```

**Expected Response:**
```json
{
  "import_id": "uuid",
  "status": "completed",
  "imported_count": 95,
  "skipped_duplicates": 3,
  "skipped_errors": 2,
  "transactions": ["uuid1", "uuid2", ...]
}
```

**Automated Assertions:**
```javascript
// Counts sum to total
const total = response.imported_count + 
                response.skipped_duplicates + 
                response.skipped_errors;
assert(total).equals(expected_total_rows);

// UUIDs returned for imported
assert(response.transactions.length).equals(response.imported_count);
response.transactions.forEach(id => {
  assert(id).matches(/^[0-9a-f-]{36}$/);
});

// Database verification
const db_count = await db.query(
  "SELECT COUNT(*) FROM transactions WHERE import_id = ?", 
  response.import_id
);
assert(db_count).equals(response.imported_count);
```

---

## Test Data Sets for Automation

### Dataset 1: Standard Bank Format (test-data-standard.csv)
```csv
Date,Description,Amount,Balance
01/15/2024,ACME Corp Payment,1250.00,15400.00
01/16/2024,Office Supplies,-45.50,15354.50
01/17/2024,Client B Invoice,3200.00,18554.50
```
**Expected Detection:** date=Date, description=Description, amount=Amount

### Dataset 2: Debit/Credit Split (test-data-split.csv)
```csv
Date,Description,Debit,Credit,Balance
01/15/2024,ACME Corp Payment,,1250.00,15400.00
01/16/2024,Office Supplies,45.50,,15354.50
```
**Expected Detection:** date=Date, description=Description, debit=Debit, credit=Credit

### Dataset 3: No Headers (test-data-noheaders.csv)
```csv
01/15/2024,ACME Corp Payment,1250.00,15400.00
01/16/2024,Office Supplies,-45.50,15354.50
```
**Expected Detection:** requires_manual_input=true

### Dataset 4: European Date Format (test-data-european.csv)
```csv
Date,Description,Amount
15/01/2024,ACME Corp Payment,1250.00
16/01/2024,Office Supplies,-45.50
```
**Expected Detection:** date format=DD/MM/YYYY

### Dataset 5: Duplicates (test-data-duplicates.csv)
```csv
Date,Description,Amount
01/15/2024,ACME Corp Payment,1250.00
01/15/2024,ACME Corp Payment,1250.00
01/16/2024,Office Supplies,-45.50
```
**Expected:** Row 2 flagged as duplicate

### Dataset 6: Errors (test-data-errors.csv)
```csv
Date,Description,Amount
invalid_date,ACME Corp Payment,1250.00
01/16/2024,Office Supplies,not_a_number
01/17/2024,,3200.00
```
**Expected:** Row 1 = date error, Row 2 = amount error, Row 3 = missing description

---

## Automated Test Cases

### TC-AUTO-F1-001: Upload Performance
```python
def test_upload_performance():
    """Verify upload completes within 10 seconds for 10k rows"""
    large_csv = generate_csv(rows=10000, size_mb=2)
    
    start = time.now()
    response = upload(large_csv)
    duration = time.now() - start
    
    assert response.status == 200
    assert duration < 10000, f"Upload took {duration}ms, max 10000ms"
```

### TC-AUTO-F1-002: Detection Accuracy Benchmark
```python
def test_detection_accuracy():
    """Verify detection accuracy >= 85% across test bank formats"""
    test_formats = [
        "chase_bank.csv",
        "bofa.csv", 
        "wells_fargo.csv",
        "citi.csv",
        "capital_one.csv"
    ]
    
    correct_detections = 0
    for format_file in test_formats:
        result = detect_columns(format_file)
        if result.confidence >= 0.85 and all_required_detected(result):
            correct_detections += 1
    
    accuracy = correct_detections / len(test_formats)
    assert accuracy >= 0.85, f"Detection accuracy {accuracy} below 85%"
```

### TC-AUTO-F1-003: Duplicate Detection Accuracy
```python
def test_duplicate_detection():
    """Verify duplicate detection >= 95% accuracy"""
    # Setup: Import base transactions
    base_transactions = load_test_transactions()
    import_transactions(base_transactions)
    
    # Test: Import with known duplicates
    test_file = "with_duplicates.csv"
    preview = generate_preview(test_file)
    
    # Verify duplicates flagged correctly
    true_duplicates = preview.rows.filter(r => r.is_duplicate)
    actual_duplicates = count_actual_duplicates(test_file)
    
    accuracy = len(true_duplicates) / actual_duplicates
    assert accuracy >= 0.95, f"Duplicate detection {accuracy} below 95%"
```

### TC-AUTO-F1-004: Data Normalization
```python
def test_data_normalization():
    """Verify all stored data follows schema"""
    import_result = import_csv("test-data-standard.csv")
    
    # Verify database schema
    transactions = db.query("SELECT * FROM transactions WHERE import_id = ?", 
                          import_result.import_id)
    
    for tx in transactions:
        # ISO date format
        assert re.match(r'^\d{4}-\d{2}-\d{2}$', tx.date)
        
        # Signed numeric amount
        assert isinstance(tx.amount, (int, float))
        
        # Required fields present
        assert tx.transaction_id
        assert tx.user_id
        assert tx.description
        assert tx.import_timestamp
        assert tx.source_file_reference
```

### TC-AUTO-F1-005: Error Handling
```python
def test_error_handling():
    """Verify graceful error handling for invalid inputs"""
    invalid_cases = [
        ("empty.csv", "EMPTY_FILE"),
        ("large.pdf", "INVALID_FILE_TYPE"),
        ("15mb.csv", "FILE_TOO_LARGE"),
        ("corrupted.csv", "PARSE_ERROR")
    ]
    
    for file, expected_error in invalid_cases:
        response = upload(file)
        assert response.status >= 400
        assert response.json.error == expected_error
        assert "message" in response.json
        assert "stacktrace" not in response.json  # No internal details leaked
```

### TC-AUTO-F1-006: Security - File Validation
```python
def test_file_security():
    """Verify file type validation prevents malicious uploads"""
    malicious_files = [
        ("script.js", "javascript"),
        ("payload.php", "php"),
        ("malware.exe", "exe"),
        ("shell.sh", "shell"),
        ("virus.csv.exe", "double extension")
    ]
    
    for filename, type in malicious_files:
        response = upload(filename)
        assert response.status == 400
        assert response.json.error == "INVALID_FILE_TYPE"
```

### TC-AUTO-F1-007: Concurrency
```python
def test_concurrent_uploads():
    """Verify system handles concurrent uploads"""
    import asyncio
    
    async def upload_task(user_id):
        return await upload_async("test.csv", user_id=user_id)
    
    # 10 concurrent uploads from different users
    tasks = [upload_task(f"user_{i}") for i in range(10)]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # All should succeed
    for result in results:
        assert not isinstance(result, Exception)
        assert result.status == 200
```

---

## Load Test Specifications

### Upload Load Test
- **Concurrent Users:** 50
- **Duration:** 10 minutes
- **File Size:** 1MB average
- **Success Criteria:**
  - 95% of uploads complete successfully
  - Average response time < 10s
  - Error rate < 2%
  - No memory leaks

### Detection Load Test
- **Concurrent Requests:** 100
- **Sample Rows:** 20 per request
- **Success Criteria:**
  - 99% success rate
  - Average response time < 2s
  - p95 response time < 3s

---

## Database Verification Queries

### Verify Import Storage
```sql
-- Check transactions stored correctly
SELECT 
  transaction_id,
  user_id,
  DATE(date) as date,
  description,
  amount,
  currency,
  import_timestamp,
  source_file_reference
FROM transactions 
WHERE import_id = '?';
```

### Verify Duplicate Handling
```sql
-- Check no duplicates in database after skip action
SELECT date, amount, description, COUNT(*) as cnt
FROM transactions
WHERE user_id = '?' AND import_id = '?'
GROUP BY date, amount, description
HAVING cnt > 1;
-- Should return 0 rows
```

### Verify Audit Trail
```sql
-- Check edit history tracked
SELECT 
  transaction_id,
  field_name,
  old_value,
  new_value,
  edited_at,
  edited_by
FROM transaction_edit_history
WHERE transaction_id = '?';
```

---

## CI/CD Integration

### Pre-merge Checks
```yaml
- name: F1 Automated Tests
  run: |
    pytest tests/f1/ -v --tb=short
    python -m coverage run --source=src/f1 -m pytest
    coverage report --fail-under=80
```

### Nightly Regression
```yaml
- name: F1 Regression Suite
  run: |
    pytest tests/f1/ -m regression -v
    pytest tests/f1/ -m load --load-users=50 --duration=600
```

---

**Test Plan Version:** 1.0
**Last Updated:** 2026-02-27
