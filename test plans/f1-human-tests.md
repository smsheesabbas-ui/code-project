# Feature 1: Smart Data Ingestion Engine - Human Test Plan

## Overview
Tests for CSV upload, column detection, preview, data normalization, duplicate detection, and error handling.

---

## EPIC 1: CSV Import System

### Test Case F1-E1-S1.1: Upload Valid CSV File

**Objective:** Verify successful CSV file upload with valid format

**Preconditions:**
- User is logged in
- Valid CSV file available (sample: 100 transactions, 5 columns)

**Steps:**
1. Navigate to "Import" page
2. Click "Upload CSV" button
3. Select valid CSV file from file picker
4. Wait for upload to complete
5. Observe progress indicator

**Expected Results:**
- Progress indicator shows upload progress (0-100%)
- Upload completes within 10 seconds for 10k rows
- Success message appears: "File uploaded successfully"
- System proceeds to column detection screen

**Pass Criteria:**
- Upload completes without errors
- File reaches backend (verify via browser network tab or backend logs)
- Progress indicator is visible and accurate

---

### Test Case F1-E1-S1.2: Drag and Drop CSV Upload

**Objective:** Verify drag-and-drop functionality for CSV upload

**Preconditions:**
- User is on Import page
- Valid CSV file available on desktop

**Steps:**
1. Navigate to "Import" page
2. Drag CSV file from file explorer to upload zone
3. Drop file in designated area
4. Observe upload behavior

**Expected Results:**
- Drag-over zone highlights when file is dragged
- Drop triggers file upload
- Same success flow as Test F1-E1-S1.1

**Pass Criteria:**
- Drag and drop works on desktop browsers
- Visual feedback provided during drag operation

---

### Test Case F1-E1-S1.3: Invalid File Type Rejection

**Objective:** Verify system rejects non-CSV files

**Preconditions:**
- User is on Import page

**Steps:**
1. Navigate to "Import" page
2. Attempt to upload PDF file
3. Attempt to upload XLSX file
4. Attempt to upload TXT file
5. Attempt to upload JPG file

**Expected Results:**
- Each non-CSV file is rejected immediately
- Clear error message: "Only CSV files are supported. Please upload a .csv file."
- No backend processing attempted

**Pass Criteria:**
- File rejected at client side when possible
- Error message is human-readable, no technical jargon
- Upload button disabled for invalid files

---

### Test Case F1-E1-S1.4: Oversized File Rejection

**Objective:** Verify 10MB file size limit enforcement

**Preconditions:**
- User is on Import page
- CSV file > 10MB available

**Steps:**
1. Navigate to "Import" page
2. Attempt to upload 15MB CSV file
3. Attempt to upload 10.1MB CSV file
4. Attempt to upload exactly 10MB file

**Expected Results:**
- Files > 10MB rejected with message: "File too large. Maximum size is 10MB."
- 10MB file accepted (boundary test)

**Pass Criteria:**
- Size validation occurs before upload processing
- Clear error message with size limit specified

---

### Test Case F1-E1-S1.5: Empty File Handling

**Objective:** Verify system handles empty CSV files gracefully

**Preconditions:**
- Empty CSV file (0 bytes) available

**Steps:**
1. Navigate to "Import" page
2. Upload empty CSV file

**Expected Results:**
- Error message: "The uploaded file is empty. Please check your file and try again."
- No system crash or hang

**Pass Criteria:**
- Graceful error handling
- User can retry with different file

---

### Test Case F1-E1-S2.1: Auto-Detect Standard Bank CSV Columns

**Objective:** Verify automatic column detection for standard bank format

**Preconditions:**
- Valid CSV uploaded with headers: Date, Description, Amount, Balance

**Steps:**
1. Upload standard bank CSV (sample data provided in test-data.md)
2. Observe column detection screen
3. Review auto-detected column mappings

**Expected Results:**
- Date column detected and highlighted
- Description column detected and highlighted
- Amount column detected and highlighted
- Balance column detected (optional)
- Detection confidence score displayed (≥85% target)

**Pass Criteria:**
- All 4 standard columns correctly identified
- Confidence score visible
- Green indicators for detected columns

---

### Test Case F1-E1-S2.2: Auto-Detect Debit/Credit Split Columns

**Objective:** Verify detection of separate Debit and Credit columns

**Preconditions:**
- CSV with separate Debit and Credit columns uploaded

**Steps:**
1. Upload CSV with Debit/Credit split format
2. Review column detection

**Expected Results:**
- System recognizes split amount format
- Both Debit and Credit columns detected
- System understands they represent signed amounts

**Pass Criteria:**
- Split columns correctly interpreted
- No data loss or misinterpretation

---

### Test Case F1-E1-S2.3: Manual Column Override

**Objective:** Verify user can manually correct auto-detected columns

**Preconditions:**
- CSV uploaded with columns detected

**Steps:**
1. Review auto-detected columns
2. Click on misdetected column mapping
3. Select correct column type from dropdown
4. Click "Apply Changes"
5. Observe preview update

