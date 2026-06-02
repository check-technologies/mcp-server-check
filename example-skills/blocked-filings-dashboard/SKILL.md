---
name: blocked-filings-dashboard
model: claude-opus-4-6
description: >
  Generate a partner-shareable HTML dashboard of blocked tax filings for a quarter,
  using the Check MCP filings API. Shows an expected filing success rate, what-if
  projections per blocker, KPI cards, charts, and a sortable/filterable table of every
  blocked filing with its blocker reasons. Use this skill when someone asks for a blocked
  filings dashboard, a filing blocker report, a quarterly blockers summary, or wants to
  see which filings are blocked and why for a partner.
---

# Blocked Filings Dashboard

This skill builds a self-contained HTML dashboard of a partner's **blocked** tax filings
for a given quarter. It pulls live data through the Check MCP filings API and writes a
partner-shareable report to the Desktop.

The Check MCP API key is already scoped to a **single partner**, so there is no partner
name or UUID to look up — every filing the API returns belongs to that partner.

## What this dashboard does and does not show

The public filings API exposes each filing's `status` and `blocked_reasons`, but **not**
operator-written issue notes or the internal/external issue split. Accordingly this
dashboard:

- **Has no "Notes" column** (the API does not return operator notes).
- Shows **all** blocker reasons the API reports — there is no internal-issue filtering to
  apply, because the API only returns externally-visible blockers.

Mention these omissions briefly when you present the report so the audience knows it is
API-sourced.

## Step 0: Parse Inputs

Collect a **quarter** and **year** (e.g. "Q2 2026" or `q2 2026`). If not provided, ask.

Derive:

- `period` — the quarter lowercased: `q1`, `q2`, `q3`, or `q4` (the `period` filter value
  the API expects).
- `period_start` / `period_end` — the calendar bounds of the quarter, used for labels and
  the "First QE" window:
  - Q1 = Jan 1 – Mar 31, Q2 = Apr 1 – Jun 30, Q3 = Jul 1 – Sep 30, Q4 = Oct 1 – Dec 31.
- `year` — integer (e.g. `2026`).

## Step 1: Pull Blocked Filings

Fetch every blocked filing for the quarter:

```
run_tool: list_filings { "status": "blocked", "year": <year>, "period": "<period>", "limit": 500 }
```

Paginate: if the response has a non-null `next_cursor`, repeat with
`"cursor": "<next_cursor>"` until it is null. Accumulate all results.

Each filing record includes `id`, `company` (a `com_...` company ID), `status`,
`blocked_reasons` (an array of blocker reason strings), `period`, `year`, and `name`.

If zero blocked filings are returned, tell the user there are none for that quarter and
stop.

## Step 2: Pull Status Counts for the Success-Rate Denominator

To compute the success rate you need the total **applicable** filing count, not just the
blocked ones. Sweep all filings for the quarter and bucket by `status`:

```
run_tool: list_filings { "year": <year>, "period": "<period>", "limit": 500 }
```

Paginate as in Step 1. Then count filings per `status`.

- `total_applicable` = count of all filings whose status is **not** `inapplicable`.
- Statuses you may see: `pending`, `blocked`, `submitted`, `filed`, `inapplicable`.

If this sweep returns a large number of filings, give the user a progress note while
paginating.

## Step 3: Enrich Companies (legal name + First QE)

Collect the **unique** `company` IDs from the blocked filings. For each one, fetch the
company to get its legal name and start date:

```
run_tool: get_company { "company_id": "<com_...>" }
```

Use `get_company` (not `list_companies`) — the company list view omits `start_date`.

Read `legal_name` and `start_date`. A company is **First QE** (this is their first
quarter-end on Check) when `start_date` falls within `[period_start, period_end]`.

Cache results by company ID so you only fetch each company once. Give progress updates for
large sets (e.g. "Fetched company details 12/40...").

## Step 4: Build the HTML Dashboard

Write a Python script that generates one self-contained HTML file and saves it to
`~/Desktop/<partner_slug>_<period>_<year>_blocked_filings_report.html`, then open it with
`open`. There is no partner name input — derive `<partner_slug>` from the data (e.g. the
most common company name root) or use `partner`; let the user override the filename.

### Dashboard specifications

**Title:** "<Q#> <Year> Blocked Filings"
**Subtitle:** "<Q#> period <period_start> to <period_end> · Snapshot as of {today's date} ·
**First QE** = company start date <period_start> – <period_end> (this is their first
quarter-end on Check)"

**Theme:** Light:
- Background `#f7f8fa`, Cards `#fff`, Border `#e5e7eb`, Text `#1c2024`, Muted `#6b7280`
- Font: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif

**Hero — Expected Filing Success Rate** (top of page, above KPI cards):
- Large percentage = `1 - (blocked_count / total_applicable)`, one decimal place.
- Label: "Expected Filing Success Rate"
- Subtitle: "Based on {blocked_count} blocked out of {total_applicable} applicable filings"
- 48px bold percentage, 16px label/subtitle, centered, accent color by rate:
  - ≥ 95%: green `#16a34a` · 90–94.9%: `#65a30d` · 80–89.9%: amber `#d97706` · < 80%: red `#dc2626`

