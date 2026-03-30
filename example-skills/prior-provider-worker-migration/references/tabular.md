# Tabular CSV/XLSX Format

This covers reports where each worker is one row and each field is a separate column. This
is the most common and easiest-to-parse format.

## Recognizing This Format

- File is CSV, TSV, or XLSX
- There's a clear header row with column names (may not be row 1 — see below)
- Each worker occupies exactly one data row
- Columns have names like "First", "Last", "SSN", "DOB", "Email", "Address", etc.

## Parsing Steps

### 1. Skip metadata rows

Many reports start with 3-5 metadata rows before the column headers:
- Row 1: Report title (e.g., "Employee Information", "New custom report", "Employee Listings")
- Row 2: Company name, blank, or report metadata
- Row 3: Date range, "Printed on" date, or "Time Run"
- Row 4: Blank

Detect the header row by looking for the first row that contains multiple recognizable field
names like "First", "Last", "SSN", "DOB", "Email", "Address", "Name", "Hire", etc.

For XLSX files with multiple sheets, check for a "Header" or metadata sheet — the actual
data may be on a separate sheet (commonly named "Data" or similar).

### 2. Filter out non-data rows

Some reports include per-worker totals rows and blank separator rows:
```
Kenneth Ayala totals,,0,0,0,...
,,,,,,,,,...
```
Filter these out — only keep rows where the name fields are populated AND the row is not
a "totals" row (i.e., the name cell doesn't end with "totals"). Also filter out any
"Grand totals" row at the end.

### 3. Map columns

Here are column patterns observed across providers. The skill's main SKILL.md has the full
synonym table — use it to map whatever column names you find.

**Pattern A — Separate first/last columns:**
Columns like `Last`, `First`, `Middle`, `Email`, `DOB`, `SSN`, etc.
- Straightforward: each column maps to one Check field

**Pattern B — Combined "Employee" or "Full name" column:**
A single column like `Employee` contains the full name (e.g., "Kenneth Ayala" or
"Sanchez, George"). Parse using the name-parsing rules in the main SKILL.md.

**Pattern C — Expanded address columns:**
Some reports have `Home address (street)`, `Home address (city)`, `Home address (state)`,
`Home address (zip)` as separate columns. Others have a single `Home address` or `Address`
column with the full address as a string. Similarly for work address.

**Pattern D — Single address column:**
Some reports combine the full address into one column (e.g., "19107 SE 400th ST Enumclaw,
WA 98022"). Parse the city/state/zip from the end of the string.

### 4. Handle worker type

Look for a column like `Employee type`, `Employment type`, or `Status` that distinguishes
employees from contractors. Common values:

| Value | Classification |
|---|---|
| `Employee` | Employee |
| `Independent Contractor` | Contractor |
| `W-2` | Employee |
| `1099` | Contractor |
| `Paid by the hour` | Compensation type — NOT classification (default to Employee) |
| `Salary/No overtime` | Compensation type — NOT classification (default to Employee) |
| `Full time` / `Part time` | Employment status — NOT classification |

### 5. Handle terminated workers

Look for:
- A `Status` or `Employment status` column with values like "Terminated", "Inactive"
- A `Termination Date` or `Employee end date` column that's populated
- An asterisk prefix on the name (some reports mark terminated workers with `*`)

Include terminated workers in the migration — they need `termination_date` set.

### 6. Special considerations for XLSX with datetime cells

Excel files may store dates as datetime objects rather than strings. When using openpyxl,
check the cell type — if it's a datetime, format it directly to `YYYY-MM-DD` rather than
trying to parse a string. Example:
```python
from datetime import datetime
if isinstance(cell_value, datetime):
    date_str = cell_value.strftime("%Y-%m-%d")
```

SSN fields in Excel may lose leading zeros if stored as numbers. Check for this: if an
SSN is only 8 digits, it likely needs a leading zero (e.g., `37507993` → `037507993`).
