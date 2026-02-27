# Feature 5: Clarity Dashboard - Human Test Plan

## Overview
Tests for dashboard KPIs, visual insights, charts, customization, and user interactions.

---

## EPIC 1: Dashboard Overview & Key Metrics

### Test Case F5-E1-S1.1: Display Cash Balance

**Objective:** Verify current cash balance displayed prominently

**Preconditions:**
- Transactions imported and processed
- Dashboard accessible

**Steps:**
1. Navigate to Dashboard
2. Review Cash Balance card

**Expected Results:**
- Cash balance displayed as large number
- Currency symbol included ($, €, etc.)
- Time period indicator ("as of today")
- Update timestamp visible
- Low balance warning if applicable

**Pass Criteria:**
- Balance accurate (matches sum of transactions)
- Prominent display
- Warning triggers correctly

---

### Test Case F5-E1-S1.2: Negative Balance Handling

**Objective:** Verify negative balance displayed appropriately

**Preconditions:**
- Account with negative balance

**Steps:**
1. View Dashboard with negative balance

**Expected Results:**
- Negative balance shown (e.g., "-$500")
- Red color indicator
- Warning message: "Your balance is negative"
- Guidance provided: "Review recent expenses or check for missing income"

**Pass Criteria:**
- Negative amount displayed correctly
- Warning visible
- No errors

---

### Test Case F5-E1-S2.1: Show Revenue Summary

**Objective:** Verify revenue summary panel displays correctly

**Preconditions:**
- Revenue transactions exist

**Steps:**
1. Navigate to Dashboard
2. Review Revenue panel

**Expected Results:**
- Total revenue for selected period displayed
- Large, readable number
- Trend indicator vs previous period (↑ 12%, ↓ 5%, or → 0%)
- Color coding (green for up, red for down)
- Time period clearly labeled

**Pass Criteria:**
- Amount accurate
- Trend calculation correct
- Visual indicators clear

---

### Test Case F5-E1-S2.2: Show Expense Summary

**Objective:** Verify expense summary panel displays correctly

**Preconditions:**
- Expense transactions exist

**Steps:**
1. Review Expense panel on Dashboard

**Expected Results:**
- Total expenses for selected period
- Trend indicator vs previous period
- Color coding (red for increase, green for decrease)
- Net position (Revenue - Expenses) visible

**Pass Criteria:**
- Math accurate
- Trends correct
- Net position calculation correct

---

### Test Case F5-E1-S2.3: Missing Historical Data Handling

**Objective:** Verify dashboard handles missing historical data

**Preconditions:**
- New user with < 1 month data
- Or selected period with no data

**Steps:**
1. Change time period to range with no transactions
2. Review dashboard panels

**Expected Results:**
- "No data for this period" message
- Suggestion: "Try selecting a different time period"
- No errors or NaN values
- Trend indicator hidden or shows "N/A"

**Pass Criteria:**
- Graceful handling of missing data
- No visual glitches
- Helpful guidance provided

---

### Test Case F5-E1-S3.1: Display Top 5 Customers

**Objective:** Verify top customers list displays correctly

**Preconditions:**
- Multiple customers with revenue

**Steps:**
1. Navigate to Dashboard
2. Scroll to Top Customers section

**Expected Results:**
- Maximum 5 customers displayed
- Each row shows:
  - Customer name
  - Total revenue amount
  - Percentage of total revenue
  - Mini bar chart or progress indicator
- Ranked by revenue (1-5)
- "View All" link if more than 5 customers

**Pass Criteria:**
- Rankings accurate
- Percentages sum to ~100%
- Visual layout clean

---

### Test Case F5-E1-S3.2: Customer Drill-Down

**Objective:** Verify clicking customer shows details

**Preconditions:**
- Top customers displayed

**Steps:**
1. Click on customer "ACME Corp" in top customers list
2. Review detail page
3. Click back

**Expected Results:**
- Customer detail page opens
- Shows all transactions for that customer
- Total revenue for period
- Average transaction size
- Transaction trend over time
- Back button returns to dashboard

**Pass Criteria:**
- Navigation works
- Data accurate
- Back returns correctly

---

### Test Case F5-E1-S3.3: Equal Revenue Customers

**Objective:** Verify handling of tied revenue amounts

**Preconditions:**
- Two customers with identical revenue totals

**Steps:**
1. Review Top Customers list

**Expected Results:**
- Both customers displayed
- Clear indication of tie OR alphabetical ordering
- Percentages calculated correctly

**Pass Criteria:**
- Ties handled gracefully
- Data accurate

---

## EPIC 2: Visual Insights & Trends

### Test Case F5-E2-S1.1: Revenue & Expense Trend Chart

**Objective:** Verify trend line chart displays correctly

**Preconditions:**
- 3+ months of transaction data

**Steps:**
1. Navigate to Dashboard
2. View Revenue vs Expenses chart
3. Hover over data points

