# Presales Weekly Tracker Web App — Implementation Prompt

## Goal
Build a clean, professional internal web app for the Presales team to enter and maintain all weekly reporting data currently stored in the provided Excel workbook:

`Presales_Weekly_Tracker(Consolidated_August).xlsx`

The web app must make data entry much easier than editing Excel directly, while the **same Excel workbook remains the backend/source of truth**.

Users should be able to:
1. Select the type of report/activity they want to update.
2. Fill a simple form containing every relevant Excel column.
3. Submit the form and append/update the correct Excel sheet.
4. View recent entries and basic submission status.
5. Download the entire latest Excel workbook at any time using one button.

This is an internal V1. Prioritize correct functionality, data integrity, and a polished simple UI over unnecessary complexity.

---

## Source Workbook
Use the supplied workbook as the master template. Do **not** recreate the workbook from scratch and do **not** rename sheets, headers, formulas, or change the workbook structure unless absolutely required.

Workbook sheets:

1. `Client Managers Target` — reference/read-only
2. `Column Guide` — reference/read-only
3. `Weekly Review` — editable through form
4. `Weekly meeting` — editable through form
5. `Training Attended` — editable through form
6. `Training Conducted` — editable through form
7. `PoC Tracker` — editable through form
8. `Customer Workshop` — editable through form
9. `Win-Lost` — editable through form
10. `Status` — display/update submission status

Keep the original `.xlsx` file inside a backend `data/` folder as something like:

`data/Presales_Weekly_Tracker.xlsx`

Never overwrite the master template during development. Keep an untouched copy such as:

`data/Presales_Weekly_Tracker_TEMPLATE.xlsx`

---

# Recommended Stack
Use a simple maintainable stack:

- Frontend: React + Vite + TypeScript
- Styling: Tailwind CSS
- UI components: shadcn/ui or lightweight equivalent
- Icons: Lucide
- Backend: Python FastAPI
- Excel handling: `openpyxl`
- File locking: `portalocker` or equivalent

Do not add a database in V1. The Excel workbook is the data store.

Structure the project cleanly:

```text
presales-tracker/
  frontend/
  backend/
    app/
    data/
      Presales_Weekly_Tracker.xlsx
      Presales_Weekly_Tracker_TEMPLATE.xlsx
      backups/
  README.md
```

---

# Core UI / UX

## Overall Design
Create a clean modern enterprise dashboard.

Visual direction:
- White/light grey background
- Navy/blue primary accent
- Minimal borders
- Rounded cards
- Clear typography
- Plenty of whitespace
- Responsive for laptop/tablet
- Avoid flashy gradients, animations, glassmorphism, or excessive colors

The app should feel like a professional internal business tool.

## Main Layout
Use a persistent left sidebar and top header.

Sidebar:
- Dashboard
- Weekly Review
- Weekly Meetings
- Training Attended
- Training Conducted
- PoC Tracker
- Customer Workshop
- Win / Lost
- Client Manager Targets
- Column Guide

Top header:
- App name: `Presales Weekly Tracker`
- Selected Presales User
- Current reporting month/week
- `Download Excel` button

Use a user selector in the header so the user can select their Presales name. Do not implement complicated authentication in V1.

Suggested existing Presales users from the workbook:
- Aditya
- Arun
- Ayush
- Irshad
- Kalim
- Surender
- Suraj
- Ankesh

Allow the list to be derived from the `Status` sheet instead of hardcoding where practical.

---

# Dashboard
The landing page should immediately show what the user needs to update.

Display:
- Selected Presales person
- Reporting month
- Current week
- Total Weekly Review entries
- Total Meetings
- Training Attended count
- Training Conducted count
- Active PoCs
- Customer Workshops
- Win/Lost entries

Add a `Weekly Submission Status` card showing:
- Weekly Review
- Weekly Meeting
- Training Attended
- Training Conducted
- PoC Tracker
- Customer Workshop

Use status badges such as:
- Pending
- Completed

Read this data from the existing `Status` sheet.

Each module should have a quick `Add Entry` button.

Also show a small `Recent Activity` table using the latest rows entered by the selected Presales user.

Do not build complex analytics for V1.

---

# Form Modules and Exact Excel Fields

## 1. Weekly Review
Target sheet: `Weekly Review`

Header row in current workbook: row 5.

Fields, in this exact order:
1. Region
2. AM
3. Presales
4. Customer
5. Date of Opportunity (MM/YY)
6. Opportunity Details
7. NN/EC (New Opportunity/Existing Customer)
8. Value (₹)
9. OEM
10. Stage
11. Expected Closure (QTR)
12. Month
13. Remarks
14. Week 1
15. Week 2
16. Week 3
17. Week 4

