# PDF Employee Details Report

This covers PDF reports with a structured table layout where each worker occupies a
multi-row block within the table.

## Recognizing This Format

- File is PDF
- Contains a title like "Employee details report"
- Has column headers: `Personal info | Hire date | Work location | Pay info | Tax info | Notes`
- Each worker spans multiple visual rows within their table cell
- May span multiple pages

## Structure

The PDF typically has:
- A company name header
- A report title (e.g., "Employee details report")
- A subtitle (e.g., "For all employees from all locations")
- A table with columns: Personal info, Hire date, Work location, Pay info, Tax info, Notes

Each worker occupies one "row" of the table, but visually that row contains multiple lines
of text within each cell.

## Parsing Strategy

Use the Read tool to view the PDF. The text extraction will produce blocks of text for
each worker. The key is to identify worker boundaries and then parse each block.

### Identifying worker boundaries

Each worker block starts with a name in **"Last, First [Middle]"** format, followed by
their address, DOB, and other details. A new worker block starts when you see the next
name pattern.

Terminated workers are typically prefixed with an asterisk: `*Ahlers, Robert T`

### Extracting fields from each worker block

**Personal info section:**
```
Kieffaber, Derek
7617 W 64th St,
Overland Park,
KS 66202
DOB: 10/30/1982
Gender: Male
```
- Line 1: Name (Last, First [Middle])
- Following lines until DOB: Home address (may be split across multiple lines)
- `DOB:` line: Date of birth
- `Gender:` line: Gender (optional)
- `Terminated:` line: Termination date (if present, preceded by asterisk on name)

**Hire date:** A simple date, e.g., `08/31/2023`

**Work location:** A multi-line address:
```
1708 Campbell
St, Kansas City,
MO 64108
```
Concatenate the lines and parse as a single address string.

**Tax info section:**
```
SSN 512-92-5851
Fed Single or Married Filing Separately
MO Single
KS Single
Local MO - Kansas City
```
- First line with `SSN`: Extract the SSN, strip dashes
- Remaining lines: Tax filing status (not needed for Check API)

**Pay info section:**
```
Salary $1,019.24/yr
Pay method DD, ....4429
Deductions None
```
- Compensation type (Salary vs Hourly rate) — informational only
- Pay method — not needed for Check API

### Multi-page handling

PDF reports with many workers will span multiple pages. The column headers may repeat at
the top of each page. When parsing, skip repeated header rows and continue extracting
worker blocks.

### Address reassembly

PDF text extraction often splits addresses across lines at arbitrary points. When
reassembling:
1. Collect all address lines between the name and DOB
2. Join them into a single string
3. Parse city, state, and postal code from the end
4. Everything before the city is line1 (and optionally line2 for apartment/suite numbers)

Example:
```
1116 E 117th St
Apt 5, Kansas
City, MO 64131-
3747
```
→ line1: "1116 E 117th St Apt 5", city: "Kansas City", state: "MO", postal_code: "64131-3747"

This requires careful handling — the city name may be split across lines, and the zip code
may wrap to the next line. Look for the 2-letter state abbreviation as the anchor point.
