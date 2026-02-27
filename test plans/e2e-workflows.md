# End-to-End Workflow Tests

## Overview
Cross-feature integration tests that validate complete user journeys from data import to insight consumption.

---

## Workflow 1: First-Time User Onboarding

### Objective
Validate complete onboarding flow for new user from signup to first insight.

### Test Steps

#### Step 1: User Registration
**Features:** Auth (outside scope but prerequisite)
- Create new account
- Verify email
- Complete profile setup

#### Step 2: First CSV Import (F1)
1. Navigate to Import page
2. Upload `test-bank-statement.csv`
3. Verify column auto-detection (date, description, amount)
4. Preview first 20 rows
5. Confirm import
6. Verify 100 transactions saved

**Expected Results:**
- Import completes < 10 seconds
- Auto-detection confidence ≥85%
- Preview loads < 2 seconds
- All transactions visible in Transactions page

#### Step 3: Entity Recognition (F2)
1. Navigate to Transactions page
2. Review AI-suggested entities
3. Confirm 3 top customers
4. Confirm 2 top suppliers
5. Verify confidence scores ≥85%

**Expected Results:**
- ACME Corp identified as customer
- AWS identified as supplier
- All clear entities detected automatically

#### Step 4: Category Mapping (F2)
1. Review expense categories
2. Verify auto-categorization:
   - Software subscriptions → "Software/Tech"
   - Office purchases → "Office Expenses"
   - Client meals → "Meals & Entertainment"

**Expected Results:**
- ≥85% categorization accuracy
- Categories editable

#### Step 5: View Dashboard (F5)
1. Navigate to Dashboard
2. Verify KPIs:
   - Cash balance displayed
   - Revenue total accurate
   - Expense total accurate
   - Top 5 customers visible
   - Top 5 suppliers visible

**Expected Results:**
- Dashboard loads < 2 seconds
- All calculations accurate
- Charts render correctly

#### Step 6: AI Insights (F3)
1. Check for recurring payment detection
2. Review spending trends
3. Verify cashflow forecast generated
4. Check weekly summary available

**Expected Results:**
- Known subscriptions detected
- Trends identified
- Forecast accuracy ≥80%

#### Step 7: Conversational Query (F4)
1. Open chat interface
2. Ask: "What was my revenue last month?"
3. Verify response < 3 seconds
4. Ask follow-up: "Who is my top customer?"

**Expected Results:**
- Both queries answered correctly
- Context maintained
- Plain language used

### Success Criteria
- User completes onboarding in < 15 minutes
- No errors or blockers
- All 5 features functional
- Data flows correctly between features

---

## Workflow 2: Regular User - Weekly Review

### Objective
Validate typical weekly usage pattern for established user.

### Test Steps

#### Step 1: Import New Transactions (F1)
1. Upload new week's CSV
2. Handle any duplicate detection
3. Review and confirm import
4. Verify new transactions merged with existing

**Expected Results:**
- Duplicates correctly flagged
- New data imports successfully
- Transaction count updated

#### Step 2: Review AI Classifications (F2+F3)
1. Check new entity suggestions
2. Confirm or correct categorizations
3. Add tags to key transactions
4. Verify AI learned from any corrections

**Expected Results:**
- New vendors identified
- Categories accurate
- Corrections persisted

#### Step 3: Check Dashboard Updates (F5)
1. Verify dashboard reflects new data
2. Review trend changes
3. Check for new anomalies
4. Note any alerts

**Expected Results:**
- Dashboard auto-updated
- Trends recalculated
- New anomalies flagged

#### Step 4: Review Weekly Summary (F4)
1. Check email for weekly summary
2. Verify content accuracy
3. Click through to dashboard
4. Review recommended actions

**Expected Results:**
- Email delivered successfully
- Summary data accurate
- Links functional
- Recommendations relevant

#### Step 5: Ask Questions via Chat (F4)
1. "How did I do this week?"
2. "What should I focus on?"
3. Review AI recommendations

**Expected Results:**
- Questions understood
- Contextual responses
- Actionable insights

### Success Criteria
- Weekly review completes in < 10 minutes
- All data sources integrated
- Insights delivered automatically
- User can get answers conversationally