Recommended controls:
- Region: dropdown — West / South / North
- Presales: auto-filled from selected user, editable only if needed
- Date of Opportunity: month/year picker
- NN/EC: dropdown — New Opportunity / Existing Customer
- Value: numeric currency input
- Stage: dropdown — Funnel / Upside / Commit / Win / Lost
- Expected Closure: dropdown — Q1 / Q2 / Q3 / Q4
- Month: month selector
- Remarks and Week fields: multiline text areas

For Week 1–4, make the form easier to use by highlighting the currently selected/current reporting week while still allowing all four fields to be edited.

---

## 2. Weekly Meetings
Target sheet: `Weekly meeting`

Header row: row 5.

Fields:
1. Sr. No.
2. Region
3. Month
4. Week
5. Date
6. Presales
7. Client Manager
8. Account Name
9. Account Type(New/Existing)
10. Meeting Mode (In-Person/Virtual)
11. Meeting Agenda
12. Discussion Points
13. Action Items
14. Remarks

Behavior:
- `Sr. No.` should be generated automatically from the highest existing serial number + 1.
- Presales auto-filled from selected user.
- Week dropdown: 1 / 2 / 3 / 4 / 5
- Account Type dropdown: New / Existing
- Meeting Mode dropdown: In-Person / Virtual
- Discussion Points, Action Items and Remarks: multiline text areas

---

## 3. Training Attended
Target sheet: `Training Attended`

Header row: row 5.

Fields:
1. Sr No.
2. Region
3. Date
4. PreSales Name
5. Training Name
6. OEM
7. Technology Vertical
8. Certification Done

Behavior:
- Auto-generate Sr No.
- PreSales Name auto-filled.
- Certification Done dropdown: Yes / No / Ongoing / NA

---

## 4. Training Conducted
Target sheet: `Training Conducted`

Header row: row 5.

Fields:
1. Sr No.
2. Region
3. Date
4. PreSales Name
5. Training Name
6. OEM
7. Technology Vertical
8. Certification

Behavior:
- Auto-generate Sr No.
- PreSales Name auto-filled.

---

## 5. PoC Tracker
Target sheet: `PoC Tracker`

Header row: row 5.

Fields:
1. Sr. No.
2. Region
3. Date
4. Presales
5. Client Manager
6. Customer
7. PoC Details
8. OEM
9. Expected Completion Date
10. Month
11. Week 1
12. Week 2
13. Week 3
14. Week 4

Behavior:
- Auto-generate Sr. No.
- Presales auto-filled.
- Date pickers for Date and Expected Completion Date.
- Week status fields are multiline text areas.
- Highlight the current reporting week.

---

## 6. Customer Workshop
Target sheet: `Customer Workshop`

Header row: row 5.

Fields:
1. Sr. No.
2. Region
3. Date
4. Presales
5. Client Manager
6. Customer
7. Workshop Details
8. OEM
9. Month

Behavior:
- Auto-generate Sr. No.
- Presales auto-filled.

---

## 7. Win / Lost
Target sheet: `Win-Lost`

Header row: row 3, columns B:H.

Fields:
1. PO Date
2. Region
3. Presales
4. Account Name
5. Win/Lost
6. Deal Value
7. Remark

Behavior:
- Win/Lost dropdown: Win / Lost
- Deal Value numeric currency input
- Presales auto-filled.

Important: The workbook currently contains a `Total PO Received` formula/summary area. Preserve existing formulas and do not overwrite summary rows. Insert new Win/Lost records into the available data-entry area before the summary row or safely expand the data region while keeping the total formula correct.

If insertion causes the total formula range to require extension, update the formula safely.

---

# Read-Only Screens

## Client Managers Target
Read data from `Client Managers Target` and show a clean table grouped by region:
- West / Mumbai
- South / Bangalore
- North / Gurugram

Show AM Name and Q1/Q2/Q3/Q4 values.

Format target amounts in Indian Rupee formatting.

Do not modify this sheet from the UI in V1.

## Column Guide
Render the content of `Column Guide` as a simple searchable help/reference page.

Show each column name and its explanation in cards or a two-column table.

---

# Excel Backend Rules — Critical

The Excel file must remain the source of truth.

## Never Rebuild the Workbook
Do not create a new workbook from the submitted form data.

Instead:
1. Load the existing workbook.
2. Locate the correct target sheet.
3. Find the correct insertion row.
4. Write only the submitted values.
5. Preserve existing formatting, merged cells, formulas, sheet names, widths, colors, and other sheets.
6. Save the same workbook safely.

