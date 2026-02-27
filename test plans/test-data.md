# Test Data Specifications

## Overview
Sample test data for validating all features. Includes CSV files, transaction records, and expected outcomes.

---

## Bank CSV Formats

### Format 1: Chase Bank Standard
**Filename:** `test-chase-bank.csv`

```csv
Date,Description,Amount,Balance
01/15/2024,ACME CORP PAYMENT,1250.00,15400.00
01/16/2024,OFFICE DEPOT #2345,-45.67,15354.33
01/17/2024,AMAZON WEB SERVICES,-200.00,15154.33
01/18/2024,UBER TRIP,-23.50,15130.83
01/19/2024,STARBUCKS #1234,-8.45,15122.38
01/20/2024,CLIENT B INVOICE,3200.00,18322.38
```

**Expected Detection:**
- Date column: Date (MM/DD/YYYY)
- Description: Description
- Amount: Amount (positive = income, negative = expense)
- Balance: Balance

---

### Format 2: Bank of America (Debit/Credit Split)
**Filename:** `test-bofa.csv`

```csv
Date,Description,Debit,Credit,Balance
01/15/2024,ACME CORP PAYMENT,,1250.00,15400.00
01/16/2024,OFFICE DEPOT #2345,45.67,,15354.33
01/17/2024,AMAZON WEB SERVICES,200.00,,15154.33
01/18/2024,UBER TRIP,23.50,,15130.83
01/19/2024,CLIENT B INVOICE,,3200.00,18322.38
```

**Expected Detection:**
- Date column: Date (MM/DD/YYYY)
- Description: Description
- Amount: Split columns (Debit/Credit)
- Balance: Balance

---

### Format 3: Wells Fargo (European Date)
**Filename:** `test-wells-fargo-eu.csv`

```csv
Date,Description,Amount
15/01/2024,ACME CORP PAYMENT,1250.00
16/01/2024,OFFICE DEPOT #2345,-45.67
17/01/2024,AMAZON WEB SERVICES,-200.00
18/01/2024,UBER TRIP,-23.50
19/01/2024,CLIENT B INVOICE,3200.00
```

**Expected Detection:**
- Date format: DD/MM/YYYY
- Description: Description
- Amount: Amount (signed)

---

### Format 4: Citi (No Headers)
**Filename:** `test-citi-no-headers.csv`

```csv
01/15/2024,ACME CORP PAYMENT,1250.00,15400.00
01/16/2024,OFFICE DEPOT #2345,-45.67,15354.33
01/17/2024,AMAZON WEB SERVICES,-200.00,15154.33
01/18/2024,UBER TRIP,-23.50,15130.83
01/19/2024,CLIENT B INVOICE,3200.00,18322.38
```

**Expected Detection:**
- No headers detected
- Requires manual column assignment
- 4 columns: Date, Description, Amount, Balance

---

### Format 5: Capital One (Extra Columns)
**Filename:** `test-capital-one.csv`

```csv
Transaction Date,Post Date,Description,Category,Type,Amount
01/15/2024,01/16/2024,ACME CORP PAYMENT,Income,Credit,1250.00
01/16/2024,01/17/2024,OFFICE DEPOT #2345,Shopping,Debit,-45.67
01/17/2024,01/18/2024,AMAZON WEB SERVICES,Business,Debit,-200.00
01/18/2024,01/19/2024,UBER TRIP,Travel,Debit,-23.50
```

**Expected Detection:**
- Date: Transaction Date (use earliest)
- Description: Description
- Amount: Amount
- Ignore: Post Date, Category, Type

---

## Edge Case Files

### File: Empty CSV
**Filename:** `test-empty.csv`

```csv
```
(0 bytes)

**Expected Behavior:** Error - "File is empty"

---

### File: Corrupted Encoding
**Filename:** `test-corrupted.csv`

```csv
Date,Description,Amount
01/15/2024,ACME CORP <garbled>,1250.00
```
(with BOM issues or invalid UTF-8)

**Expected Behavior:** Error with specific row flagged

---

