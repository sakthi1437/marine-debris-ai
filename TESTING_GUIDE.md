# Marine Debris UI - Comprehensive Testing Guide

## Pre-Test Requirements
- Application compiled and running
- X11/Wayland display available
- SQLite database initialized

## Test Suite

### TEST 1: Application Startup and Layout
**Objective**: Verify the application starts with correct layout structure

**Steps**:
1. Start application: `.venv/bin/python desktop_app.py`
2. Verify main window displays with title "Marine Debris Analysis Tool"
3. Verify title reads "SIDE SCAN SONAR INTELLIGENCE WORKSTATION"
4. Check for 4 panel sections:
   - Left: INPUT LOCATION with collapse button (▼)
   - Center: SONAR IMAGE VIEWER with collapse button (▼)
   - Right: DETECTION RESULTS with collapse button (▼)
   - Bottom: ANALYSIS HISTORY with collapse button (▼)

**Expected Result**: 
- Window displays with all panels visible
- Panels properly arranged horizontally
- History panel at bottom
- All collapse buttons present and functional

---

### TEST 2: Horizontal Resizing (LEFT | CENTER | RIGHT)
**Objective**: Verify users can resize panels horizontally

**Steps**:
1. Locate splitter handle between INPUT LOCATION and SONAR IMAGE VIEWER
2. Click and drag handle to the LEFT
3. Verify INPUT LOCATION shrinks and VIEWER expands
4. Drag back to the RIGHT
5. Verify INPUT LOCATION expands
6. Locate splitter between VIEWER and DETECTION RESULTS
7. Drag handle to enlarge DETECTION RESULTS
8. Verify table columns become more visible
9. Drag back to restore balance

**Expected Result**:
- Splitters respond smoothly to dragging
- Panels resize appropriately
- No frozen or stuck splitters
- Panels maintain minimum usable sizes

---

### TEST 3: Vertical Resizing (TOP WORKSPACE | HISTORY)
**Objective**: Verify users can resize the history section vertically

**Steps**:
1. Locate splitter between top workspace and ANALYSIS HISTORY
2. Click and drag handle UPWARD
3. Verify history table shrinks, workspace expands
4. Drag handle DOWNWARD
5. Verify history table expands, workspace shrinks

**Expected Result**:
- Vertical splitter responds smoothly
- History visible at all times
- Workspace remains usable when resized

---

### TEST 4: Collapse INPUT LOCATION Panel
**Objective**: Verify INPUT LOCATION panel collapses/expands

**Steps**:
1. Locate collapse button (▼) in INPUT LOCATION panel header
2. Click the collapse button
3. Verify:
   - Panel content disappears
   - Collapse button changes to (▲)
   - SONAR VIEWER and DETECTION RESULTS expand to use freed space
4. Click collapse button again to expand
5. Verify:
   - Panel content reappears
   - Collapse button changes back to (▼)
   - Layout restored

**Expected Result**:
- Panel collapses/expands cleanly
- No visual glitches
- Other panels adjust automatically

---

### TEST 5: Collapse SONAR IMAGE VIEWER Panel
**Objective**: Verify SONAR VIEWER panel collapses/expands

**Steps**:
1. Locate collapse button (▼) in SONAR IMAGE VIEWER header
2. Click to collapse
3. Verify button changes to (▲) and content disappears
4. INPUT LOCATION and DETECTION RESULTS should expand
5. Click again to expand

**Expected Result**:
- Same as TEST 4 but for center panel
- Image tabs not accessible when collapsed

---

### TEST 6: Collapse DETECTION RESULTS Panel
**Objective**: Verify DETECTION RESULTS panel collapses/expands

**Steps**:
1. Locate collapse button (▼) in DETECTION RESULTS header
2. Click to collapse
3. Verify button changes to (▲) and table/buttons disappear
4. Other panels expand
5. Click to expand

**Expected Result**:
- Panel collapses/expands
- Table and export buttons hidden when collapsed

---

### TEST 7: Collapse ANALYSIS HISTORY Panel
**Objective**: Verify ANALYSIS HISTORY panel collapses/expands

**Steps**:
1. Locate collapse button (▼) in ANALYSIS HISTORY header
2. Click to collapse
3. Verify history table disappears, workspace expands
4. History header remains visible with button at (▲)
5. Click to expand
6. History table reappears

**Expected Result**:
- History section independently collapsible
- Workspace gains significant vertical space when collapsed

---

### TEST 8: Multiple Panels Collapsed
**Objective**: Verify multiple panels can be collapsed simultaneously

**Steps**:
1. Collapse INPUT LOCATION
2. Collapse SONAR VIEWER
3. Verify DETECTION RESULTS panel fills most of workspace
4. Expand both panels
5. Verify original layout restored

**Expected Result**:
- Panels collapse independently
- Layout updates correctly
- No conflicts or overlapping

---

### TEST 9: History Refresh Button
**Objective**: Verify Refresh button reloads history from database

**Steps**:
1. Create an analysis (or load from existing history)
2. Note history row count
3. Click "Refresh" button in ANALYSIS HISTORY header
4. Verify table reloads

**Expected Result**:
- History table updates
- No database errors
- Records persist correctly

---

### TEST 10: History Row Selection
**Objective**: Verify users can select history rows

**Steps**:
1. Ensure history table has at least 2 records
2. Click on first row
3. Verify row highlighted
4. Hold Ctrl and click second row
5. Verify both rows highlighted

**Expected Result**:
- Row selection works
- Multiple rows selectable with Ctrl+Click
- Selection clearly visible

