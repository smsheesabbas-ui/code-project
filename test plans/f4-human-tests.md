# Feature 4: Conversational Financial Assistant - Human Test Plan

## Overview
Tests for natural language queries, contextual responses, proactive alerts, and multi-channel delivery.

---

## EPIC 1: Natural Language Query Engine

### Test Case F4-E1-S1.1: Ask "What was my revenue last month?"

**Objective:** Verify system understands basic revenue query

**Preconditions:**
- Transactions imported with revenue data
- Previous month has revenue transactions

**Steps:**
1. Open chat interface
2. Type: "What was my revenue last month?"
3. Press Enter or click Send

**Expected Results:**
- Response time < 3 seconds
- Response includes:
  - Last month's total revenue amount
  - Comparison to previous month (e.g., "up 12%")
  - Plain language format: "Your revenue last month was $8,500. That's 12% higher than the month before."
- No accounting jargon used

**Pass Criteria:**
- Correct amount returned
- Comparison accurate
- Response in plain English

---

### Test Case F4-E1-S1.2: Ask "Who is my top customer?"

**Objective:** Verify entity ranking query works

**Preconditions:**
- Multiple customers with revenue transactions

**Steps:**
1. Type: "Who is my top customer?"
2. Review response

**Expected Results:**
- Response: "Your top customer is ACME Corp, contributing $15,000 (45% of your total revenue)."
- Customer name correctly identified
- Percentage calculation accurate
- Time period implied (all time or current year)

**Pass Criteria:**
- Correct customer identified
- Math accurate

---

### Test Case F4-E1-S1.3: Ask "Why was last month lower?"

**Objective:** Verify trend analysis and reasoning query

**Preconditions:**
- Month-over-month revenue decline occurred

**Steps:**
1. Type: "Why was last month lower?"
2. Review response

**Expected Results:**
- System recognizes "last month" and "lower" context
- Response explains:
  - Revenue amount vs previous month
  - Primary causes identified (e.g., "Client B didn't purchase this month")
  - Contributing factors
- Plain language explanation

**Pass Criteria:**
- Context correctly interpreted
- Reasoning provided
- Answer relevant to actual data

---

### Test Case F4-E1-S1.4: Ask "How much did I spend on marketing?"

**Objective:** Verify category-based expense query

**Preconditions:**
- Expenses categorized with "Marketing" or similar

**Steps:**
1. Type: "How much did I spend on marketing?"
2. Review response

**Expected Results:**
- System maps "marketing" to expense category
- Returns total marketing expenses (default: current month or all time)
- Offers to show breakdown by vendor/time

**Pass Criteria:**
- Category correctly mapped
- Amount accurate

---

### Test Case F4-E1-S1.5: Vague Question Handling

**Objective:** Verify graceful handling of unclear questions

**Preconditions:**
- Chat interface open

**Steps:**
1. Type: "How am I doing?"
2. Review response

**Expected Results:**
- Response asks for clarification OR provides general summary
- "I can tell you about your revenue, expenses, or cashflow. What would you like to know?"
- Suggested follow-up questions provided

**Pass Criteria:**
- No error or crash
- Helpful clarification requested
- Conversation continues smoothly

---

### Test Case F4-E1-S1.6: Follow-up Question Context

**Objective:** Verify context maintained across multiple questions

**Preconditions:**
- Previous question asked about revenue

**Steps:**
1. First question: "What was my revenue last month?"
2. Follow-up: "What about the month before?"
3. Another follow-up: "How does that compare to expenses?"

**Expected Results:**
- Second question understood as "revenue the month before last"
- Third question compares to expenses for same period
- No need to re-specify subject (revenue) or time period
- Context maintained within session

**Pass Criteria:**
- Context correctly maintained
- Follow-ups understood
- Correct data returned

---

### Test Case F4-E1-S2.1: Time Reference Parsing

**Objective:** Verify various time expressions understood

**Preconditions:**
- Historical data available across multiple periods

**Steps:**
Test these queries:
1. "This month"
2. "Last month"
3. "In January"
4. "Q1 2024"
5. "Last 3 months"
6. "Year to date"
7. "2023"

**Expected Results:**
- Each time reference correctly parsed
- Correct date range applied to query
- Results match expected period

**Pass Criteria:**
- All common time expressions work
- Date ranges accurate

---

### Test Case F4-E1-S2.2: Multi-Currency Data Query

**Objective:** Verify queries work with multi-currency data

**Preconditions:**
- Transactions in multiple currencies

**Steps:**
1. Type: "What was my revenue in EUR?"
2. Review response

**Expected Results:**
- Revenue calculated in requested currency
- Exchange rates applied appropriately
- Response notes: "Your revenue was €7,800 (converted from USD at current rates)"