## Preserve Formatting
When inserting a new row, copy formatting from the previous normal data row where appropriate so the workbook continues looking consistent when downloaded.

Preserve:
- fonts
- fills
- borders
- alignment
- date formats
- currency formats
- row heights

## Dates
Store dates as actual Excel date values, not display strings.

Apply the appropriate existing date formatting from surrounding rows.

## Currency
Store deal values as numbers, not strings with `₹` included.

## Empty Fields
Write truly empty cells where optional fields are blank. Do not write strings like `null` or `undefined`.

## Atomic Writes and File Locking
Multiple team members may submit at nearly the same time.

Implement a lock around every workbook write.

Suggested flow:
1. Acquire file lock.
2. Load latest workbook from disk.
3. Apply change.
4. Save to a temporary file.
5. Validate that the temporary workbook can be opened.
6. Atomically replace the active workbook.
7. Release the lock.

Do not let simultaneous requests overwrite each other.

## Backup
Before a successful write, maintain automatic rolling backups in:

`backend/data/backups/`

At minimum, retain the latest 10 backups or one backup per day.

Provide an admin-safe recovery path in the README.

---

# Status Sheet Behavior
Target sheet: `Status`

Existing columns:
- Presales Name
- Weekly Review
- Weekly Meeting
- Training Attended
- Training Conducted
- PoC Tracker
- Customer Workshop
- Up to

The dashboard should read these statuses.

For each form module, add a small `Mark section completed` action.

When clicked:
- Find the selected Presales user in `Status`.
- Change the relevant module cell from `Pending` to `Completed`.
- Update `Up to` with the latest reporting date/week information in a human-readable form.

Do not automatically mark a module complete just because one row was entered. A user may need to enter multiple rows first.

Allow the user to reopen/reset a section to `Pending` if needed.

---

# Existing Data / Recent Entries
Every form screen should also show a table below the form containing the latest entries from that sheet.

Features:
- Default filter to selected Presales user.
- Search text box.
- Month filter where relevant.
- Region filter.
- Show the latest 20–50 rows.

For V1, do not implement destructive delete unless it is safe.

If editing is implemented, it must update the exact workbook row rather than creating duplicates.

Prefer `Add Entry` + read-only recent rows first; add edit only if implementation remains simple and reliable.

---

# Download Excel
Add a prominent `Download Excel` button in the top-right header.

Backend endpoint example:

`GET /api/workbook/download`

Requirements:
- Return the latest current `.xlsx` workbook.
- Use a filename like:
  `Presales_Weekly_Tracker_YYYY-MM-DD_HH-mm.xlsx`
- Never generate an incomplete workbook from frontend state.
- The downloaded workbook must contain every original sheet plus all new submissions.

---

# Backend API
Keep endpoints small and predictable.

Suggested endpoints:

```text
GET  /api/health
GET  /api/users
GET  /api/dashboard?presales=<name>
GET  /api/entries/{module}?presales=<name>&month=<month>
POST /api/entries/weekly-review
POST /api/entries/weekly-meeting
POST /api/entries/training-attended
POST /api/entries/training-conducted
POST /api/entries/poc
POST /api/entries/customer-workshop
POST /api/entries/win-lost
GET  /api/status
PATCH /api/status/{presales}/{module}
GET  /api/client-manager-targets
GET  /api/column-guide
GET  /api/workbook/download
```

Use Pydantic request models and backend validation for every form.

Never trust frontend-only validation.

---

# Validation
Implement clear validation messages.

Required fields should generally include:
- Region
- Presales
- Date where applicable
- Customer/Account where applicable
- Activity/Opportunity details where applicable

Validate:
- Values cannot be negative.
- Dates must be valid.
- Week must be a supported week number.
- Quarter must be Q1–Q4.
- Dropdown values should use normalized spelling.

Before writing, trim accidental leading/trailing whitespace from normal text fields while preserving multiline notes.

---

# Data Normalization
The current workbook has some inconsistent historical values such as `Jul` vs `July`, capitalization differences, and spacing differences.

Do **not** mass-edit or clean historical records.

For new entries, use standardized values:
- Months: January, February, March, ...
- Regions: West, South, North
- Account Type: New, Existing
- Meeting Mode: In-Person, Virtual
- Stage: Funnel, Upside, Commit, Win, Lost

Historical data should remain untouched.

---

