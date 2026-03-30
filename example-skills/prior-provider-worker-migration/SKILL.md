---
name: prior-provider-worker-migration
model: claude-opus-4-6
description: >
  Set up a company's workers in Check from any prior payroll provider's worker report.
  Accepts CSV, XLS, XLSX, or PDF reports and auto-detects the format — whether it's a
  tabular spreadsheet, a multi-line cell layout, or a PDF employee details report.
  Parses workplaces and worker data (employees and/or contractors), creates them via
  the Check API, and verifies every record matches the original source data. Use this
  skill whenever someone mentions setting up a company in Check, migrating workers from
  a prior provider, importing employee/contractor data into Check, onboarding a company's
  workforce, or uploading a worker report. Also trigger when a user provides a CSV, Excel
  file, or PDF with worker data and a Check company ID and wants those workers created
  in the system. Even if they don't name the provider — if they have a worker report and
  want to set up employees/contractors in Check, this is the skill to use.
---

# Check Company Setup — Worker Migration from Prior Provider

This skill imports workers (employees and contractors) into Check from any prior payroll
provider's worker report. The guiding principle is **data integrity**: every record created
in Check must be verified against the original source data, and any discrepancies must be
corrected before moving on.

## Prerequisites

Before starting, collect two things from the user:

1. **A Check company ID** (looks like `com_XXXXXXXXXXXXXXXXXX`). Ask for it if not provided.
2. **A worker report** — a CSV, XLS, XLSX, or PDF exported from the prior payroll provider.

## Step 1: Detect the File Format and Parse

Reports vary wildly across providers. The first job is to figure out what you're looking at.

### 1a. Open the file and identify the format family

Read the file using the appropriate method for its type:
- **CSV/TSV** — read as text, look at the first 10 rows
- **XLS** — use `xlrd` to open and inspect sheets
- **XLSX** — use `openpyxl` to open and inspect sheets
- **PDF** — extract text (use the Read tool or a PDF extraction library)

Then classify the report into one of these format families based on what you see. Read the
matching reference file from `references/` for detailed parsing instructions:

| Format Family | How to Recognize | Reference |
|---|---|---|
| **Tabular CSV/XLSX** | Clean column headers in one of the first ~5 rows; one worker per row with separate columns for each field (name, SSN, DOB, address components, etc.) | `references/tabular.md` |
| **Multi-line Cell Spreadsheet** | XLS/XLSX where a single cell contains multiple lines of data (e.g., name + address + DOB + SSN all packed into one "Personal info" or "Employee Information" cell) | `references/multiline-cell.md` |
| **PDF Employee Details** | PDF with a table layout where each worker occupies a multi-row block; fields like "Personal info", "Hire date", "Work location", "Pay info", "Tax info" | `references/pdf-details.md` |
| **PDF Simple List** | PDF with a simple tabular list — one row per worker, clear column headers | `references/pdf-list.md` |

If the format doesn't match any of these families, do your best to identify the column/field
structure. Present your interpretation to the user and ask them to confirm before proceeding.

### 1b. Extract the raw worker records

Follow the instructions in the relevant reference file to extract a list of worker records.
Each record should be a dictionary of raw field values, keyed by whatever the report calls them.

### 1c. Map fields to Check API fields

Regardless of how the report names its columns, you need to map them to Check's API fields.
Here are the target fields:

**Identity:**
- `first_name` (required)
- `last_name` (required)
- `middle_name`
- `dob` — date of birth
- `ssn` — Social Security Number (9 digits, no dashes)
- `email`

**Employment:**
- `start_date` — hire date
- `termination_date` — if the worker has been terminated
- Worker classification: employee vs contractor

**Home address** (field name depends on worker type):
- For employees: `residence` → `{ line1, line2, city, state, postal_code }`
- For contractors: `address` → `{ line1, line2, city, state, postal_code }`

**Workplace:**
- Work location address → used to create/assign a workplace

Common column-name synonyms to watch for:

| Check Field | Common Report Column Names |
|---|---|
| first_name | `First`, `First name`, `First Name`, or parsed from a combined "Last, First M" field |
| last_name | `Last`, `Last name`, `Last Name`, or parsed from combined name field |
| middle_name | `Middle`, `Middle Name`, `Employee middle initial`, or initial in combined name |
| dob | `DOB`, `Date of birth`, `Birth Date`, `Birth date` |
| ssn | `SSN`, `SS No.`, `Social Security`, `Taxpayer ID (SSN or Fed ID)` |
| email | `Email`, `Email address`, `Work Email`, `Work email address`, `Personal email` |
| start_date | `Start Date`, `Hire Date`, `Hire date`, `Most recent hire date`, `Employee start date` |
| termination_date | `Termination Date`, `Employee end date`, `Terminated` (as a date) |
| residence/address line1 | `Home Address Line 1`, `Home address (street)`, `Address 1`, `Address` (single string) |
| residence/address city | `Home City`, `Home address (city)`, `City` |
| residence/address state | `Home State`, `Home address (state)`, `State/province` |
| residence/address postal_code | `Home Zip Code`, `Home address (zip)`, `ZIP/postal code` |
| work location | `Work Location`, `Work address`, `Work location`, or a separate multi-line field |
| worker type | `Employee Type`, `Employment type`, `Employee type` — but see note below |