### File: Invalid Data Types
**Filename:** `test-invalid-data.csv`

```csv
Date,Description,Amount
invalid_date,ACME CORP,1250.00
01/16/2024,OFFICE DEPOT,not_a_number
01/17/2024,,200.00
01/18/2024,AMAZON WEB SERVICES,-200.00
```

**Expected Behavior:**
- Row 1: Date error flagged
- Row 2: Amount error flagged  
- Row 3: Missing description flagged
- Row 4: Valid, no error

---

### File: Duplicate Transactions
**Filename:** `test-duplicates.csv`

```csv
Date,Description,Amount
01/15/2024,ACME CORP PAYMENT,1250.00
01/15/2024,ACME CORP PAYMENT,1250.00
01/16/2024,OFFICE DEPOT,-45.67
01/16/2024,OFFICE DEPOT,-45.67
01/17/2024,AMAZON WEB SERVICES,-200.00
```

**Expected Detection:**
- Rows 1&2: Duplicate pair (same date, amount, description)
- Rows 3&4: Duplicate pair
- Row 5: Unique

---

### File: Large File (10k rows)
**Filename:** `test-large-10k.csv`

Generated with 10,000 rows of synthetic data.

**Expected Performance:**
- Upload: < 10 seconds
- Detection: < 2 seconds
- Preview: < 2 seconds

---

## Transaction Data Sets

### Dataset A: Small Business (3 months)
**Purpose:** Standard testing dataset

| Customer/Supplier | Transactions | Total Revenue/Expense |
|------------------|--------------|---------------------|
| ACME Corp | 12 | $45,000 |
| Client B | 8 | $28,000 |
| Client C | 5 | $15,000 |
| AWS | 3 | $2,400 |
| Office Depot | 6 | $890 |
| Starbucks | 45 | $450 |
| Uber | 28 | $840 |
| Adobe | 3 | $1,200 |

**Total Revenue:** $88,000
**Total Expenses:** $35,000
**Net:** +$53,000

---

### Dataset B: Seasonal Business (12 months)
**Purpose:** Trend and forecasting tests

**Pattern:**
- Q1: Low season ($15k revenue, $12k expenses)
- Q2: Medium ($25k revenue, $18k expenses)
- Q3: High season ($45k revenue, $22k expenses)
- Q4: Holiday spike ($55k revenue, $30k expenses)

**Total Revenue:** $140,000
**Total Expenses:** $82,000

**Expected AI Detection:**
- Seasonal pattern recognized
- Q3 identified as peak
- November spike not flagged as anomaly

---

### Dataset C: High Concentration Risk
**Purpose:** Customer concentration tests

| Customer | Revenue | Percentage |
|----------|---------|------------|
| ACME Corp | $80,000 | 80% |
| Client B | $10,000 | 10% |
| Client C | $5,000 | 5% |
| Others | $5,000 | 5% |

**Expected Alert:**
- Customer concentration risk: ACME Corp = 80%
- Threshold exceeded (typically 40-50%)

---

### Dataset D: Recurring Payments Pattern
**Purpose:** Recurring detection tests

**Subscriptions:**
- AWS: Monthly, $180-320 (varies by usage)
- Adobe Creative Cloud: Monthly, $52.99 (fixed)
- Office Rent: Monthly, $2,500 (fixed)
- Internet: Monthly, $89.99 (fixed)
- G Suite: Monthly, $12/user × 5 = $60 (fixed)

**Expected Detection:**
- All 5 subscriptions detected
- Fixed amounts: >95% confidence
- Variable (AWS): >85% confidence with range detection

---

### Dataset E: Anomaly Scenarios
**Purpose:** Anomaly detection tests

**Baseline:** Office Supplies avg = $200/month

**Test Case:**
- Jan: $180
- Feb: $220
- Mar: $195
- Apr: $800 (spike - 300% above baseline)

**Expected Detection:**
- April flagged as spending spike
- 300% increase detected
- Alert triggered

---

## Multi-Currency Data

### Dataset F: USD + EUR Transactions
**Purpose:** Multi-currency tests