**Pass Criteria:**
- Currency conversion handled
- Amounts accurate

---

### Test Case F4-E1-S3.1: Simple Language Response

**Objective:** Verify responses avoid technical jargon

**Preconditions:**
- Query that could trigger technical terms

**Steps:**
1. Type: "What are my financial trends?"
2. Review response language

**Expected Results:**
- No terms: "variance", "standard deviation", "regression", "correlation"
- Use instead: "ups and downs", "typical range", "pattern", "connection"
- Short, concise sentences
- Summary insight included

**Pass Criteria:**
- Zero prohibited terms
- Readability score appropriate for general audience

---

### Test Case F4-E1-S3.2: Include Summary Insight

**Objective:** Verify responses include actionable insight, not just numbers

**Preconditions:**
- Query about revenue or expenses

**Steps:**
1. Type: "What was my revenue?"
2. Review complete response

**Expected Results:**
- Not just: "$10,000"
- Instead: "Your revenue was $10,000. That's 15% higher than last month, mostly due to a large payment from Client A."
- Includes context and explanation

**Pass Criteria:**
- Numbers have context
- Insight provided
- Plain language maintained

---

## EPIC 2: Proactive Alerts & Notifications

### Test Case F4-E2-S1.1: Cashflow Risk Notification

**Objective:** Verify proactive cashflow alerts appear

**Preconditions:**
- Cashflow forecast predicts risk condition
- User has notifications enabled

**Steps:**
1. Review dashboard or wait for notification
2. Observe alert

**Expected Results:**
- Alert appears without user query
- Message: "You may run low on cash in 12 days if spending continues at this rate."
- Alert includes:
  - Projected shortfall date
  - Current vs projected balance
  - Brief explanation
  - Suggested action
- Dismissible

**Pass Criteria:**
- Alert triggered automatically
- Information accurate
- Actionable

---

### Test Case F4-E2-S1.2: Alert Explanation Clarity

**Objective:** Verify alert explanations are human-readable

**Preconditions:**
- Cashflow or other risk alert displayed

**Steps:**
1. Click alert for details
2. Read explanation

**Expected Results:**
- Explanation in plain language
- Specific numbers provided
- Contributing factors listed
- No technical formulas or calculations shown

**Pass Criteria:**
- Explanation understandable
- No technical jargon

---

### Test Case F4-E2-S2.1: Large Transaction Alert

**Objective:** Verify unusual transaction notifications

**Preconditions:**
- Baseline spending established
- New large transaction processed

**Steps:**
1. Import or process large unusual transaction
2. Review notifications

**Expected Results:**
- Alert: "Large expense detected: $2,500 to Vendor XYZ"
- Comparison to typical spending
- Quick actions: "Review", "Mark as Expected", "Investigate"

**Pass Criteria:**
- Large transactions flagged
- Context provided
- Quick actions work

---

### Test Case F4-E2-S2.2: Revenue Drop Alert

**Objective:** Verify revenue decline notifications

**Preconditions:**
- Revenue drop detected vs previous period

**Steps:**
1. Review dashboard alerts section

**Expected Results:**
- Alert: "Revenue down 20% vs last month"
- Affected customers or streams identified
- Explanation provided
- Suggested follow-up actions

**Pass Criteria:**
- Drop correctly detected
- Root cause identified

---

### Test Case F4-E2-S3.1: Weekly Summary Email Delivery

**Objective:** Verify weekly email sent automatically

**Preconditions:**
- Email notifications enabled in settings
- Week of data available

**Steps:**
1. Check email inbox on scheduled day
2. Review email content
3. Check sender, formatting

**Expected Results:**
- Email received from branded sender (not spam)
- Subject: "Your Weekly Financial Summary - Week of Feb 19"
- Content includes:
  - Week's revenue and expenses
  - Top customer
  - Top expense category
  - Notable trends
  - Call-to-action to view dashboard
- Mobile-friendly formatting
- Unsubscribe link present

**Pass Criteria:**
- Email delivered
- Content accurate
- Not marked as spam

---

### Test Case F4-E2-S3.2: Weekly Summary Email Unsubscribe

**Objective:** Verify unsubscribe functionality

**Preconditions:**
- Weekly email enabled

**Steps:**
1. Click "Unsubscribe" in weekly email
2. Confirm unsubscription
3. Wait for next weekly cycle

**Expected Results:**
- Unsubscribe page loads
- Confirmation shown
- Next week: No email sent
- Dashboard setting updated to reflect unsubscribe
- User can re-subscribe from settings

**Pass Criteria:**
- Unsubscribe works
- No further emails
- Setting persisted

---

### Test Case F4-E2-S3.3: Alert Preference Management

**Objective:** Verify user can customize alert settings

**Preconditions:**
- User settings accessible