# Usability Details
Add useful small interactions:
- Save button fixed/visible at bottom of long forms.
- Toast: `Entry added successfully`.
- Disable Save while request is processing.
- Confirmation before leaving a form with unsaved changes.
- Required-field indicators.
- Human-readable currency formatting while typing, but submit numeric values.
- Multiline text fields should support bullet-like notes/new lines.
- Remember selected Presales user in localStorage.
- Automatically default Month and Week from the current date, but allow manual change.

Do not create overly large forms visually. Group related fields into sections/cards.

Example Weekly Review grouping:
- Customer & ownership
- Opportunity
- Commercial / Forecast
- Weekly updates

---

# Error Handling
Never silently lose a submission.

If Excel writing fails:
- return a clear backend error
- show a visible frontend error toast/message
- do not claim the entry was saved
- keep the user's form data on screen so they can retry

Log backend errors with enough detail for debugging but never expose stack traces to normal users.

---

# Deployment / Persistence Warning
This app writes to a real `.xlsx` file.

Do not deploy the backend to a platform where the local filesystem is ephemeral unless persistent storage is configured.

For internal V1, prefer:
- a company VM/server
- a local network server
- Docker on a persistent host
- or persistent mounted storage

If deployed to a serverless platform, store the workbook in persistent object/file storage and implement the same locking/version-safety strategy.

Never assume Vercel/temporary function filesystem is persistent.

---

# Security for V1
This is an internal application.

Implement basic protections without overengineering:
- CORS restricted to frontend origin
- file download only through backend endpoint
- validate all payloads
- never accept arbitrary sheet names or cell references from the client
- backend maps each supported module to a predefined sheet and column list
- prevent path traversal

Do not allow the frontend to send Excel row/cell coordinates for new entries.

---

# Code Quality
Keep the implementation modular but not overengineered.

Backend should contain a centralized Excel service, for example:

```text
excel_service.py
```

Responsibilities:
- load workbook
- lock workbook
- create backup
- find next valid insertion row
- append entry
- copy row styling
- update status
- read recent rows
- download workbook

Create one configuration/schema mapping for sheet names, header rows, and field columns rather than scattering Excel coordinates throughout the code.

Example concept:

```python
MODULES = {
    "weekly-review": {
        "sheet": "Weekly Review",
        "header_row": 5,
        "start_col": 1,
        "fields": [...]
    }
}
```

---

# V1 Acceptance Criteria
The project is complete only when all of the following work:

1. App launches with one frontend and one backend command.
2. Original workbook loads successfully.
3. User can select their Presales name.
4. User can submit a Weekly Review record.
5. User can submit a Weekly Meeting record.
6. User can submit Training Attended.
7. User can submit Training Conducted.
8. User can submit a PoC entry.
9. User can submit a Customer Workshop entry.
10. User can submit a Win/Lost entry.
11. Submitted values appear in the correct existing sheet and columns.
12. Existing workbook formatting is preserved.
13. Existing formulas are not accidentally overwritten.
14. Auto serial numbers work correctly where needed.
15. Status page reads the existing `Status` sheet.
16. User can mark a module Pending/Completed.
17. Client Manager Targets display correctly in read-only mode.
18. Column Guide displays correctly.
19. Recent entries display from the actual Excel workbook.
20. Download Excel returns the latest complete workbook.
21. Two rapid simultaneous submissions do not corrupt or overwrite the workbook.
22. Failed writes do not produce a partially corrupted workbook.
23. A backup exists after changes.
24. UI is clean, responsive, and professional.
25. README explains setup, workbook location, backup/recovery, and deployment persistence requirements.

---

# Do Not Build in V1
Avoid spending tokens/time on:
- complex authentication/SSO
- separate SQL database
- AI features
- charts-heavy analytics
- notifications
- role-based permissions
- email integration
- complicated admin console
- rebuilding Excel formatting in the frontend

Focus on a reliable, polished form-to-Excel workflow.

---

# Final Deliverables
Produce the complete working project with:

1. React frontend
2. FastAPI backend
3. Existing Excel workbook integrated as the data source
4. All module forms
5. Dashboard + submission status
6. Read-only Client Manager Target + Column Guide views
7. Safe Excel append/update logic
8. Excel download endpoint/button
9. Automatic backups and locking
10. README with exact local setup commands
11. `.env.example` only if configuration is required

The final result should be usable by a real Presales team immediately after running it and placing the supplied workbook in the expected backend data folder.

Before finishing, test at least one write in every editable module against a copy of the workbook, reopen the resulting `.xlsx`, verify the values are in the correct columns, and confirm the workbook still opens normally with its original sheets and formatting intact.