**Expected Results:**
- Line chart with two lines (revenue, expenses)
- X-axis: time periods (months/weeks)
- Y-axis: amounts
- Legend clearly identifying each line
- Hover shows exact values for period
- Different colors for revenue (green) and expenses (red/orange)
- Chart renders < 2 seconds

**Pass Criteria:**
- Chart renders correctly
- Data accurate
- Interactive elements work
- Performance < 2s

---

### Test Case F5-E2-S1.2: Missing Data Points in Chart

**Objective:** Verify chart handles missing data gracefully

**Preconditions:**
- Data with gaps (e.g., no transactions in certain months)

**Steps:**
1. View trend chart spanning gap period

**Expected Results:**
- Line breaks or shows zero for missing periods
- No visual artifacts
- Gap clearly indicated
- Chart still readable

**Pass Criteria:**
- Missing data handled gracefully
- No crashes

---

### Test Case F5-E2-S2.1: Cashflow Timeline

**Objective:** Verify cashflow visualization displays

**Preconditions:**
- Cashflow data available

**Steps:**
1. View Cashflow Timeline section
2. Review historical and projected data

**Expected Results:**
- Historical cash balance plotted
- 30-day projection line shown (dashed or different color)
- Projected low points highlighted in red
- Interactive zoom if implemented
- Legend distinguishes historical vs projected

**Pass Criteria:**
- Timeline accurate
- Projections visible
- Warnings highlighted

---

### Test Case F5-E2-S2.2: Cashflow Projection Accuracy Display

**Objective:** Verify projection shown with confidence context

**Preconditions:**
- Cashflow forecast generated

**Steps:**
1. Review cashflow projection section

**Expected Results:**
- Projected range shown (not just single number)
- Confidence interval visible or implied
- Disclaimer about projections being estimates
- Historical accuracy note (if available)

**Pass Criteria:**
- Projections contextualized
- User understands uncertainty

---

### Test Case F5-E2-S3.1: Highlight Top Anomalies

**Objective:** Verify anomalies displayed prominently

**Preconditions:**
- Anomalies detected by AI (Feature 3)

**Steps:**
1. View Dashboard
2. Look at Alerts/Anomalies section

**Expected Results:**
- Top 3 anomalies displayed
- Color coding: red for high expense spike, yellow for revenue dip
- Each anomaly shows:
  - Type (spending spike, revenue drop, etc.)
  - Category/customer affected
  - Amount/percentage change
  - Brief explanation
- Clickable for full details

**Pass Criteria:**
- Anomalies visible
- Color coding clear
- Explanations helpful

---

### Test Case F5-E2-S3.2: Anomaly Drill-Down

**Objective:** Verify clicking anomaly shows details

**Preconditions:**
- Anomaly displayed on dashboard

**Steps:**
1. Click on anomaly card
2. Review detail view

**Expected Results:**
- Detailed explanation opens
- Contributing transactions listed
- Trend comparison shown
- AI-generated insight provided
- Option to dismiss/mark as reviewed

**Pass Criteria:**
- Drill-down works
- Details comprehensive
- Actions available

---

## EPIC 3: Customization & Interaction

### Test Case F5-E3-S1.1: Toggle Metrics Visibility

**Objective:** Verify user can show/hide KPI cards

**Preconditions:**
- User logged in
- Dashboard accessible

**Steps:**
1. Click "Customize Dashboard"
2. Uncheck "Top Customers"
3. Check "Cashflow Forecast"
4. Save changes
5. Review dashboard

**Expected Results:**
- Unchecked metrics hidden immediately
- Checked metrics appear
- Layout adjusts automatically
- Changes persist after refresh
- Settings saved per user

**Pass Criteria:**
- Toggle works
- Layout responsive
- Changes persist

---

### Test Case F5-E3-S1.2: Hide All Metrics Edge Case

**Objective:** Verify graceful handling when all metrics hidden

**Preconditions:**
- Customize dashboard mode

**Steps:**
1. Uncheck ALL metric toggles
2. Save

**Expected Results:**
- Warning: "Please select at least one metric to display"
- OR: Empty state message with guidance
- Dashboard doesn't break

**Pass Criteria:**
- Edge case handled
- User guided to correct action

---

### Test Case F5-E3-S2.1: Filter by Date Range

**Objective:** Verify date range filter works

**Preconditions:**
- Dashboard with data

**Steps:**
1. Click date range selector
2. Select "Last 3 Months"
3. Observe dashboard update
4. Select "Custom Range"
5. Set start: Jan 1, end: Mar 31
6. Apply

**Expected Results:**
- All dashboard panels update to reflect selected range
- Top Customers recalculated for range
- Charts update
- URL updates with filter parameters
- Time period label updates

**Pass Criteria:**
- All components update
- Data accurate for range
- Performance < 2s

---

### Test Case F5-E3-S2.2: Filter by Tags

