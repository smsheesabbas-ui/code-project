# Feature 2: Business Entity Structuring Layer - Human Test Plan

## Overview
Tests for AI entity recognition, revenue/expense mapping, tagging, and entity dashboards.

---

## EPIC 1: Intelligent Entity Recognition

### Test Case F2-E1-S1.1: AI Suggests Customer from Transaction

**Objective:** Verify AI identifies customer from transaction description

**Preconditions:**
- Transactions imported with descriptions like "ACME Corp Payment Received"
- Feature 1 data import completed

**Steps:**
1. Navigate to Transactions page
2. Review transaction with "ACME Corp Payment Received"
3. Observe Entity column

**Expected Results:**
- Entity column shows "ACME Corp" as suggested customer
- Confidence score displayed (e.g., "92%")
- Visual indicator shows AI suggestion (e.g., lightbulb icon)
- Suggestion marked as "New Entity" if not previously seen

**Pass Criteria:**
- Customer name extracted from description
- Confidence score ≥85% for clear cases
- Visual distinction between AI suggestion vs confirmed entity

---

### Test Case F2-E1-S1.2: AI Suggests Supplier from Transaction

**Objective:** Verify AI identifies supplier from expense transactions

**Preconditions:**
- Expense transactions imported (negative amounts or marked as expense)

**Steps:**
1. Review expense transaction: "Amazon Web Services - Invoice #1234"
2. Observe Entity column

**Expected Results:**
- "Amazon Web Services" suggested as supplier
- Entity type indicated as "Supplier"
- Confidence score displayed

**Pass Criteria:**
- Supplier correctly identified from expense
- Entity type classification accurate

---

### Test Case F2-E1-S1.3: Entity Creation on Confirmation

**Objective:** Verify new entity created when user confirms AI suggestion

**Preconditions:**
- Transaction with AI-suggested entity visible

**Steps:**
1. Click on AI-suggested entity "ACME Corp"
2. Click "Confirm" button
3. Navigate to Entities page
4. Search for "ACME Corp"

**Expected Results:**
- "ACME Corp" appears in Entities list
- Entity type set to "Customer"
- First seen date recorded
- Transaction count: 1
- Total revenue from this entity displayed

**Pass Criteria:**
- Entity persisted to database
- Transaction linked to entity
- Entity dashboard data correct

---

### Test Case F2-E1-S1.4: Ambiguous Entity Handling

**Objective:** Verify handling of unclear or abbreviated entity names

**Preconditions:**
- Transactions with abbreviated descriptions (e.g., "AMZN MKTP", "SQ *COFFEE SHOP")

**Steps:**
1. Review transaction with "AMZN MKTP"
2. Observe AI suggestion
3. Review confidence score

**Expected Results:**
- Low confidence score (<70%) shown for ambiguous cases
- "Unsure" indicator displayed
- User prompted to manually confirm/correct

**Pass Criteria:**
- Low confidence flagged for user review
- No incorrect high-confidence suggestions

---

### Test Case F2-E1-S2.1: Manual Entity Edit

**Objective:** Verify user can override AI entity suggestion

**Preconditions:**
- Transaction with AI-suggested entity

**Steps:**
1. Click on AI-suggested entity name
2. Click "Edit"
3. Type different entity name: "ACME Corporation"
4. Select from existing entities dropdown OR create new
5. Save changes

**Expected Results:**
- Entity field editable
- Dropdown shows existing entities for search/selection
- "Create New" option available
- Changes saved immediately
- AI learns from correction (future similar transactions map to new entity)

**Pass Criteria:**
- Manual override works
- New entity creation functional
- Changes persist

---

### Test Case F2-E1-S2.2: Entity Merge Handling

**Objective:** Verify system handles same entity with different names

**Preconditions:**
- Multiple transactions for same entity with variations:
  - "ACME Corp"
  - "ACME Corporation"
  - "Acme Corp"

**Steps:**
1. Review all three transactions
2. Edit "ACME Corporation" to match "ACME Corp"
3. Merge entities
4. Review combined entity

**Expected Results:**
- All transactions now linked to single entity
- Historical transactions updated
- Total revenue reflects all payments
- Merge action logged

**Pass Criteria:**
- Merge operation succeeds
- Data integrity maintained
- No orphaned records

---

### Test Case F2-E1-S3.1: System Learns from Corrections

**Objective:** Verify AI improves after user corrections

**Preconditions:**
- User previously corrected "AMZN" → "Amazon"
- New transaction arrives with "AMZN Purchase"

**Steps:**
1. Wait for new transaction import
2. Review entity suggestion for "AMZN Purchase"

**Expected Results:**
- System now suggests "Amazon" instead of "AMZN"
- Higher confidence score than initial suggestion
- Learning indicator: "Based on your previous correction"

