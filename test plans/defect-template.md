# Defect Report Template

## Overview
Standard template for logging defects found during testing. Use this format for consistent defect tracking.

---

## Defect Template

```markdown
# Defect Report: [DEF-XXX]

## Basic Information
| Field | Value |
|-------|-------|
| **Defect ID** | DEF-XXX |
| **Title** | Brief description of the issue |
| **Feature** | F1 / F2 / F3 / F4 / F5 / Cross-Feature |
| **Severity** | Critical / High / Medium / Low |
| **Priority** | P0 / P1 / P2 / P3 |
| **Environment** | Dev / Staging / Production |
| **Browser** | Chrome / Firefox / Safari / Edge / Mobile |
| **OS** | Windows / macOS / iOS / Android |
| **Date Reported** | YYYY-MM-DD |
| **Reported By** | Tester Name |
| **Assigned To** | Developer Name |
| **Status** | New / In Progress / Fixed / Verified / Closed |

## Defect Description
### Summary
One sentence summary of the defect.

### Detailed Description
Detailed explanation of what is wrong. Include:
- What is the actual behavior?
- What is the expected behavior?
- Why is this a defect?

## Steps to Reproduce
1. Step one
2. Step two
3. Step three
4. Expected result at each step
5. Actual result at each step

## Expected Result
What should happen when following the steps above.

## Actual Result
What actually happens. Include:
- Error messages
- Visual issues
- Data problems
- Performance issues

## Evidence
### Screenshots
Attach screenshots with annotations showing the issue.

### Video/GIF
Attach screen recording if issue involves animation/interaction.

### Logs
```
Relevant console logs, error logs, or API responses
```

### Test Data
- Input files used
- Database state
- User account used

## Impact Assessment
### User Impact
- How does this affect users?
- Workaround available? Yes/No
- Workaround description (if applicable)

### Business Impact
- Revenue impact? Yes/No
- Data integrity risk? Yes/No
- Compliance risk? Yes/No

## Related Information
### Related Defects
- Link to related defects (if any)

### Related Test Cases
- Test case ID that found this defect
- Link to test plan section

### Requirements Reference
- Link to requirement document
- Specific requirement ID

## Root Cause Analysis (Filled by Dev)
### Cause Category
- [ ] Code defect
- [ ] Design issue
- [ ] Environment issue
- [ ] Data issue
- [ ] Requirement gap
- [ ] Third-party issue
- [ ] Other: _____

### Technical Details
Developer notes on root cause and fix approach.

## Fix Verification (Filled by QA)
### Fix Version
Version containing the fix: _______

### Verification Steps
Steps taken to verify fix:
1. Step one
2. Step two
3. Step three

### Verification Result
- [ ] Defect fixed
- [ ] Defect partially fixed (explain)
- [ ] Defect not fixed
- [ ] New issues introduced (describe)

### Regression Test
- [ ] Related test cases passed
- [ ] No new defects introduced
```

---

## Severity Guidelines

### Critical
- **Definition:** System crash, data loss, security breach
- **Examples:**
  - Application completely unresponsive
  - Data corruption in database
  - Unauthorized access to data
  - Payment processing failure
- **Response Time:** Immediate (within 1 hour)

### High
- **Definition:** Major feature broken, no workaround
- **Examples:**
  - CSV import completely fails
  - Dashboard shows incorrect totals
  - AI classification fails on all transactions
  - Chat interface non-functional
- **Response Time:** Same day

### Medium
- **Definition:** Feature partially broken, workaround exists
- **Examples:**
  - Column detection accuracy < 85%
  - Charts render slowly (> 5 seconds)
  - Mobile layout issues
  - Minor UI glitches
- **Response Time:** Within 3 days

### Low
- **Definition:** Cosmetic issues, minor inconveniences
- **Examples:**
  - Spelling errors
  - Minor alignment issues
  - Color inconsistencies
  - Suggestions for improvement
- **Response Time:** Next sprint

---

## Priority Guidelines

### P0 - Blocker
- Blocks release
- Blocks testing of other features
- No workaround available

### P1 - Critical
- Must fix for release
- Significant user impact
- Workaround difficult

### P2 - Important
- Should fix for release
- Moderate user impact
- Workaround available

### P3 - Nice to Have
- Fix if time permits
- Minor user impact
- Easy workaround

