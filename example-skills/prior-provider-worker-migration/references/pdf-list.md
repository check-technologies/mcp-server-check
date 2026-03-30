# PDF Simple List Format

This covers PDF reports with a straightforward tabular layout — one row per worker,
clear column headers, minimal nesting.

## Recognizing This Format

- File is PDF
- Contains a simple table with clear column headers
- Each worker occupies exactly one row
- Columns are things like: Employee, SS No., Main Phone, Address, Gender
- No multi-row blocks per worker — just a flat table
- Often has a report title and date at the top or bottom

## Structure

Example layout:
```
                    Auburn Valley Animal Clinic
                    Employee Contact List

Employee              SS No.        Main Phone      Address                              Gender
Erin D Heise          538-84-2859   253-205-9996    19107 SE 400th ST Enumclaw, WA 98022 Female
Geoffrey R Kraabel    533-33-6779   2062458470      614 SW 127th ST Seattle, WA 98146    Male
```

## Parsing Strategy

### 1. Extract text from the PDF

Use the Read tool to view the PDF. The text extraction should produce a recognizable
table structure.

### 2. Identify the header row

Look for a row containing column names. Common columns in this format:
- `Employee` — full name (First [Middle] Last format)
- `SS No.` or `SSN` — Social Security Number
- `Main Phone` or `Phone` — phone number (not needed for Check)
- `Address` — full home address as a single string
- `Gender` — gender (not needed for Check)

### 3. Parse each worker row

**Name:** In this format, the name is typically in `First [Middle] Last` order (NOT
Last, First), e.g., `"Erin D Heise"`. Parse as:
- First word: first_name
- Last word: last_name
- Middle words: middle_name
- Watch for multi-word last names (e.g., `"Lillian O Rosado Ramos"` — may need user
  confirmation for ambiguous cases)

**SSN:** Format `XXX-XX-XXXX`. Strip dashes for Check API.

**Address:** Single string combining street, city, state, and zip:
- `"19107 SE 400th ST Enumclaw, WA 98022"` → line1: "19107 SE 400th ST",
  city: "Enumclaw", state: "WA", postal_code: "98022"
- `"23240 88th Ave S Apt VV 204 Kent, WA 98031"` → line1: "23240 88th Ave S Apt VV 204",
  city: "Kent", state: "WA", postal_code: "98031"

The general approach: find the 2-letter state abbreviation near the end, the zip after it,
the city before it (back to the previous comma or recognizable boundary), and everything
before the city is line1.

### 4. Missing fields

This format often lacks:
- **DOB** — date of birth
- **Hire date / start date**
- **Email**
- **Work location**
- **Termination status**

Flag these missing fields to the user. The workers can still be created with the available
data (first_name, last_name, ssn, and residence are enough to create a record), but the
user should be aware of what's missing and may need to provide supplementary data.

### 5. Phone number formats

Phone numbers in this format vary widely:
- `253-205-9996`
- `2062458470` (no formatting)
- `(509) 338-5291`
- `(714) 396 -8689` (extra space)
- `5039642516`

These are not needed for the Check API but can be noted in the summary.
