# Multi-line Cell Spreadsheet Format

This covers XLS/XLSX reports where multiple fields are packed into a single cell with
newline separators. Two major variants exist.

## Recognizing This Format

- File is XLS or XLSX
- Opening the file reveals cells with `\n` characters embedding multiple data points
- A single cell contains a block of text like:
  ```
  Jones, Leonard
  974 Smith Island, Wilkinsmouth, AK 21142
  DOB: 07/23/1918
  Gender: Male
  ```
- OR a cell contains a block like:
  ```
  Robertson, Jason E
  392 Hurst Fields
  New Renee, VA410997352
  Home Phone:
   Mobile: 9416376674
  Hourly: 14.2500
  SSN: xxx-xx-2599
  Hire Date: 02/07/2023
   Birth Date: 04/21/1943
   Status: Active
   Emp Type: Part time
  ```

## Variant A: "Employee Details Report" (QBO-style)

### Structure
- Row 0: Company name
- Row 1: "Employee details report"
- Row 3: "For all employees from all locations"
- Row 4: Column headers — `Personal info | Hire date | Work location | Pay info | Tax info | Notes`
- Row 5+: One worker per row, with multi-line content in each cell

### Parsing the "Personal info" cell

This cell contains the worker's name, address, DOB, and gender, separated by blank lines:

```
Last, First [Middle]

Full address as single string

DOB: MM/DD/YYYY

Gender: Male/Female
```

If the worker is terminated, the cell may also contain:
```
Terminated: MM/DD/YYYY
```

**Name parsing:** The first line is `Last, First [Middle]` — split on comma. Watch for:
- Suffixes: `"Gill II, Robert T"` → last: "Gill II", first: "Robert", middle: "T"
- Hyphenated: `"Ruebel-Marshall, Maya E"` → last: "Ruebel-Marshall", first: "Maya", middle: "E"
- No middle: `"Jones, Leonard"` → last: "Jones", first: "Leonard"
- Asterisk prefix for terminated: `"*Ahlers, Robert T"` → strip the `*`, note as terminated

**Address parsing:** The address is a single string. Parse city, state, and zip from the end:
- `"974 Smith Island, Wilkinsmouth, AK 21142"` → line1, city, state, postal_code
- `"1116 E 117th St Apt 5, Kansas City, MO 64131-3747"` → handle zip+4

**DOB:** Extract the date after `DOB:` and convert to YYYY-MM-DD.

### Parsing the "Hire date" cell

Usually a simple date string: `"06/12/2024"`. Convert to YYYY-MM-DD.

### Parsing the "Work location" cell

A single-line address string: `"8810 Smith Tunnel Suite 561, Mccormicktown, AZ 51564"`.
Parse into address components.

### Parsing the "Tax info" cell

Contains SSN and tax filing information:
```
SSN: 789-39-5118

Fed: Head of Household
Claim dependents amount: $2,000.00

NY: Single or Head of household
```

Extract the SSN from the line starting with `SSN:`. Strip dashes.

### Parsing the "Pay info" cell

Contains compensation info. Not directly needed for worker creation, but the pay type
can hint at classification (hourly vs salary). Not used for Check API fields.

---

## Variant B: "Employee Summary" (ADP-style)

### Structure
- Row 1: Company/report header like `"Company: Third Avenue LLC  Report: Employee Summary  Year: 2024  Quarter: 1"`
- Row 3: Column headers — `Employee Information | Earnings | Taxes | Deductions | Disbursement Type`
- Row 5: Pay frequency note (can be skipped)
- Row 6+: One worker per row (every other row — odd rows are blank separators)

### Parsing the "Employee Information" cell

This is the densest format. All worker identity data is in a single cell:

```
Robertson, Jason E
392 Hurst Fields
New Renee, VA410997352
Home Phone:
 Mobile: 9416376674
Hourly: 14.2500
SSN: xxx-xx-2599
Hire Date: 02/07/2023
 Birth Date: 04/21/1943
 Status: Active
 Emp Type: Part time
```

Parse line by line:

1. **Line 1: Name** — `"Last, First [Middle]"` format. Same parsing rules as Variant A.

2. **Lines 2-3: Address** — The street address may span 1-2 lines. The last address line
   contains city, state, and zip concatenated without clear delimiters. The state is a
   2-letter abbreviation and the zip is 5 or 9 digits fused to the end:
   - `"New Renee, VA410997352"` → city: "New Renee", state: "VA", zip: "41099-7352"

   **Important:** In this format, state and zip are often fused together without a space.
   Parse the 2-letter state code and separate the remaining digits as the zip code.
   If the zip is 9 digits, format as `XXXXX-XXXX`.

3. **Phone lines** — `Home Phone:` and `Mobile:` — skip (not needed for Check API)

4. **Compensation** — `Hourly: 14.2500` or `Salary Per Pay: 1923.08` — skip for creation

5. **SSN** — `SSN: xxx-xx-2599` — NOTE: this format typically masks the first 5 digits.
   You only get the last 4. Flag this as a limitation to the user.

6. **Hire Date** — `Hire Date: MM/DD/YYYY` — extract and convert

7. **Birth Date** — `Birth Date: MM/DD/YYYY` — extract and convert

8. **Status** — `Status: Active` or `Status: Terminated`

9. **Emp Type** — `Emp Type: Part time` or `Full time` — this is employment status, NOT
   employee vs contractor classification.

### Important notes for ADP format

- Workers appear on every other row (e.g., rows 6, 8, 10, ...) — skip blank separator rows
- The SSN is typically masked (only last 4 visible) — note this limitation prominently
- Address parsing requires special care due to fused state+zip