**Steps:**
1. Navigate to Settings > Notifications
2. Toggle off "Cashflow Risk Alerts"
3. Toggle on "Large Transaction Alerts"
4. Change frequency to "Daily Digest"
5. Save settings

**Expected Results:**
- Toggles work and persist
- Disabled alerts no longer shown
- Enabled alerts continue
- Frequency setting respected

**Pass Criteria:**
- Preferences saved
- Respected by system
- UI reflects current settings

---

## EPIC 3: Multi-Channel Communication

### Test Case F4-E3-S1.1: WhatsApp Summary Delivery (if implemented)

**Objective:** Verify WhatsApp message delivery (if feature enabled)

**Preconditions:**
- WhatsApp integration enabled
- User opted in
- Phone number verified

**Steps:**
1. Trigger weekly summary
2. Check WhatsApp messages

**Expected Results:**
- Message received from verified business number
- Formatted for mobile reading
- Summary within WhatsApp message limits
- Secure link to detailed view (if needed)

**Pass Criteria:**
- Message delivered
- Link secure
- Opt-in respected

---

### Test Case F4-E3-S2.1: Mobile Chat Interface

**Objective:** Verify chat works on mobile devices

**Preconditions:**
- Mobile device or emulator
- Chat feature accessible

**Steps:**
1. Open app on mobile browser
2. Navigate to chat/assistant
3. Ask a question
4. Review response layout

**Expected Results:**
- Chat interface responsive
- Input field accessible
- Keyboard doesn't obscure input
- Conversation history scrollable
- Messages display properly
- Response time < 3s on mobile

**Pass Criteria:**
- Usable on mobile
- No layout issues
- Performance acceptable

---

### Test Case F4-E3-S3.1: Alert Preference Channel Selection

**Objective:** Verify user can select alert channels

**Preconditions:**
- Multiple channels available (dashboard, email, mobile push)

**Steps:**
1. Navigate to Settings > Notification Channels
2. Enable "Dashboard Notifications"
3. Enable "Email"
4. Disable "Push Notifications"
5. Save

**Expected Results:**
- Settings persisted per channel
- Alerts appear on enabled channels only
- Disabled channels don't receive alerts

**Pass Criteria:**
- Channel preferences work
- Settings persist

---

## Cross-Cutting Tests

### Test Case F4-CROSS-001: Response Time < 3 Seconds

**Objective:** Verify chat responses are fast

**Preconditions:**
- Chat interface open

**Steps:**
1. Time these queries:
   - Simple: "What was revenue?"
   - Complex: "Why did expenses increase last quarter?"
   - Follow-up: "What about the quarter before?"

**Expected Results:**
- All responses < 3 seconds
- Loading indicator for complex queries
- No timeout errors

**Pass Criteria:**
- 95% of queries < 3s
- p99 < 5s

---

### Test Case F4-CROSS-002: Graceful Fallback for Unknown Queries

**Objective:** Verify system handles unrecognized questions gracefully

**Preconditions:**
- Chat interface open

**Steps:**
1. Ask off-topic question: "What's the weather today?"
2. Ask ambiguous question: "Tell me about my stuff"
3. Ask technical question: "What SQL queries do you run?"

**Expected Results:**
- No error messages or crashes
- Polite response: "I'm not sure I understand. I can help with questions about your revenue, expenses, customers, or cashflow."
- Suggested questions provided
- Conversation can continue

**Pass Criteria:**
- Graceful handling
- Conversation continuity maintained

---

### Test Case F4-CROSS-003: 20+ Core Financial Intents Recognized

**Objective:** Verify system recognizes all core financial intents

**Preconditions:**
- List of 20+ test queries prepared

**Steps:**
Execute queries covering:
- Revenue queries (5 variations)
- Expense queries (5 variations)
- Customer queries (4 variations)
- Cashflow queries (3 variations)
- Trend queries (3 variations)

**Expected Results:**
- All queries understood correctly
- Appropriate data retrieved
- Responses relevant

**Pass Criteria:**
- ≥20 intents recognized
- 90%+ recognition accuracy

---

## Regression Test Checklist

Execute when modifying F4 code:

- [ ] F4-E1-S1.1: Basic revenue query
- [ ] F4-E1-S1.5: Vague question handling
- [ ] F4-E1-S1.6: Follow-up context
- [ ] F4-E1-S2.1: Time reference parsing
- [ ] F4-E1-S3.1: Simple language
- [ ] F4-E2-S1.1: Cashflow risk alert
- [ ] F4-E2-S3.1: Weekly email
- [ ] F4-E3-S2.1: Mobile chat
- [ ] F4-CROSS-001: Response time
- [ ] F4-CROSS-003: 20+ intents

---

**Test Plan Version:** 1.0
**Last Updated:** 2026-02-27
