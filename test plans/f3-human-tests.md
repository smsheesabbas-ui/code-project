# Feature 3: AI Financial Intelligence Engine - Human Test Plan

## Overview
Tests for AI classification, pattern detection, risk detection, forecasting, and insight generation.

---

## EPIC 1: Smart Classification & Pattern Detection

### Test Case F3-E1-S1.1: Auto-Classify New Transactions

**Objective:** Verify AI automatically categorizes new transactions

**Preconditions:**
- Transactions imported (Feature 1 complete)
- Entities mapped (Feature 2 complete)
- New transactions added

**Steps:**
1. Import new batch of transactions
2. Navigate to Transactions page
3. Review AI classifications

**Expected Results:**
- Transactions show AI-suggested:
  - Entity (customer/supplier)
  - Revenue stream or expense category
  - Custom tags
- Confidence score displayed (target ≥85%)
- Visual indicator for AI suggestions
- Option to correct manually

**Pass Criteria:**
- ≥85% of clear transactions classified correctly
- Confidence score visible
- Suggestions reasonable

---

### Test Case F3-E1-S1.2: Classification Confidence Display

**Objective:** Verify confidence scores help users trust/reject suggestions

**Preconditions:**
- Transactions with varying confidence levels

**Steps:**
1. Review high-confidence classification (>90%)
2. Review medium-confidence (70-85%)
3. Review low-confidence (<70%)

**Expected Results:**
- High: Green indicator, "High confidence"
- Medium: Yellow indicator, "Check suggested category"
- Low: Red/orange indicator, "Please review"
- Low confidence items require user confirmation before finalizing

**Pass Criteria:**
- Confidence levels visually distinct
- Appropriate thresholds trigger review prompts

---

### Test Case F3-E1-S2.1: Detect Recurring Payments

**Objective:** Verify AI identifies recurring/subscription payments

**Preconditions:**
- 3+ months of transaction history
- Known recurring transactions (e.g., AWS monthly, Rent, Software subscriptions)

**Steps:**
1. Navigate to Insights > Recurring Payments
2. Review detected patterns
3. Compare to known subscriptions

**Expected Results:**
- Recurring payments listed with:
  - Vendor name
  - Amount (with variation tolerance ±10%)
  - Frequency (Monthly, Weekly, Quarterly)
  - Next expected date
  - 12-month total
- Actual recurring payments detected with ≥85% accuracy

**Pass Criteria:**
- Known subscriptions detected
- Frequency identified correctly
- Variations handled (e.g., AWS bill varies by usage)

---

### Test Case F3-E1-S2.2: Recurring Payment Alerts on Change

**Objective:** Verify alerts when recurring amounts change significantly

**Preconditions:**
- Recurring payment established (e.g., "AWS", $200/month)
- New month with different amount (e.g., $350)

**Steps:**
1. Import new month with increased AWS charge
2. Navigate to Dashboard or Alerts
3. Review notification

**Expected Results:**
- Alert: "Your AWS payment increased 75% this month ($200 → $350)"
- Option to view details
- Option to dismiss/mark as expected

**Pass Criteria:**
- Significant changes flagged
- Alert includes percentage and absolute change
- User can acknowledge

---

### Test Case F3-E1-S3.1: Identify Spending Trends

**Objective:** Verify AI detects spending patterns over time

**Preconditions:**
- 6+ months of categorized expense data

**Steps:**
1. Navigate to Insights > Spending Trends
2. Review category trends
3. Look for rising/falling indicators

**Expected Results:**
- Top 3 categories with significant change highlighted
- Trend arrows (↗ rising, ↘ falling, → stable)
- Percentage change vs previous period
- Visual chart showing trend over 12 months
- Plain language insight: "Software expenses increased 23% over 3 months"

**Pass Criteria:**
- Real trends detected
- False positives minimized
- Visualization clear

---

### Test Case F3-E1-S3.2: Seasonal Trend Handling

**Objective:** Verify AI doesn't flag seasonal variations as anomalies

**Preconditions:**
- Year+ of data with clear seasonal pattern (e.g., holiday sales spike, summer slowdown)

**Steps:**
1. Review insights during seasonal spike period
2. Check if flagged as anomaly

**Expected Results:**
- Seasonal patterns recognized as normal
- Not flagged as unusual spending spike
- Comparison made to same period previous year (if available)

**Pass Criteria:**
- Seasonal patterns learned
- False alerts minimized

---

## EPIC 2: Risk & Anomaly Detection

### Test Case F3-E2-S1.1: Detect Unusual Spending Spikes

**Objective:** Verify AI flags unusual expense increases

**Preconditions:**
- Baseline spending established in a category
- New transaction significantly exceeds baseline

