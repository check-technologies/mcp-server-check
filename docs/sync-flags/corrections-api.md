# FLAG: Corrections API needs MCP/CLI toolset

**Status:** Needs human sign-off before implementation  
**Last updated:** 2026-07-29 (check-api PR #9018)

## Triggering merges

| check-api PR | Merge commit | What landed |
|---|---|---|
| [#8970](https://github.com/check-technologies/check-api-primary/pull/8970) | `46c23fb3e3` | Initial public corrections API: `POST /corrections`, `GET /corrections`, `GET /corrections/{id}` |
| [#9018](https://github.com/check-technologies/check-api-primary/pull/9018) | `aa7c51be38` | List filters, `PATCH /corrections/{id}`, draft-only `DELETE` |

`mcp-server-check` has **no `corrections` toolset**. Per sync workflow guardrails, this automation will not unilaterally add a new resource module.

## Public request-surface changes in #9018

### New endpoint

- **`PATCH /corrections/{id}`** (`partial_update`, scope `payroll:write`)
  - Body (`UpdateCorrectionInputSerializer`): optional `fulfillment_date` (date, nullable), `description` (string, nullable/blank), `metadata` (object). Unknown fields rejected.
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

- `GET /corrections` list items now include read-only `fulfillment_date`, `description`, `metadata`.

## Suggested toolset (for human review)

When approved, add `src/mcp_server_check/tools/corrections.py` wired into `_TOOLSETS`, covering at minimum:

| Tool | HTTP | Notes |
|---|---|---|
| `list_corrections` | `GET /corrections` | Params: `company`, `year`, `status`, `payroll`, pagination |
| `get_correction` | `GET /corrections/{id}` | From #8970 |
| `create_correction` | `POST /corrections` | From #8970 |
| `update_correction` | `PATCH /corrections/{id}` | New in #9018 |
| `delete_correction` | `DELETE /corrections/{id}` | Draft-only contract (#9018) |

Additional `@action` endpoints on `CorrectionViewSet` (save, apply_updates, corrected_payrolls, etc.) are out of scope for this flag — confirm separately whether they should be public MCP tools.

## Please verify

- [ ] Corrections API is ready for MCP/CLI exposure (feature flag `ENABLE_CORRECTIONS_API` gating on API keys)
- [ ] Tool naming and `read_only` gating conventions
- [ ] Complete enum values for `status` filter
- [ ] Whether nested member/action endpoints belong in v1 toolset
