# AGENTS.md

## Cursor Cloud specific instructions

This repo is `mcp-server-check`: a Python (>=3.10) package providing both an **MCP server**
(`mcp-server-check`) and a **CLI** (`check`) for the Check Payroll API. It is managed with
[`uv`](https://docs.astral.sh/uv/); dependencies are locked in `uv.lock`. There is no
database, frontend, or other service — the only "backend" it talks to is the remote Check API
(`https://sandbox.checkhq.com` by default).

The update script runs `uv sync --frozen`, so dependencies and the `.venv` are already in place
when a session starts. Run all commands through `uv run` (they execute inside `.venv`).

### Lint / test / build (see `.github/workflows/ci.yml`)
- Lint: `uv run ruff check src/ tests/` and `uv run ruff format --check src/ tests/`
- Tests: `uv run pytest tests/` — 465 tests. Tests need **no** API key or network; HTTP is
  mocked with `respx`.
- Optional git hooks mirroring CI lint: `uv run pre-commit install` (config in `.pre-commit-config.yaml`).

### Running the services
- MCP server: `uv run mcp-server-check`. **Requires `CHECK_API_KEY`** (exits with an error
  otherwise). Defaults to stdio transport and "dynamic" tool mode (exposes 3 meta-tools:
  `search_tools`, `list_toolsets`, `run_tool`). Env knobs: `CHECK_TOOL_MODE=all` (legacy
  all-tools), `CHECK_TRANSPORT`, `CHECK_ENV` / `CHECK_API_BASE_URL`, `CHECK_READ_ONLY`,
  `CHECK_TOOLSETS`, `CHECK_TOOLS`, `CHECK_EXCLUDE_TOOLS`.
- CLI: `uv run check ...` (see `CLI.md`). `check --help`, `check --version`, and
  `check init <target>` work without a key; any command that hits the API needs `CHECK_API_KEY`
  (passed via `--api-key` or env). Defaults to the **sandbox** environment.

### Non-obvious notes
- No real Check API key is provisioned in this environment. Tests and `--help`/`init` work
  offline; live API calls (and starting the MCP server) require a valid `CHECK_API_KEY` secret.
  To exercise tool round-trips without a key, mock the HTTP layer with `respx` (as the tests do)
  and drive the in-memory server via `fastmcp`'s `Client(mcp)`.
- `uv.lock` resolves `fastmcp` to a 3.x release even though `pyproject.toml` only pins
  `>=2.0.0`; use `uv sync --frozen` to stay consistent with CI.
