# FLAG: Corrections API needs MCP/CLI toolset

**Status:** Needs human sign-off before implementation  
**Last updated:** 2026-08-12 (check-api PR #9753)

## Triggering merges

| check-api PR | Merge commit | What landed |
|---|---|---|
| [#8970](https://github.com/check-technologies/check-api-primary/pull/8970) | `46c23fb3e3` | Initial public corrections API: `POST /corrections`, `GET /corrections`, `GET /corrections/{id}` |
| [#9018](https://github.com/check-technologies/check-api-primary/pull/9018) | `aa7c51be38` | List filters, `PATCH /corrections/{id}`, draft-only `DELETE` |
| [#9423](https://github.com/check-technologies/check-api-primary/pull/9423) | `392dec4096` | `POST /corrections/{id}/preview`, `fulfillment_date` → `settlement_date`, `totals`/`preview` on correction object, drop `fulfillment` id |
| [#9753](https://github.com/check-technologies/check-api-primary/pull/9753) | `c56c1ea0c5` | `POST /corrections/{id}/approve`, `approval` async state on correction object, block edits during in-flight approval |

`mcp-server-check` has **no `corrections` toolset**. Per sync workflow guardrails, this automation will not unilaterally add a new resource module.

## Public request-surface changes in #9018

### New endpoint

- **`PATCH /corrections/{id}`** (`partial_update`, scope `payroll:write`)
  - Body (`UpdateCorrectionInputSerializer`): optional `settlement_date` (date, nullable; was `fulfillment_date` before #9423), `description` (string, nullable/blank), `metadata` (object). Unknown fields rejected.
  - Draft-only envelope edits; membership/member contents are not PATCHable.

### New list query parameters (`GET /corrections`)

- **`status`** — enum filter; valid values: `draft`, `failed`, `live`, `pending`, `processing` (`soft-deleted` excluded and invalid).
- **`payroll`** — filter corrections that include the given payroll as a member (`pay_xxxxx`).

Existing list filters unchanged: `company`, `year`, plus standard cursor pagination (`limit`, `cursor`).

### Changed endpoint behavior

- **`DELETE /corrections/{id}`** — for API-key callers, deletion is **draft-only**; non-draft sessions raise `CorrectionNotDraftError`.

### Pagination defaults (list)

- Default page size: **25** (was 100)
- Max page size (`limit`): **100** (was 500)

### Response-only (no MCP code change once tools exist)

- `GET /corrections` list items include read-only `settlement_date` (was `fulfillment_date` before #9423), `description`, `metadata`.

## Public request-surface changes in #9423

### Field rename (request + response) — **breaking**

- **`fulfillment_date` → `settlement_date`** on `POST /corrections` and `PATCH /corrections/{id}` request bodies, and on all correction response objects (detail + list). The wire name is `settlement_date`; internally it maps to the `fulfillment_date` model column via `source`.

### New endpoint

- **`POST /corrections/{id}/preview`** (`preview` action, scope `payroll:write`)
  - Async dry-run fulfillment pricing; returns **202 Accepted** with the updated correction object.
  - Requires at least one member payroll on the correction; draft-only.
  - Errors: `ActionInProgressError` if a calculation or preview is already in progress; `CorrectionNotDraftError` if not draft.

### Response shape changes (read-only — no MCP param changes once tools exist)

- **`fulfillment` id removed** from correction detail responses (fulfillment summary stays internal).
- **`totals` added** — money-movement totals (`FulfillmentTotalsSerializer` shape), null until preview has priced the draft.
- **`preview` added** — async preview state object (`status`, `started_at`, `error_code`), null until a preview is requested or after invalidation.

## Public request-surface changes in #9753

### New endpoint

- **`POST /corrections/{id}/approve`** (`approve` action, scope `payroll:write`)
  - Fully async: commits the correction and moves money. Returns **202 Accepted** with the updated correction object.
  - No request body; path param only (`cor_xxxxx`).
  - Requires session-managed lifecycle (`manages_payroll_lifecycle`); console-authored sessions must approve elsewhere (`CorrectionNotSessionManagedError`).
  - Draft-only with at least one member payroll.
  - Re-validates `settlement_date` lead time, company good standing, and member void integrity at approval time.
  - Errors: `CorrectionNotDraftError`, `CorrectionEmptyError`, `ActionInProgressError` (calculation or approval already in progress), `CompanyNotInGoodStandingError`, `PayrollItemAlreadyVoidedError`.
  - On workflow signal failure, rolls back to draft and returns **500** with `{"detail": "Failed to start approval."}`.

### Response shape changes (read-only — no MCP param changes once tools exist)

- **`approval` added** — async approval state object (`status`, `started_at`, `error_code`), null until an approval is requested. Same shape as `preview`.
  - `status` enum: `calculating`, `succeeded`, `failed`.
  - `error_code` example on drift: `fulfillment_changed` (session stays draft; refreshed numbers on the correction).

### Changed endpoint behavior (error conditions only — wire contract unchanged)

While `approval.status` is `calculating`, the following raise `ActionInProgressError`:
- **`PATCH /corrections/{id}`** — envelope edits blocked.
- **`DELETE /corrections/{id}`** — deletion blocked.
- **`POST /corrections/{id}/preview`** — new preview blocked.

## Suggested toolset (for human review)

When approved, add `src/mcp_server_check/tools/corrections.py` wired into `_TOOLSETS`, covering at minimum:

| Tool | HTTP | Notes |
|---|---|---|
| `list_corrections` | `GET /corrections` | Params: `company`, `year`, `status`, `payroll`, pagination |
| `get_correction` | `GET /corrections/{id}` | From #8970 |
| `create_correction` | `POST /corrections` | Body: `company`, `settlement_date`, `description`, `metadata` |
| `update_correction` | `PATCH /corrections/{id}` | Body: `settlement_date`, `description`, `metadata` (#9018) |
| `delete_correction` | `DELETE /corrections/{id}` | Draft-only contract (#9018) |
| `preview_correction` | `POST /corrections/{id}/preview` | Async dry-run pricing (#9423); write tool behind `read_only` gate |
| `approve_correction` | `POST /corrections/{id}/approve` | Async commit + money movement (#9753); write tool behind `read_only` gate |

Additional `@action` endpoints on `CorrectionViewSet` (save, apply_updates, corrected_payrolls, etc.) are out of scope for this flag — confirm separately whether they should be public MCP tools.

## Please verify

- [ ] Corrections API is ready for MCP/CLI exposure (feature flag `ENABLE_CORRECTIONS_API` gating on API keys)
- [ ] Tool naming and `read_only` gating conventions
- [ ] Complete enum values for `status` filter and `approval.status`
- [ ] Whether nested member/action endpoints belong in v1 toolset
- [ ] `settlement_date` rename is reflected in create/update tool params and docstrings (#9423)
- [ ] Whether `preview_correction` and `approve_correction` belong in v1 toolset (#9423, #9753)