**Worker classification note:** Some providers' "Employee Type" or "Employment type" column
describes compensation type (e.g., "Paid by the hour", "Salary/No overtime") rather than
whether someone is an employee vs contractor. Look for explicit values like "Employee",
"Independent Contractor", "W-2", "1099", or "Contractor" to distinguish. If the column
is ambiguous, ask the user whether the report contains employees, contractors, or both.
Default to treating all workers as employees unless told otherwise or the data says otherwise.

### 1d. Show the mapping and get confirmation

Present the column mapping before proceeding:

```
Here's how I've mapped the report fields to Check:

  "Last name"              →  last_name
  "First name"             →  first_name
  "DOB"                    →  dob  (will convert to YYYY-MM-DD)
  "SSN"                    →  ssn  (will strip dashes)
  "Hire Date"              →  start_date  (will convert to YYYY-MM-DD)
  "Home Address Line 1"    →  residence.line1
  "Home City"              →  residence.city
  "Home State"             →  residence.state
  "Home Zip Code"          →  residence.postal_code
  "Work Location"          →  workplace address

  Unmapped columns (will be skipped): "Department", "Payment Info", "Manager", ...

Workers found: 8 employees, 0 contractors
  (includes 1 terminated employee)

Does this look right?
```

Wait for confirmation before proceeding.

## Step 2: Format the Data

Normalize all values to match Check's API expectations.

### Dates

Convert all dates to `YYYY-MM-DD`. Common formats you'll encounter:
- `M/D/YY` or `MM/DD/YY` (e.g., "6/5/24" → "2024-06-05", "11/14/95" → "1995-11-14")
- `MM/DD/YYYY` or `M/D/YYYY` (e.g., "02/01/2001", "6/5/2024")
- `YYYY-MM-DD` with optional time (e.g., "2020-02-25 00:00:00" → "2020-02-25")
- Date objects from Excel — convert directly

For 2-digit years: use a sensible century cutoff. Years 00-30 are 2000s, years 31-99 are
1900s. This matters because DOBs will be 1900s and start dates will typically be 2000s.

### SSN

Strip all dashes, spaces, and formatting. Common formats:
- `XXX-XX-XXXX` → 9 digits
- `xxx-xx-XXXX` (masked with last 4 visible) — note this as a limitation
- Full 9-digit number without dashes

If the report only has last 4 digits, note this to the user as a limitation.

### Addresses

Check's API expects:
```json
{
  "line1": "123 Main St",
  "line2": "Suite 100",
  "city": "San Francisco",
  "state": "CA",
  "postal_code": "94105"
}
```

The zip/postal code field is `postal_code` (not `zip`). This applies to all address objects.

**When the report has separate columns** (Line 1, City, State, Zip), use them directly but
map the Zip column to `postal_code`.

**When the address is a single string**, parse it. Examples:
- `"53302 Hunt Brooks, Callahanview, MO 90213"` → line1: "53302 Hunt Brooks",
  city: "Callahanview", state: "MO", postal_code: "90213"
- `"7617 W 64th St, Overland Park, KS 66202"` → line1: "7617 W 64th St",
  city: "Overland Park", state: "KS", postal_code: "66202"
- `"1116 E 117th St Apt 5, Kansas City, MO 64131-3747"` → line1: "1116 E 117th St Apt 5",
  city: "Kansas City", state: "MO", postal_code: "64131-3747"

When a work location is a non-address value like `"Office"`, ask the user for the actual
office address, or skip workplace creation if they confirm it's already set up.

### Names

**Simple columns** (separate First, Last): trim whitespace, normalize ALL-CAPS to title case.

**Combined "Last, First M" fields**: split on the comma, trim. The part after the comma is
the first name, optionally followed by a middle initial or middle name. Watch for suffixes
like "Jr", "Sr", "II", "III" which belong with the last name:
- `"Jones, Leonard"` → first: "Leonard", last: "Jones"
- `"Gill II, Robert T"` → first: "Robert", last: "Gill II", middle: "T"
- `"Stone Jr, Earl R"` → first: "Earl", last: "Stone Jr", middle: "R"
- `"PachecoCasillas, Felicia"` → first: "Felicia", last: "PachecoCasillas"