**Pass Criteria:**
- Correction remembered
- Similar transactions classified correctly
- Confidence improves over time

---

## EPIC 2: Revenue & Expense Structuring

### Test Case F2-E2-S2.1: Map Revenue to Stream

**Objective:** Verify revenue transactions map to revenue streams

**Preconditions:**
- Revenue transactions imported
- Default revenue streams exist (or user created)

**Steps:**
1. Review revenue transaction
2. Observe Revenue Stream column
3. Click to edit stream assignment

**Expected Results:**
- AI suggests revenue stream (e.g., "Consulting", "Product Sales")
- Default streams available: "General Revenue", "Services", "Products"
- User can create custom stream
- Monthly breakdown visible per stream

**Pass Criteria:**
- Revenue stream assignment works
- Custom streams creatable
- Totals calculated correctly

---

### Test Case F2-E2-S2.2: Map Expense to Category

**Objective:** Verify expense transactions categorize correctly

**Preconditions:**
- Expense transactions imported

**Steps:**
1. Review expense transaction: "AWS Invoice"
2. Observe Expense Category
3. Review other expenses

**Expected Results:**
- "AWS Invoice" categorized as "Software/Tech"
- "Office Supplies" categorized as "Office Expenses"
- AI categories have ≥85% accuracy
- Categories editable by user

**Pass Criteria:**
- Common expenses categorized correctly
- Category totals accurate
- Trends visible

---

### Test Case F2-E2-S2.3: Multi-Purpose Vendor Handling

**Objective:** Verify same vendor can have different categories

**Preconditions:**
- Transactions from same vendor in different contexts:
  - "Amazon - Office Supplies"
  - "Amazon - Software Purchase"

**Steps:**
1. Review both transactions
2. Observe category assignments
3. Verify they can differ

**Expected Results:**
- Transaction 1: Category = "Office Expenses"
- Transaction 2: Category = "Software/Tech"
- Same vendor, different categories allowed
- AI suggests based on description, not just vendor

**Pass Criteria:**
- Context-aware categorization works
- Same vendor split across categories

---

### Test Case F2-E2-S3.1: Add Custom Tags

**Objective:** Verify custom tagging functionality

**Preconditions:**
- Transactions imported

**Steps:**
1. Click "Add Tags" on a transaction
2. Type new tag: "Q1-Project"
3. Press Enter
4. Add second tag: "Tax-Deductible"
5. Save

**Expected Results:**
- Tags displayed as chips on transaction
- Multiple tags allowed per transaction
- Tags searchable in filter
- Tag colors auto-assigned

**Pass Criteria:**
- Tag creation works
- Multiple tags persist
- Visual display correct

---

### Test Case F2-E2-S3.2: Filter by Tags

**Objective:** Verify tag-based filtering

**Preconditions:**
- Multiple transactions with different tags

**Steps:**
1. Navigate to Transactions page
2. Click "Filter"
3. Select tag: "Tax-Deductible"
4. Apply filter

**Expected Results:**
- Only transactions with "Tax-Deductible" tag displayed
- Filter pill shows active filter
- "Clear Filters" option available
- Tag count shown (e.g., "Tax-Deductible (12)")

**Pass Criteria:**
- Filter works correctly
- Results accurate
- Clear filter works

---

### Test Case F2-E2-S3.3: Tag-Based Reporting

**Objective:** Verify reports can be filtered by tags

**Preconditions:**
- Transactions with tags
- Expense report accessed

**Steps:**
1. Navigate to Expense Report
2. Apply tag filter: "Q1-Project"
3. Review totals

**Expected Results:**
- Report shows only Q1-Project expenses
- Total recalculated based on filter
- Visual indicator shows filter active

**Pass Criteria:**
- Tag filter applied to reports
- Totals update correctly

---

## EPIC 3: Entity Dashboards

### Test Case F2-E3-S1.1: Display Top 5 Customers

**Objective:** Verify top customers ranked by revenue

**Preconditions:**
- Multiple customers with transactions over time period

**Steps:**
1. Navigate to Dashboard
2. Scroll to "Top Customers" section
3. Review list

**Expected Results:**
- 5 customers displayed max (limit to reduce clutter)
- Ranked by total revenue (highest first)
- Each shows:
  - Customer name
  - Total revenue amount
  - Percentage of total revenue
  - Transaction count
- Time period selector available (This Month, Last 3 Months, This Year)

**Pass Criteria:**
- Ranking correct
- Percentages sum to ≤100%
- Math accurate

---

### Test Case F2-E3-S1.2: Customer Drill-Down

**Objective:** Verify clicking customer shows transaction history

**Preconditions:**
- Top customers displayed