**Objective:** Verify tag-based dashboard filtering

**Preconditions:**
- Transactions with tags

**Steps:**
1. Click "Filter by Tags"
2. Select tag "Q1-Project"
3. Apply

**Expected Results:**
- Dashboard shows only Q1-Project data
- Revenue/Expense totals recalculated
- Top Customers filtered
- Active filter pill shown
- "Clear Filters" option available

**Pass Criteria:**
- Filter applied correctly
- Totals accurate
- Clear filter works

---

### Test Case F5-E3-S2.3: Invalid Date Range Handling

**Objective:** Verify invalid date ranges handled gracefully

**Preconditions:**
- Custom date range selector open

**Steps:**
1. Set end date before start date
2. Try to apply

**Expected Results:**
- Validation error: "End date must be after start date"
- Apply button disabled or error shown
- User can correct

**Pass Criteria:**
- Validation works
- Helpful error message

---

### Test Case F5-E3-S3.1: Drag and Reorder Cards

**Objective:** Verify dashboard cards can be reordered

**Preconditions:**
- Customize mode enabled (if required)

**Steps:**
1. Drag "Revenue Summary" card to top position
2. Drag "Cashflow" card below it
3. Save layout
4. Refresh page

**Expected Results:**
- Cards reorder visually during drag
- Drop places card in new position
- Layout saves successfully
- After refresh, order maintained
- Smooth animation during drag

**Pass Criteria:**
- Drag and drop works
- Layout persists
- No visual glitches

---

### Test Case F5-E3-S3.2: Mobile Drag-and-Drop

**Objective:** Verify reordering works on mobile

**Preconditions:**
- Mobile device or emulator

**Steps:**
1. Touch and hold card to initiate drag
2. Move to new position
3. Release

**Expected Results:**
- Touch-hold initiates drag mode
- Card lifts and can be moved
- Other cards make space
- Release drops card
- OR: Alternative reordering UI provided for mobile

**Pass Criteria:**
- Reordering possible on mobile
- Usable touch interface

---

### Test Case F5-E3-S3.3: Reset to Default Layout

**Objective:** Verify reset option available

**Preconditions:**
- Dashboard layout customized

**Steps:**
1. Click "Reset to Default"
2. Confirm in dialog

**Expected Results:**
- Confirmation dialog appears
- Upon confirmation, layout resets to default
- Default metric selection restored
- Default card order restored

**Pass Criteria:**
- Reset works
- Confirmation prevents accidents

---

## Cross-Cutting Tests

### Test Case F5-CROSS-001: Dashboard Load Performance

**Objective:** Verify dashboard loads quickly

**Preconditions:**
- Large dataset (10k+ transactions)
- Clear browser cache

**Steps:**
1. Navigate to Dashboard
2. Time full load
3. Check all components

**Expected Results:**
- Initial render < 2 seconds
- All cards visible
- Charts render < 2 seconds each
- No loading spinners after 5 seconds

**Pass Criteria:**
- Load time < 2s
- Performance acceptable

---

### Test Case F5-CROSS-002: Mobile Responsive Layout

**Objective:** Verify dashboard works on mobile

**Preconditions:**
- Mobile device or emulator

**Steps:**
1. Open dashboard on mobile
2. Scroll through all sections
3. Interact with charts
4. Test filters

**Expected Results:**
- Single column layout on mobile
- Charts resize appropriately
- Horizontal scroll for tables if needed
- Touch targets 44px+
- No horizontal overflow
- All features accessible

**Pass Criteria:**
- Usable on mobile
- No layout breaks
- Touch-friendly

---

### Test Case F5-CROSS-003: Real-Time Updates

**Objective:** Verify dashboard updates when new data arrives

**Preconditions:**
- Dashboard open
- New transaction imported elsewhere

**Steps:**
1. Note current dashboard values
2. Import new transaction (different tab or by another user)
3. Wait for update
4. Refresh dashboard

**Expected Results:**
- After refresh: Updated values shown
- OR (if real-time): Values update automatically within reasonable time

**Pass Criteria:**
- Data consistency maintained
- Updates visible

---

## Regression Test Checklist

Execute when modifying F5 code:

- [ ] F5-E1-S1.1: Cash balance display
- [ ] F5-E1-S2.1: Revenue summary
- [ ] F5-E1-S3.1: Top customers
- [ ] F5-E2-S1.1: Trend charts
- [ ] F5-E2-S2.1: Cashflow timeline
- [ ] F5-E2-S3.1: Anomaly highlights
- [ ] F5-E3-S1.1: Toggle metrics
- [ ] F5-E3-S2.1: Date filtering
- [ ] F5-E3-S3.1: Drag and reorder
- [ ] F5-CROSS-001: Load performance
- [ ] F5-CROSS-002: Mobile responsive

---

**Test Plan Version:** 1.0
**Last Updated:** 2026-02-27