**Single "Full name" column** (first last order): `"George Sanchez"` → first: "George",
last: "Sanchez"; `"Bennett, Marcus P"` → detect comma and parse as Last, First M.

## Step 3: Create Workplaces

Workplaces represent physical work locations. Set these up before creating workers.

### 3a. Extract unique workplace addresses
Deduplicate the work location values from the report.

### 3b. Check for existing workplaces
```
run_tool: list_workplaces { "company": "<company_id>" }
```
Compare existing workplace addresses against the report's work locations. Normalize for
comparison: ignore case, expand/collapse abbreviations ("St"/"Street"), compare core components.

### 3c. Create missing workplaces
```
run_tool: create_workplace {
  "company": "<company_id>",
  "address": {
    "line1": "1708 Campbell St",
    "city": "Kansas City",
    "state": "MO",
    "postal_code": "64108"
  }
}
```

### 3d. Verify each workplace
After creating, call `get_workplace` and confirm the stored address matches. If there's a
mismatch, correct it with `update_workplace`. Keep a mapping of workplace addresses → IDs.

## Step 4: Create Workers

### 4a. Check for existing workers (do this once, up front)

Pull the full list of existing workers:
```
run_tool: list_employees { "company": "<company_id>" }
run_tool: list_contractors { "company": "<company_id>" }
```

**Matching priority:**
1. **SSN last four** — compare last 4 of full SSN against `ssn_last_four` from the API
2. **Date of birth** — use DOB as a matching criterion when available
3. **Name** — first_name + last_name, case-insensitive

Consider a worker a match if their name matches AND at least one of SSN or DOB also matches.
If only the name matches but neither SSN nor DOB can be compared, flag it as an uncertain
match rather than silently skipping.

### 4b. Create each worker

**For employees** — `create_employee` requires `company`, `first_name`, and `last_name`:
```
run_tool: create_employee {
  "company": "<company_id>",
  "first_name": "Rachel",
  "last_name": "Young",
  "email": "zsalazar@example.net",
  "dob": "2001-02-01",
  "start_date": "2024-06-05",
  "ssn": "454746596",
  "residence": {
    "line1": "850 Garcia Viaduct",
    "city": "North Michele",
    "state": "FL",
    "postal_code": "61759"
  },
  "workplaces": ["<workplace_id>"],
  "primary_workplace": "<workplace_id>"
}
```
For employees, the home address field is `residence` (not `address`).

**For contractors** — `create_contractor` requires only `company`:
```
run_tool: create_contractor {
  "company": "<company_id>",
  "first_name": "John",
  "last_name": "Smith",
  "dob": "1985-03-22",
  "start_date": "2024-06-01",
  "ssn": "987654321",
  "address": {
    "line1": "789 Pine Rd",
    "city": "Berkeley",
    "state": "CA",
    "postal_code": "94704"
  },
  "workplaces": ["<workplace_id>"],
  "primary_workplace": "<workplace_id>"
}
```
For contractors, the home address field is `address` (not `residence`).

Include `termination_date` if the worker has one.

### 4c. Report progress
For reports with more than a few workers, give progress updates (e.g., "Created 5/13...").

## Step 5: Verification (Critical)

Every record created in Check must be verified against the original report. Do not skip this.

### 5a. Re-read all created records
For each created worker, call `get_employee` or `get_contractor`. Compare every field:
- first_name, last_name, middle_name
- dob, start_date, termination_date
- email
- residence/address: line1, line2, city, state, postal_code
- ssn_last_four (compare against last 4 of SSN from report)
- workplace assignment

### 5b. Build a verification report
For each worker: **MATCH** (all fields match) or **MISMATCH** (list which fields differ).

### 5c. Correct any mismatches
Use `update_employee` or `update_contractor` to fix. Re-verify until everything matches.

### 5d. Present the final summary
```
Worker Setup Complete for com_XXXXXXXXXXXXXXXXXX

Workplaces: 1 created, 0 already existed
Employees:  7 created (1 terminated), 1 already existed
Contractors: 0 created

All 7 created records verified against source report — no mismatches.
```

If there were unresolved issues:
```
Issues requiring manual attention:
- Adam Sabra: Work location "29226 Township Rd Temecula" missing state and zip
- SSN for 2 workers was last-4 only — full SSN may be needed
```

## Error Handling

- **API errors on create**: Log the error, continue with remaining workers, summarize all
  failures at the end.
- **Ambiguous dates**: Flag to the user.
- **Missing required fields**: Skip the row and include it in the error summary.
- **Partial addresses**: Ask the user for missing parts rather than guessing.
- **Large reports (50+ workers)**: Process in batches with progress updates.
- **Masked/partial SSN**: Note which workers have incomplete SSNs in the final summary.