**Steps:**
1. Click on customer "ACME Corp" in Top Customers list
2. Review detail view

**Expected Results:**
- Customer detail page opens
- All transactions for ACME Corp listed
- Total revenue displayed
- Average transaction size
- Payment trend over time
- "Back to Dashboard" button

**Pass Criteria:**
- Drill-down navigation works
- Data accurate
- All transactions shown

---

### Test Case F2-E3-S2.1: Display Top 5 Suppliers

**Objective:** Verify top suppliers ranked by expense

**Preconditions:**
- Multiple suppliers with expense transactions

**Steps:**
1. Navigate to Dashboard
2. Scroll to "Top Suppliers" section
3. Review list

**Expected Results:**
- 5 suppliers displayed max
- Ranked by total expense (highest first)
- Each shows:
  - Supplier name
  - Total expense amount
  - Percentage of total expenses
  - Transaction count
- Time period selector available

**Pass Criteria:**
- Ranking correct
- Expense totals accurate

---

### Test Case F2-E3-S3.1: Revenue Breakdown Summary

**Objective:** Verify revenue breakdown by stream

**Preconditions:**
- Revenue streams configured
- Transactions mapped to streams

**Steps:**
1. Navigate to Dashboard
2. View Revenue Summary panel
3. Review breakdown

**Expected Results:**
- Total revenue for selected period displayed
- Breakdown by revenue stream shown
- Top stream highlighted
- Comparison to previous period shown (e.g., "+12% vs last month")
- Visual chart (pie or bar) available

**Pass Criteria:**
- Totals correct
- Breakdown percentages accurate
- Comparison math correct

---

### Test Case F2-E3-S3.2: Expense Breakdown Summary

**Objective:** Verify expense breakdown by category

**Preconditions:**
- Expense categories configured
- Transactions categorized

**Steps:**
1. Navigate to Dashboard
2. View Expense Summary panel
3. Review breakdown

**Expected Results:**
- Total expenses for selected period
- Breakdown by category shown
- Top expense category highlighted
- Comparison to previous period
- Visual chart available

**Pass Criteria:**
- Totals correct
- Categories accurate
- No accounting jargon used

---

### Test Case F2-E3-S3.3: Time Period Filtering

**Objective:** Verify dashboard updates with time period change

**Preconditions:**
- Dashboard with data displayed

**Steps:**
1. Note current dashboard values
2. Click time period dropdown
3. Select "Last 3 Months"
4. Observe updates
5. Select "Custom Range"
6. Set specific dates
7. Apply

**Expected Results:**
- All dashboard panels update immediately
- Top Customers/Suppliers recalculated for period
- Revenue/Expense totals recalculated
- Charts update
- URL reflects filter (for sharing/bookmarking)

**Pass Criteria:**
- All components update on period change
- Data accurate for selected period
- Performance <2 seconds

---

## Cross-Cutting Tests

### Test Case F2-CROSS-001: Mobile Entity Management

**Objective:** Verify entity features work on mobile

**Preconditions:**
- Mobile device or emulator
- Transactions imported

**Steps:**
1. Open app on mobile
2. Navigate to Transactions
3. Edit an entity
4. View Entity Dashboard
5. Add tags

**Expected Results:**
- All features accessible
- Touch targets adequate (44px+)
- Horizontal scroll for tables if needed
- No horizontal overflow

**Pass Criteria:**
- Usable on mobile
- No layout breaks

---

### Test Case F2-CROSS-002: No Accounting Jargon

**Objective:** Verify UI uses plain language

**Preconditions:**
- Full feature access

**Steps:**
1. Review all UI text
2. Check for accounting terms

**Expected Results:**
- No terms: "chart of accounts", "debit", "credit", "ledger", "journal entry"
- Use instead: "customers", "suppliers", "money in", "money out"
- All text understandable to non-accountant

**Pass Criteria:**
- Zero accounting jargon
- Plain language throughout

---

## Regression Test Checklist

Execute these when modifying F2 code:

- [ ] F2-E1-S1.1: Customer entity detection
- [ ] F2-E1-S1.2: Supplier entity detection
- [ ] F2-E1-S2.1: Manual entity edit
- [ ] F2-E1-S3.1: Learning from corrections
- [ ] F2-E2-S2.1: Revenue stream mapping
- [ ] F2-E2-S2.2: Expense categorization
- [ ] F2-E2-S3.1: Custom tags
- [ ] F2-E3-S1.1: Top customers display
- [ ] F2-E3-S2.1: Top suppliers display
- [ ] F2-E3-S3.3: Time period filtering
- [ ] F2-CROSS-002: No jargon check

---

**Test Plan Version:** 1.0
**Last Updated:** 2026-02-27