```
USD Transactions:
- Revenue: $50,000
- Expenses: $30,000

EUR Transactions:
- Revenue: €20,000
- Expenses: €15,000

Exchange Rate: 1 EUR = 1.10 USD
```

**Expected Totals:**
- Total Revenue: $50,000 + $22,000 = $72,000
- Total Expenses: $30,000 + $16,500 = $46,500

---

## Tagged Transactions Sample

### For Tag Filtering Tests:

| Transaction | Amount | Tags |
|-------------|--------|------|
| ACME Project A | $5,000 | Q1-2024, Priority, Client-A |
| Software License | $1,200 | Q1-2024, Software, Tax-Deductible |
| Marketing Campaign | $3,500 | Q1-2024, Marketing |
| ACME Project B | $8,000 | Q2-2024, Priority, Client-A |
| AWS Services | $450 | Q2-2024, Infrastructure |

**Filter Tests:**
- Filter "Q1-2024": 3 transactions, $9,700 total
- Filter "Client-A": 2 transactions, $13,000 total
- Filter "Tax-Deductible": 1 transaction, $1,200 total

---

## Expected Entity Mappings

### Vendor Name Variations (for learning tests):

| Raw Description | Expected Entity | Expected Type |
|-------------------|-----------------|---------------|
| ACME Corp Payment | ACME Corp | Customer |
| ACME Corporation | ACME Corp | Customer |
| ACME | ACME Corp | Customer |
| AMZN MKTP | Amazon | Supplier |
| Amazon.com | Amazon | Supplier |
| Amazon Prime | Amazon | Supplier |
| SQ *COFFEE SHOP | Starbucks | Supplier |
| Starbucks #1234 | Starbucks | Supplier |
| Starbucks Store 1234 | Starbucks | Supplier |
| UBER TRIP | Uber | Supplier |
| Uber Technologies | Uber | Supplier |
| AWS EMEA | Amazon Web Services | Supplier |
| Amazon Web Services | Amazon Web Services | Supplier |

---

## Category Mappings

### Expected Auto-Categorization:

| Description | Expected Category |
|-------------|-------------------|
| AWS Invoice | Software/Tech |
| Adobe Subscription | Software/Tech |
| Office Depot | Office Expenses |
| Staples Purchase | Office Expenses |
| Starbucks | Meals & Entertainment |
| Restaurant Name | Meals & Entertainment |
| Uber | Travel & Transport |
| Gas Station | Travel & Transport |
| Client Dinner | Meals & Entertainment |
| Software License | Software/Tech |
| Legal Services | Professional Services |
| Marketing Agency | Marketing |

---

## Test Data Generation

### Script: generate_test_csv.py
```python
def generate_test_csv(filename, rows=100, pattern='standard'):
    """Generate synthetic transaction data"""
    import csv
    import random
    from datetime import datetime, timedelta
    
    vendors = ['ACME Corp', 'Client B', 'AWS', 'Office Depot', 
               'Starbucks', 'Uber', 'Adobe']
    
    with open(filename, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Date', 'Description', 'Amount'])
        
        for i in range(rows):
            date = datetime(2024, 1, 1) + timedelta(days=i)
            vendor = random.choice(vendors)
            amount = round(random.uniform(-500, 2000), 2)
            
            writer.writerow([
                date.strftime('%m/%d/%Y'),
                f'{vendor} Transaction',
                amount
            ])
```

---

## Data Validation Checksums

For automated verification:

| File | MD5 Checksum | Row Count | Total Amount |
|------|--------------|-----------|--------------|
| test-chase-bank.csv | (to be generated) | 6 | $4,172.76 |
| test-bofa.csv | (to be generated) | 5 | $4,172.76 |
| test-large-10k.csv | (to be generated) | 10,000 | ~$5M |
| test-duplicates.csv | (to be generated) | 5 | $2,109.33 |

---

**Test Data Version:** 1.0
**Last Updated:** 2026-02-27
**Generated By:** Test Data Management Script v1.0