**What-If Projections** (below the hero, above KPI cards): for each blocker reason present,
compute the success rate if **all filings whose sole blocker is that reason** were
unblocked. A filing with multiple blockers stays blocked (conservative projection). Render
as a flex-wrap row of ~180px cards sorted by highest projected rate first, each showing:
- Human-readable blocker name (e.g. "Applied-for Tax ID")
- Projected rate (e.g. "→ 93.1%")
- Count of blocked filings with that reason (e.g. "42 filings")
- Colored left border using the blocker color below.

**KPI Cards (5):**
1. <Q#> Applicable Filings — `total_applicable`
2. Blocked — count from Step 1
3. Companies Affected — unique company count from Step 1
4. First QE — Blocked — blocked filings where the company is First QE (with company count + block rate in a context line)
5. Not First QE — Blocked — the complement (with company count + block rate)

**Charts (side by side, Chart.js 4.4.0 from CDN):**
- Left: "Blocker reasons" — vertical stacked bar, split First QE (teal `#0d9488`) vs Not First QE (blue `#1976d2`).
- Right: "Most affected companies" — horizontal bar, top 15 companies, colored by First QE (teal) vs Not (blue).

**Blocker colors:**
```
applied_for_tax_id: #ff6f61
invalid_tax_id: #c62828
tpa_failure: #8e24aa
inactive_account: #5e35b1
already_filed: #fdd835
not_liable: #7cb342
filing_configuration_incomplete: #546e7a
awaiting_tax_funds: #00695c
incorrect_account_setup: #fb8c00
company_bad_standing: #3949ab
missing_tax_funds: #ef6c00
invalid_ssn: #6d4c41
correction_needed: #8d6e63
missing_historical_data: #795548
held_by_customer: #a1887f
poa_failure: #d84315
```
For any blocker reason not in this map, fall back to a neutral gray (`#6b7280`).

**Table: "<Q#> <Year> Blocked Filings"** with a row-count badge. Columns (no Status column —
every row is blocked):
1. Company (`legal_name`, sortable)
2. Company ID (`company`, monospace, sortable)
3. Filing (`name`, sortable)
4. Blocker Reasons (tags colored from the palette, clickable to set the blocker filter)
5. First QE (green "First QE" tag when true, sortable)
6. Start Date (`start_date`, sortable)

**Blocker tag styling:** solid background at 15% opacity of the blocker color.

**Filters (one line):**
- Search input — searches company name, company ID, and filing name.
- Blocker reason dropdown — single-select, default "All blocker reasons", no counts.
- First QE dropdown — "All companies" / "First QE only" / "Not First QE only", no counts.

**Features:**
- All columns sortable by clicking headers.
- CSV export of the filtered rows: Company, Company ID, Filing, Blocker Reasons, Blocker Count, First QE, Start Date.
- Blocker tags have hover tooltips (descriptions below) and click to set the blocker filter.
- Footer: "<Q#> <Year> Blocked Filings — Snapshot {date} · Sourced from the Check filings API"

**Blocker tooltip descriptions:**
```
applied_for_tax_id: "Company has applied for a tax ID with the agency but has not received it yet. Filing will proceed once the ID is issued."
invalid_tax_id: "The tax ID on file was rejected by the agency or does not match their records."
tpa_failure: "Third-party authorization was rejected or has expired. A new authorization needs to be submitted to the agency."
already_filed: "This filing appears to have already been submitted, possibly filed directly with the agency."
filing_configuration_incomplete: "Setup for this filing type is not yet complete."
inactive_account: "Tax account appears to be inactive with the agency."
not_liable: "Company does not appear to be liable for this tax in this jurisdiction."
company_bad_standing: "Account is not in good standing with the tax agency."
awaiting_tax_funds: "Waiting for sufficient funds to be available."
incorrect_account_setup: "Configuration issue with this account that needs correction."
held_by_customer: "A hold has been placed on this filing at the customer's request."
missing_tax_funds: "Insufficient tax funds available for this filing period."
invalid_ssn: "An employee SSN issue is preventing this filing."
correction_needed: "Filing data needs a correction before submission."
missing_historical_data: "Prior period data needed but currently unavailable."
poa_failure: "Power of Attorney not accepted or rejected by the agency."
```

## Step 5: Output

Save the HTML to `~/Desktop/<partner_slug>_<period>_<year>_blocked_filings_report.html`,
open it, and report the total blocked filings count and number of companies affected.
Remind the user this is sourced from the filings API and therefore omits operator notes.

## Error Handling

- **API error envelopes**: list/get tools may return `{"error": true, "status_code": ...,
  "detail": ...}`. Surface the `detail`, skip the affected record, and continue; note any
  companies whose details could not be fetched.
- **Pagination**: always follow `next_cursor` until null on both list sweeps.
- **No blocked filings**: report that the quarter is clean and stop before building HTML.
- **Missing company fields**: if `start_date` is absent for a company, treat it as Not
  First QE and note it.