---

## Status Definitions

| Status | Definition |
|--------|------------|
| **New** | Defect reported, not yet assigned |
| **In Progress** | Developer actively working on fix |
| **Fixed** | Fix committed, awaiting verification |
| **Verified** | QA verified fix works |
| **Closed** | Defect resolved and closed |
| **Reopened** | Fix failed verification, back to dev |
| **Deferred** | Won't fix in this release |
| **Duplicate** | Same as existing defect |
| **Not a Defect** | Working as designed |

---

## Defect Logging Best Practices

### Do's
- ✅ Be specific and clear
- ✅ Include exact steps to reproduce
- ✅ Provide screenshots/videos
- ✅ Include test data
- ✅ Reference test case that found it
- ✅ Set appropriate severity/priority
- ✅ Check for duplicates before logging

### Don'ts
- ❌ Use vague language ("it doesn't work")
- ❌ Skip steps in reproduction
- ❌ Log multiple issues in one defect
- ❌ Set everything as Critical
- ❌ Forget to test on multiple browsers

---

## Example Defect Report

```markdown
# Defect Report: DEF-001

## Basic Information
| Field | Value |
|-------|-------|
| **Defect ID** | DEF-001 |
| **Title** | CSV column detection fails for European date format |
| **Feature** | F1 - Smart Data Ingestion |
| **Severity** | High |
| **Priority** | P1 |
| **Environment** | Staging |
| **Browser** | Chrome 122 |
| **OS** | Windows 11 |
| **Date Reported** | 2026-02-27 |
| **Reported By** | QA Engineer |
| **Assigned To** | Backend Developer |
| **Status** | In Progress |

## Defect Description
### Summary
Auto-detection fails to recognize DD/MM/YYYY date format, causing date column to be unmapped.

### Detailed Description
When uploading a CSV with European date format (DD/MM/YYYY), the system fails to detect the date column and marks it as "Unassigned". This requires manual correction for all European bank exports.

## Steps to Reproduce
1. Navigate to Import page
2. Upload `test-wells-fargo-eu.csv` (attached)
3. Observe column detection screen
4. Check Date column mapping

## Expected Result
- Date column detected with 90%+ confidence
- Format recognized as DD/MM/YYYY
- Column auto-mapped to "Date"

## Actual Result
- Date column shows "Unassigned"
- Detection confidence: 0%
- User must manually select "Date" and specify format

## Evidence
### Screenshot
[Attached: column-detection-failure.png]

### Logs
```
2026-02-27 10:15:32 ERROR [detection] Failed to parse date: 15/01/2024
2026-02-27 10:15:32 WARN  [detection] Date column confidence: 0.0
```

### Test Data
File: `test-wells-fargo-eu.csv`
```csv
Date,Description,Amount
15/01/2024,ACME CORP,1250.00
16/01/2024,OFFICE DEPOT,-45.67
```

## Impact Assessment
### User Impact
- All European users affected
- Workaround: Manual column mapping required
- Adds 2-3 minutes per import

### Business Impact
- Affects ~30% of target market
- Not a blocker but significant friction

## Related Information
### Related Test Cases
- F1-E1-S2.5: Different Date Format Detection

### Requirements Reference
- f1.md Story 1.2: Auto-Detect CSV Columns
- Requirement: "Detection accuracy ≥ 85%"

## Root Cause Analysis (Filled by Dev)
### Cause Category
- [x] Code defect
- [ ] Design issue
- [ ] Environment issue
- [ ] Data issue
- [ ] Requirement gap
- [ ] Third-party issue
- [ ] Other

### Technical Details
Date parser only tries MM/DD/YYYY and YYYY-MM-DD formats. Need to add DD/MM/YYYY detection and use locale context.

## Fix Verification (Filled by QA)
### Fix Version
v1.2.3

### Verification Steps
1. Uploaded `test-wells-fargo-eu.csv`
2. Verified date column auto-detected
3. Verified confidence > 85%
4. Verified preview shows correct dates

### Verification Result
- [x] Defect fixed
- [ ] Defect partially fixed
- [ ] Defect not fixed
- [ ] New issues introduced

### Regression Test
- [x] All F1 date format tests passed
- [x] No new defects introduced
```

---

**Template Version:** 1.0
**Last Updated:** 2026-02-27