---

## Workflow 3: Risk Detection & Response

### Objective
Validate end-to-end risk detection and user notification flow.

### Test Steps

#### Step 1: Create Risk Condition
1. Import data showing:
   - Sudden 50% expense spike
   - Customer concentration >60%
   - Projected cash shortfall in 15 days

#### Step 2: AI Detection (F3)
1. Wait for AI processing
2. Verify anomaly detected
3. Verify customer concentration risk calculated
4. Verify cashflow forecast updated

**Expected Results:**
- Anomaly accuracy ≥90%
- Risk alerts generated
- Forecast reflects new data

#### Step 3: Dashboard Alerts (F5)
1. Navigate to Dashboard
2. Verify risk alerts displayed
3. Check alert severity indicators
4. Click alerts for details

**Expected Results:**
- All 3 risks visible
- Severity appropriate
- Details accessible

#### Step 4: Proactive Notification (F4)
1. Check email for risk alerts
2. Verify notification content
3. Click link to dashboard
4. Review recommended actions

**Expected Results:**
- Alerts delivered via email
- Content clear and actionable
- Deep links work

#### Step 5: Conversational Follow-up (F4)
1. Ask: "What risks should I worry about?"
2. Verify system explains all 3 risks
3. Ask: "What should I do about cashflow?"
4. Review recommendations

**Expected Results:**
- All risks explained
- Contextual advice provided
- Actions specific and actionable

#### Step 6: User Takes Action
1. Mark alerts as reviewed
2. Adjust cashflow alert threshold
3. Dismiss false positive anomaly
4. Verify preferences saved

**Expected Results:**
- Alert status updated
- Settings persisted
- Dashboard reflects dismissed items

### Success Criteria
- All risks detected automatically
- User notified via multiple channels
- Recommendations actionable
- User can manage alert preferences

---

## Workflow 4: Data Correction & Learning

### Objective
Validate system learns from user corrections.

### Test Steps

#### Step 1: Initial AI Suggestion (F2+F3)
1. Import transactions with ambiguous vendor
2. Note AI suggestion: "AMZN" → entity unknown, confidence 45%
3. Note categorization: "Unknown Category", confidence 40%

#### Step 2: User Correction (F2)
1. Edit transaction
2. Set entity to "Amazon"
3. Set category to "Software/Tech"
4. Add tag "Subscription"
5. Save

#### Step 3: Verify Learning Recorded
1. Check correction logged in system
2. Verify training signal stored
3. Trigger model update (or wait for batch)

#### Step 4: Test Similar Transaction (F2+F3)
1. Import new transaction: "AMZN Prime Membership"
2. Verify new AI suggestion: "Amazon", confidence >70%
3. Verify category: "Software/Tech", confidence >70%

**Expected Results:**
- System learned from correction
- Similar transactions classified better
- Confidence improved

#### Step 5: Dashboard Updates (F5)
1. Verify entity now appears in Top Suppliers
2. Check category breakdown updated
3. Review tag-based reports

### Success Criteria
- Correction recorded
- Learning applied
- Future accuracy improved
- Dashboard reflects changes

---

## Workflow 5: Multi-Period Analysis

### Objective
Validate user can analyze trends across multiple time periods.

### Test Steps

#### Step 1: Historical Data Setup
1. Import 12 months of historical data
2. Verify data for each month accurate

#### Step 2: Period Comparison via Dashboard (F5)
1. Set dashboard to "This Year"
2. Note annual totals
3. Change to "Last 6 Months"
4. Verify recalculation
5. Change to "Q1 Only"
6. Verify quarterly data

**Expected Results:**
- All periods calculate correctly
- Trends update appropriately
- Charts adjust to period

#### Step 3: Period Comparison via Chat (F4)
1. Ask: "How did Q1 compare to Q2?"
2. Verify response includes both quarters
3. Ask: "What about vs last year?"
4. Verify year-over-year comparison

**Expected Results:**
- Time periods correctly parsed
- Comparisons accurate
- Context maintained across queries

#### Step 4: Trend Analysis (F3)
1. Review AI-detected trends
2. Verify seasonal patterns recognized
3. Check 30-day forecast uses full history