**Expected Results:**
- Dropdown shows options: Date, Description, Amount, Debit, Credit, Balance, Ignore
- Manual selection overrides auto-detection
- Preview updates to reflect new mapping
- Manual choice persisted for this import session

**Pass Criteria:**
- Manual override is possible for all columns
- Preview reflects changes immediately

---

### Test Case F1-E1-S2.4: Missing Header Handling

**Objective:** Verify system handles CSV files without headers

**Preconditions:**
- CSV file without header row available

**Steps:**
1. Upload CSV without headers
2. Observe system behavior

**Expected Results:**
- System detects missing headers
- Prompts user: "No headers detected. Please assign column meanings."
- All columns shown as "Unassigned"
- User can manually assign all columns

**Pass Criteria:**
- Missing headers detected
- Manual assignment workflow triggered
- Import can still proceed after manual assignment

---

### Test Case F1-E1-S2.5: Different Date Format Detection

**Objective:** Verify system handles various date formats

**Preconditions:**
- CSVs with different date formats available:
  - MM/DD/YYYY
  - DD/MM/YYYY
  - YYYY-MM-DD
  - DD-MM-YYYY

**Steps:**
1. Upload CSV with MM/DD/YYYY dates
2. Verify dates parsed correctly in preview
3. Repeat for each date format

**Expected Results:**
- All standard date formats correctly parsed
- Preview shows dates in consistent display format
- No date misinterpretation (e.g., 02/03/2024 not confused between Feb 3 and Mar 2)

**Pass Criteria:**
- Common date formats handled correctly
- Preview reflects correct dates

---

### Test Case F1-E1-S3.1: Preview First 20 Rows

**Objective:** Verify preview displays first 20 rows correctly

**Preconditions:**
- CSV with > 20 rows uploaded and columns mapped

**Steps:**
1. Complete column mapping
2. Click "Preview"
3. Review displayed data

**Expected Results:**
- First 20 rows displayed in table format
- All mapped columns visible
- Data aligned correctly under headers
- Column highlighting shows mapped columns in different colors

**Pass Criteria:**
- Exactly 20 rows shown (or fewer if file is smaller)
- All columns mapped correctly
- Data displayed accurately from source file

---

### Test Case F1-E1-S3.2: Preview Performance Under 2 Seconds

**Objective:** Verify preview loads quickly

**Preconditions:**
- CSV with 10,000 rows uploaded

**Steps:**
1. Click "Preview" button
2. Time the load using stopwatch

**Expected Results:**
- Preview appears within 2 seconds
- Progress indicator shown during load

**Pass Criteria:**
- Load time < 2 seconds for standard file sizes

---

### Test Case F1-E1-S3.3: Back Button from Preview

**Objective:** Verify user can go back from preview to edit mappings

**Preconditions:**
- User is on Preview screen

**Steps:**
1. Click "Back" button on preview screen
2. Modify column mappings
3. Return to preview

**Expected Results:**
- Back button returns to column mapping screen
- Previous mappings retained but editable
- Preview updates after changes

**Pass Criteria:**
- Navigation works bidirectionally
- Changes persist within session

---

### Test Case F1-E1-S3.4: Cancel Import from Preview

**Objective:** Verify user can cancel import without saving

**Preconditions:**
- User is on Preview screen

**Steps:**
1. Click "Cancel" button
2. Confirm cancellation in dialog
3. Check database for new records

**Expected Results:**
- Confirmation dialog: "Are you sure? No data will be saved."
- Upon confirmation, returned to Import start page
- No transactions saved to database
- Original file deleted from temporary storage

**Pass Criteria:**
- Cancel prevents data persistence
- No orphaned data in database

---

## EPIC 2: Data Normalization & Storage

### Test Case F1-E2-S2.1: Duplicate Transaction Detection

**Objective:** Verify duplicate detection based on date, amount, description

**Preconditions:**
- User has existing transactions in system
- Uploading CSV with some duplicate transactions

**Steps:**
1. Import CSV with known duplicates (same date, amount, description)
2. Proceed to preview
3. Observe duplicate flagging
4. Choose "Skip Duplicates" option
5. Complete import
6. Verify database state

**Expected Results:**
- Duplicate rows highlighted in preview
- User option: Skip, Overwrite, or Import Anyway
- Skipped duplicates not added to database
- Duplicates detected based on: same date + amount + similar description + same user

**Pass Criteria:**
- Duplicates correctly identified (≥95% accuracy target)
- User choice respected
- No duplicate data stored when "Skip" selected

---

### Test Case F1-E2-S2.2: Legitimate Similar Transactions Not Flagged

**Objective:** Verify legitimate similar transactions are not incorrectly flagged

**Preconditions:**
- User has recurring daily/weekly transactions (e.g., coffee purchases)

**Steps:**
1. Import CSV with recurring same-vendor transactions
2. Review duplicate detection

**Expected Results:**
- Recurring transactions on different dates NOT flagged as duplicates
- Only true duplicates (same date + amount) flagged

**Pass Criteria:**
- False positive rate < 5%
- Recurring payments handled correctly

---