**Steps:**
1. Normal monthly "Office Supplies" ~$200
2. Import month with $800 "Office Supplies" charge
3. Navigate to Dashboard or Alerts

**Expected Results:**
- Alert: "Office Supplies spending increased 300% this month"
- Alert includes trend comparison to previous 3 months
- Visual indicator on dashboard (red dot or banner)
- Click for details: breakdown of what drove the increase

**Pass Criteria:**
- True anomalies detected (≥90% accuracy)
- Alert includes context
- Actionable information provided

---

### Test Case F3-E2-S1.2: False Positive Minimization

**Objective:** Verify legitimate one-time purchases not flagged

**Preconditions:**
- One-time large purchase (e.g., laptop, annual conference)

**Steps:**
1. Import one-time $2000 "Equipment" purchase
2. Review alerts

**Expected Results:**
- NOT flagged as anomaly if "Equipment" category has history of one-time large purchases
- OR flagged with context: "One-time equipment purchase - expected variation"

**Pass Criteria:**
- Category history considered
- False positive rate < 10%

---

### Test Case F3-E2-S2.1: Flag Revenue Drops

**Objective:** Verify AI detects revenue decline vs previous periods

**Preconditions:**
- Multiple months of revenue data
- Recent month with lower revenue

**Steps:**
1. Review Dashboard revenue summary
2. Check for alerts

**Expected Results:**
- Alert if revenue drops >20% vs previous period
- Alert includes:
  - "Revenue down 25% vs last month"
  - Affected revenue streams
  - Affected customers (if concentrated)
  - Plain language explanation

**Pass Criteria:**
- Significant drops detected
- Root cause analysis provided (which streams/customers)

---

### Test Case F3-E2-S2.2: Seasonal Revenue Drop Handling

**Objective:** Verify seasonal revenue dips not flagged as concerning

**Preconditions:**
- Year+ of data with seasonal revenue pattern

**Steps:**
1. Review insights during known slow season

**Expected Results:**
- Comparison to same period last year
- Alert only if down vs prior year, not vs busy season
- Context provided: "Winter revenue typically lower - within expected range"

**Pass Criteria:**
- Seasonal context considered
- Appropriate baseline used for comparison

---

### Test Case F3-E2-S3.1: Customer Concentration Risk Alert

**Objective:** Verify AI warns when business relies too heavily on one customer

**Preconditions:**
- Revenue data where one customer >50% of total

**Steps:**
1. Navigate to Dashboard
2. View Risk Alerts section
3. Review customer concentration warning

**Expected Results:**
- Alert: "Customer 'ACME Corp' represents 65% of your revenue"
- Risk level indicator (High/Medium/Low)
- Threshold: Alert when single customer >40% (configurable)
- Actionable advice: "Consider diversifying your customer base"
- Option to adjust threshold in settings

**Pass Criteria:**
- Concentration calculated correctly
- Alert threshold respected
- Advice relevant and actionable

---

### Test Case F3-E2-S3.2: New Customer Sudden Large Payment

**Objective:** Verify handling of new large customer (not immediately flagged as risk)

**Preconditions:**
- New customer with single large payment making up large % of monthly revenue

**Steps:**
1. Review dashboard after new customer payment

**Expected Results:**
- If first month with new customer: No concentration risk alert
- Dashboard notes: "New high-value customer - monitor trend"
- Alert triggers if pattern continues 3+ months

**Pass Criteria:**
- New customer exception handled
- Alert triggers appropriately after pattern establishes

---

## EPIC 3: Forecasting & Insight Generation

### Test Case F3-E3-S1.1: Generate 30-Day Cashflow Projection

**Objective:** Verify 30-day cashflow forecast accuracy

**Preconditions:**
- 3+ months of transaction history
- Mix of income and expenses

**Steps:**
1. Navigate to Insights > Cashflow Forecast
2. Review 30-day projection
3. Compare actual results after 30 days

**Expected Results:**
- Projection shows:
  - Current cash position
  - Predicted low point in next 30 days
  - Predicted high point
  - Confidence interval (range)
- Visual timeline with projected curve
- Alert if predicted to go below threshold

**Pass Criteria:**
- Forecast generated without errors
- Actual cashflow within predicted range ≥80% of time
- Alert threshold triggers correctly

---

### Test Case F3-E3-S1.2: Cashflow Risk Alert

**Objective:** Verify alerts when forecast predicts cash shortfall

**Preconditions:**
- Cashflow forecast predicts low balance below threshold

**Steps:**
1. Review cashflow forecast
2. Check for risk alerts

**Expected Results:**
- Alert: "You may run low on cash in 12 days"
- Alert includes:
  - Projected low amount
  - Date of projected low
  - Contributing factors (upcoming large expenses, revenue drop)
  - Suggested actions ("Consider collecting outstanding invoices")