**Expected Results:**
- Trends accurate
- Seasonality handled
- Forecast uses historical patterns

### Success Criteria
- Multi-period analysis accurate
- Comparisons correct
- Trends detected
- Forecasts leverage history

---

## Workflow 6: Mobile User Journey

### Objective
Validate complete workflow works on mobile devices.

### Test Steps

#### Step 1: Mobile Import (F1)
1. Access app on mobile browser
2. Upload CSV from mobile
3. Complete column detection
4. Preview and confirm

**Expected Results:**
- Upload works on mobile
- UI responsive
- No layout issues

#### Step 2: Mobile Entity Review (F2)
1. Review AI suggestions
2. Confirm/correct entities
3. Add tags

**Expected Results:**
- Touch targets adequate
- Forms usable
- Data saves correctly

#### Step 3: Mobile Dashboard (F5)
1. View dashboard
2. Scroll through sections
3. Interact with charts
4. Apply filters

**Expected Results:**
- Single column layout
- Charts responsive
- Filters accessible
- Performance < 3s

#### Step 4: Mobile Chat (F4)
1. Open chat interface
2. Ask questions
3. Review responses

**Expected Results:**
- Chat UI responsive
- Keyboard doesn't obscure input
- Responses display correctly

### Success Criteria
- All features usable on mobile
- Performance acceptable
- Touch-friendly interface

---

## Workflow 7: Data Export & Integration

### Objective
Validate data can be exported and integrated with external systems.

### Test Steps

#### Step 1: Filter Data (F5)
1. Apply date filter: Last Quarter
2. Apply tag filter: "Tax-Deductible"
3. Verify filtered results

#### Step 2: Export Transactions
1. Click "Export" button
2. Select format: CSV
3. Download file
4. Verify file contents match filter

**Expected Results:**
- Export includes filtered data only
- CSV format valid
- All fields included

#### Step 3: Export Reports
1. Navigate to Reports
2. Generate "Expense by Category" report
3. Export as PDF
4. Verify PDF contains charts and data

**Expected Results:**
- Report generates successfully
- PDF formatted correctly
- Charts visible in PDF

### Success Criteria
- Data exportable
- Formats valid
- Reports shareable

---

## Workflow 8: Error Recovery

### Objective
Validate graceful handling of errors throughout the flow.

### Test Steps

#### Step 1: Import Error (F1)
1. Upload corrupted CSV
2. Verify error message displayed
3. Verify user can retry
4. Upload valid file
5. Verify recovery successful

#### Step 2: AI Service Error (F3)
1. Simulate AI service downtime
2. Attempt to get classification
3. Verify graceful fallback
4. Verify manual categorization still works

#### Step 3: Dashboard Error (F5)
1. Simulate chart data API error
2. Navigate to dashboard
3. Verify error boundary caught error
4. Verify other dashboard components still render
5. Verify retry option available

#### Step 4: Chat Error (F4)
1. Submit query during service issue
2. Verify "I'm having trouble" message
3. Verify suggested offline actions
4. Verify chat history preserved

### Success Criteria
- Errors handled gracefully
- User can recover
- Partial functionality maintained
- No data loss

---

## Success Criteria Summary

| Workflow | Key Success Criteria | Pass Threshold |
|----------|---------------------|----------------|
| 1. Onboarding | Complete in < 15 min | 100% |
| 2. Weekly Review | Complete in < 10 min | 100% |
| 3. Risk Detection | All risks detected | ≥95% |
| 4. Learning | Accuracy improves | +20% |
| 5. Multi-Period | Comparisons accurate | 100% |
| 6. Mobile | All features usable | 100% |
| 7. Export | Data exportable | 100% |
| 8. Error Recovery | Graceful handling | 100% |

---

## Regression Test Execution

Execute these workflows when:
- New feature deployed
- Database schema changed
- AI models updated
- UI framework updated
- Performance optimizations made

**Frequency:**
- Full suite: Weekly
- Critical workflows (1,3): Daily
- Mobile workflow (6): Per release

---

**Test Plan Version:** 1.0
**Last Updated:** 2026-02-27