### Test Case F1-E2-S2.3: Partial Import with Duplicates

**Objective:** Verify partial import works when some rows are duplicates

**Preconditions:**
- CSV with mix of new and duplicate transactions

**Steps:**
1. Import CSV with 50% new, 50% duplicates
2. Select "Skip Duplicates"
3. Complete import

**Expected Results:**
- New transactions imported successfully
- Duplicates skipped
- Import summary shows: "50 imported, 50 skipped (duplicates)"

**Pass Criteria:**
- Partial import succeeds
- Accurate summary statistics

---

### Test Case F1-E2-S3.1: Confirm Import Saves Data

**Objective:** Verify "Confirm & Save" persists transactions

**Preconditions:**
- User on Preview screen with valid data

**Steps:**
1. Review preview data
2. Click "Confirm & Save"
3. Wait for processing
4. Navigate to Transactions page

**Expected Results:**
- Loading indicator shows during processing
- Success message: "100 transactions imported successfully"
- All transactions visible in Transactions page
- Dates in ISO format (YYYY-MM-DD)
- Amounts stored as signed numbers
- Import metadata (timestamp, source file) stored

**Pass Criteria:**
- All transactions persisted to database
- Data correctly normalized
- Import audit trail created

---

## EPIC 3: Error Handling & Data Integrity

### Test Case F1-E3-S1.1: Clear Error Messages for Invalid Data

**Objective:** Verify human-readable error messages for data issues

**Preconditions:**
- CSV with various data errors prepared

**Steps:**
1. Upload CSV with:
   - Invalid dates (e.g., "not a date")
   - Invalid amounts (e.g., "$abc")
   - Empty required fields
2. Review error messages

**Expected Results:**
- Row 15: "Invalid date format. Expected: YYYY-MM-DD, MM/DD/YYYY, or DD/MM/YYYY"
- Row 23: "Invalid amount. Please enter a valid number."
- Row 31: "Missing required field: Description"
- No technical stack traces shown
- Row numbers clearly indicated

**Pass Criteria:**
- Errors are human-readable
- Specific row numbers provided
- Fix suggestions included

---

### Test Case F1-E3-S1.2: Inline Row Editing Before Import

**Objective:** Verify user can edit problematic rows before import

**Preconditions:**
- Preview screen showing flagged rows with errors

**Steps:**
1. Click on row with invalid date
2. Inline edit field appears
3. Correct the date value
4. Click "Save Edit"
5. Complete import

**Expected Results:**
- Inline editing enabled for flagged rows
- Edited values validated before save
- Error flag removed after valid edit
- Corrected data imported

**Pass Criteria:**
- Row editing works for all data types
- Validation on edit
- Changes persist to import

---

### Test Case F1-E3-S1.3: Skip Invalid Rows Option

**Objective:** Verify option to skip invalid rows

**Preconditions:**
- CSV with some invalid rows

**Steps:**
1. Upload CSV with mixed valid/invalid rows
2. Choose "Skip Invalid Rows" option
3. Complete import

**Expected Results:**
- Valid rows imported
- Invalid rows skipped with summary
- Message: "95 imported successfully, 5 skipped due to errors"
- List of skipped rows with reasons available

**Pass Criteria:**
- Partial import succeeds
- Skipped rows logged
- No data corruption

---

### Test Case F1-E3-S3.1: Edit Transactions After Import

**Objective:** Verify post-import transaction editing

**Preconditions:**
- Transactions already imported and visible

**Steps:**
1. Navigate to Transactions page
2. Click edit icon on a transaction
3. Modify date, description, or amount
4. Save changes
5. Verify audit trail

**Expected Results:**
- Edit form opens with current values
- Changes saved immediately
- Audit log shows: original value → new value, timestamp, user
- Updated values reflect in all reports

**Pass Criteria:**
- Edit UI functional
- Changes persist
- Audit trail maintained

---

### Test Case F1-E3-S3.2: Mobile Responsive Upload

**Objective:** Verify upload works on mobile devices

**Preconditions:**
- Mobile device or emulator

**Steps:**
1. Open application on mobile browser
2. Navigate to Import page
3. Attempt CSV upload
4. Review column detection screen
5. Review preview screen

**Expected Results:**
- Upload button accessible
- File picker opens correctly
- Column detection UI scrollable and usable
- Preview table horizontally scrollable
- All buttons reachable

**Pass Criteria:**
- Import flow usable on mobile
- No layout breaks
- Touch targets minimum 44px

---

## Regression Test Checklist

Execute these tests when modifying F1 code:

- [ ] F1-E1-S1.1: Valid CSV upload
- [ ] F1-E1-S1.3: Invalid file rejection
- [ ] F1-E1-S2.1: Auto-detection accuracy
- [ ] F1-E1-S3.1: Preview functionality
- [ ] F1-E2-S2.1: Duplicate detection
- [ ] F1-E3-S1.1: Error message clarity
- [ ] F1-E3-S3.2: Mobile responsive

---

**Test Plan Version:** 1.0
**Last Updated:** 2026-02-27
**Test Data Reference:** test-data.md