**Pass Criteria:**
- Risk alert triggered appropriately
- Suggestion actionable
- Date prediction reasonable

---

### Test Case F3-E3-S2.1: Weekly AI Business Summary

**Objective:** Verify weekly summary generated and delivered

**Preconditions:**
- Weekly summary enabled in settings
- Week of transaction data available

**Steps:**
1. Wait for weekly summary (or trigger manually)
2. Review summary on dashboard
3. Check email delivery (if configured)

**Expected Results:**
- Summary includes:
  - Week's total revenue vs previous week
  - Week's total expenses vs previous week
  - Top customer of the week
  - Top expense category
  - Notable trends or anomalies
  - Plain language recommendation
- Email formatted cleanly (not spam-like)
- Dashboard widget shows same content

**Pass Criteria:**
- Summary auto-generated weekly
- Content accurate
- Plain language used throughout

---

### Test Case F3-E3-S2.2: Weekly Summary - Empty Week

**Objective:** Verify summary handles weeks with no transactions

**Preconditions:**
- Week with zero transactions

**Steps:**
1. Review weekly summary for empty week

**Expected Results:**
- "No transactions this week" message
- Comparison to previous active period
- No errors or crashes

**Pass Criteria:**
- Graceful handling of empty data
- No system errors

---

### Test Case F3-E3-S3.1: Generate Actionable Recommendations

**Objective:** Verify AI provides specific, actionable advice

**Preconditions:**
- Sufficient data for pattern analysis

**Steps:**
1. Navigate to Insights > Recommendations
2. Review generated recommendations
3. Test different scenarios:
   - High customer concentration
   - Rising expense trend
   - Cashflow risk
   - Unused subscription detected

**Expected Results:**
- Recommendations specific to user's data:
  - "Customer ACME Corp is 60% of revenue. Consider finding new customers to diversify."
  - "Software expenses rose 30% in 3 months. Review your subscriptions."
  - "You may run low on cash in 15 days. Consider sending invoice reminders."
  - "You paid for Adobe subscription but haven't used it in 3 months. Consider canceling."
- Each recommendation has:
  - Clear explanation of why
  - Specific action to take
  - Mark as done / Dismiss options

**Pass Criteria:**
- Recommendations relevant to actual data
- Advice actionable (not generic)
- User can dismiss/done

---

### Test Case F3-E3-S3.2: Recommendation Relevance Over Time

**Objective:** Verify outdated recommendations removed or updated

**Preconditions:**
- Recommendation generated (e.g., "Expenses rising")
- User takes action or situation changes

**Steps:**
1. Note recommendation
2. Dismiss or mark done
3. Wait for data update or trigger refresh
4. Review recommendations

**Expected Results:**
- Dismissed recommendation disappears
- New recommendations appear based on current data
- Same issue not re-recommended immediately after dismissal

**Pass Criteria:**
- Dismissal persists
- Recommendations stay relevant

---

## Cross-Cutting Tests

### Test Case F3-CROSS-001: Response Time Under 3 Seconds

**Objective:** Verify AI features respond quickly

**Preconditions:**
- Large dataset (10k+ transactions)

**Steps:**
1. Request classification for batch of 100 transactions
2. Generate cashflow forecast
3. Load insights dashboard
4. Time each operation

**Expected Results:**
- All operations complete < 3 seconds
- Progress indicator for longer operations
- No browser timeout

**Pass Criteria:**
- 95% of requests < 3s
- p99 < 5s

---

### Test Case F3-CROSS-002: Plain Language Throughout

**Objective:** Verify no technical jargon in AI outputs

**Preconditions:**
- All AI features accessible

**Steps:**
1. Review all AI-generated text:
   - Classification labels
   - Trend descriptions
   - Recommendations
   - Alerts
2. Check for prohibited terms

**Expected Results:**
- No terms: "standard deviation", "regression", "variance", "correlation coefficient"
- Use instead: "typical range", "pattern", "trend", "connection"
- All insights explainable to non-technical user

**Pass Criteria:**
- Zero prohibited technical terms
- Language tested with non-technical users

---

## Regression Test Checklist

Execute when modifying F3 code:

- [ ] F3-E1-S1.1: Auto-classification accuracy
- [ ] F3-E1-S2.1: Recurring payment detection
- [ ] F3-E1-S3.1: Trend detection
- [ ] F3-E2-S1.1: Anomaly detection
- [ ] F3-E2-S3.1: Customer concentration risk
- [ ] F3-E3-S1.1: Cashflow forecast
- [ ] F3-E3-S2.1: Weekly summary generation
- [ ] F3-E3-S3.1: Actionable recommendations
- [ ] F3-CROSS-001: Response time
- [ ] F3-CROSS-002: Plain language

---

**Test Plan Version:** 1.0
**Last Updated:** 2026-02-27
