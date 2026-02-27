# End-to-End Test Plans - Master Index

## Overview

This folder contains comprehensive behavioral end-to-end test plans for all 5 features of the financial intelligence platform. Tests are organized for both **human testers** (manual QA) and **AI/automated testers**.

## Test Plan Structure

| File | Purpose | Audience |
|------|---------|----------|
| `master-index.md` | This file - navigation hub for all test plans | All |
| `f1-human-tests.md` | Feature 1: Smart Data Ingestion Engine - Manual test cases | Human QA |
| `f1-automated-tests.md` | Feature 1: Automated test specifications | AI/Automation |
| `f2-human-tests.md` | Feature 2: Business Entity Structuring - Manual test cases | Human QA |
| `f2-automated-tests.md` | Feature 2: Automated test specifications | AI/Automation |
| `f3-human-tests.md` | Feature 3: AI Financial Intelligence - Manual test cases | Human QA |
| `f3-automated-tests.md` | Feature 3: Automated test specifications | AI/Automation |
| `f4-human-tests.md` | Feature 4: Conversational Assistant - Manual test cases | Human QA |
| `f4-automated-tests.md` | Feature 4: Automated test specifications | AI/Automation |
| `f5-human-tests.md` | Feature 5: Clarity Dashboard - Manual test cases | Human QA |
| `f5-automated-tests.md` | Feature 5: Automated test specifications | AI/Automation |
| `e2e-workflows.md` | Cross-feature end-to-end workflow tests | Both |
| `test-data.md` | Sample test data specifications | Both |
| `defect-template.md` | Template for logging defects | Human QA |

## Feature Summary

### Feature 1: Smart Data Ingestion Engine
- CSV upload and validation
- Auto column detection
- Preview and confirmation
- Data normalization
- Duplicate detection
- Error handling

### Feature 2: Business Entity Structuring Layer
- AI entity recognition (customers/suppliers)
- Revenue stream mapping
- Expense categorization
- Custom tagging
- Entity dashboards

### Feature 3: AI Financial Intelligence Engine
- Auto-classification
- Recurring payment detection
- Spending trend analysis
- Anomaly detection
- Cashflow forecasting
- Weekly AI summaries

### Feature 4: Conversational Financial Assistant
- Natural language queries
- Contextual responses
- Proactive alerts
- Weekly email summaries
- Multi-channel communication

### Feature 5: Clarity Dashboard
- KPI overview cards
- Revenue/expense trends
- Cashflow visualization
- Anomaly highlights
- Customization & drag-drop

## Test Execution Priority

### Phase 1: Core Data Flow (Week 1-2)
1. Feature 1: Data Ingestion
2. Feature 2: Entity Structuring
3. Cross-feature: Import → Entity Mapping

### Phase 2: Intelligence Layer (Week 3-4)
4. Feature 3: AI Analysis
5. Cross-feature: Data → AI Insights

### Phase 3: User Interface (Week 5-6)
6. Feature 5: Dashboard
7. Feature 4: Conversational Interface
8. Cross-feature: Full User Journey

## Test Environment Requirements

### Minimum Test Data
- 5 different bank CSV formats
- 10,000+ transaction records
- 20+ customer entities
- 15+ supplier entities
- 3 months of historical data

### Browser Requirements
- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
- Mobile: iOS Safari, Android Chrome

## How to Use These Test Plans

### For Human Testers
1. Start with `fX-human-tests.md` for your assigned feature
2. Follow test cases in order (they build on each other)
3. Use `test-data.md` for sample inputs
4. Log defects using `defect-template.md`
5. Execute cross-feature workflows from `e2e-workflows.md`

### For AI/Automated Testers
1. Reference `fX-automated-tests.md` for test specifications
2. Implement tests using the provided assertions and expected results
3. Use API schemas from `../detailed design/`
4. Report pass/fail metrics against acceptance criteria

## Acceptance Criteria Summary

| Feature | Key Metrics |
|---------|-------------|
| F1 | Upload <10s, Detection ≥85%, Preview loads <2s |
| F2 | Classification ≥85%, Response <2s, Top 5 ranking correct |
| F3 | Classification ≥85%, Anomaly ≥90%, Forecast ≥80% |
| F4 | Response <3s, 20+ intents recognized, Delivery ≥99% |
| F5 | Load <2s, Mobile responsive, Charts render <2s |

---

**Last Updated:** 2026-02-27
**Version:** 1.0