---

### TEST 11: Delete Single History Record
**Objective**: Verify deletion of single history record

**Steps**:
1. Select one history record
2. Click "Delete Selected" button
3. Confirmation dialog appears: "Delete 1 selected history record(s)? This cannot be undone."
4. Click "Yes"
5. Verify:
   - Record removed from table
   - Status message: "Deleted 1 history record(s)."
6. Close and restart application
7. Verify record does NOT reappear

**Expected Result**:
- Record deleted from both UI and database
- Confirmation dialog works
- Deletion persists after restart

---

### TEST 12: Delete Multiple History Records
**Objective**: Verify deletion of multiple history records

**Steps**:
1. Select 2-3 history records (Ctrl+Click)
2. Click "Delete Selected" button
3. Confirmation shows correct count
4. Click "Yes"
5. Verify all selected records deleted
6. Status message shows correct count
7. Restart app to verify persistence

**Expected Result**:
- Multiple records deleted simultaneously
- Database reflects changes
- Persistence verified

---

### TEST 13: Clear All History
**Objective**: Verify Clear All History functionality

**Steps**:
1. Ensure history table has records
2. Click "Clear All History" button
3. Confirmation dialog: "Clear all analysis history? This cannot be undone."
4. Click "No"
5. Verify history table unchanged
6. Click "Clear All History" again
7. Click "Yes"
8. Verify:
   - All records removed
   - Status: "Analysis history cleared."
   - Table empty
9. Restart application
10. Verify table still empty

**Expected Result**:
- Cancellation works (No button)
- Confirmation works (Yes button)
- All records deleted from database
- Persistence verified

---

### TEST 14: No Selection Error Handling
**Objective**: Verify error when attempting delete with no selection

**Steps**:
1. Click in history table to deselect all
2. Click "Delete Selected" button
3. Verify information dialog: "No selection - Select at least one history record to delete."
4. Click OK

**Expected Result**:
- Dialog appears
- No deletion occurs
- No database errors

---

### TEST 15: History Row Click Behavior
**Objective**: Verify clicking history row reloads analysis

**Steps**:
1. Ensure history table has records with stored images
2. Click on a history row
3. Verify:
   - Images display in viewer panels
   - Detection results populate table
   - Status message shows: "Reloaded analysis [survey_id]"

**Expected Result**:
- Analysis data loads correctly
- No interference with delete selection mode

---

### TEST 16: Window Resizing
**Objective**: Verify layout adapts to window resizing

**Steps**:
1. Maximize window
2. Verify panels scale properly
3. Verify all elements remain visible
4. Restore window to smaller size
5. Verify panels adapt
6. Drag window edges to resize gradually
7. Verify no elements get cut off

**Expected Result**:
- Layout responsive to window size
- All panels remain usable
- Splitters adjust correctly

---

### TEST 17: Layout Persistence
**Objective**: Verify layout state is saved and restored

**Steps**:
1. Resize horizontal splitters to custom positions (e.g., 200px, 800px, 480px)
2. Resize vertical splitter to custom position (e.g., 500px, 400px)
3. Collapse INPUT LOCATION panel
4. Close application
5. Restart application
6. Verify:
   - Horizontal splitter positions restored
   - Vertical splitter positions restored
   - INPUT LOCATION panel still collapsed

**Expected Result**:
- User layout preferences saved in QSettings
- Layout restored on application restart
- Settings persist across sessions

---

### TEST 18: Existing Functionality - Image Analysis
**Objective**: Verify analysis functionality still works

**Steps**:
1. Click "Browse image" button
2. Select a test sonar image
3. File displays in drop area
4. Click "ANALYZE SONAR IMAGE" button
5. Wait for processing
6. Verify:
   - Original tab displays original image
   - Processed tab displays processed image
   - Annotated tab shows detections
   - Detection table populates
7. Results persist in history after refresh

**Expected Result**:
- Analysis execution unchanged
- Image display works
- Detection table populated
- History records saved

---

### TEST 19: Existing Functionality - Export
**Objective**: Verify export features still work

**Steps**:
1. Load analysis results (run or reload from history)
2. Click "Export JSON" button
3. Choose save location
4. Verify JSON file created with correct content
5. Click "Export CSV" button
6. Verify CSV file created with correct format

**Expected Result**:
- Export functionality unchanged
- Files created with correct data
- No corrupted or missing fields

---

### TEST 20: Existing Functionality - Location Modes
**Objective**: Verify location source selection still works

**Steps**:
1. Verify default mode is "Manual"
2. Change to "Phone GPS" - verify UI updates
3. Change to "Metadata" - load a metadata file
4. Change back to "Manual"
5. Verify location_note label updates correctly

**Expected Result**:
- Location mode switching works
- Manual lat/long editable
- Metadata loading works
- GPS polling in background works

---

## Test Execution Summary

Run all 20 tests in sequence:
```bash
cd /home/sakthivel/Documents/marine-debris-ai
.venv/bin/python desktop_app.py
# Execute tests 1-20
# Document results
```

## Success Criteria
- All 20 tests pass
- No UI crashes or glitches
- No database errors
- All deletions persist after restart
- Layout changes persist after restart
- All original features work unchanged

## Regression Testing
After each modification, re-run:
- TEST 18: Existing Functionality - Image Analysis
- TEST 19: Existing Functionality - Export
- TEST 20: Existing Functionality - Location Modes

## Notes
- Use real sonar images for more realistic testing
- Test on different screen resolutions
- Test with multiple history records (10+)
- Test with very long filenames in history
