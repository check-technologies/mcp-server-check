# Example Skills

Ready-made [Claude Code custom slash commands](https://docs.anthropic.com/en/docs/claude-code/slash-commands#custom-slash-commands) that combine the Check MCP server's tools into multi-step workflows.

Each skill is a self-contained directory with a `SKILL.md` file and optional `references/` for supplementary context. Copy a skill into your project's `.claude/commands/` directory to use it as a `/slash-command` in Claude Code.

## Available Skills

| Skill | Description |
|---|---|
| [prior-provider-worker-migration](./prior-provider-worker-migration/) | Import employees and contractors into Check from a prior payroll provider's worker report (CSV, XLS, XLSX, or PDF). Parses the report, creates workplaces and workers via the API, and verifies every record against the source data. |

## Installation

Copy a skill's `SKILL.md` and `references/` directory into your project:

```bash
# From your project root
mkdir -p .claude/commands/prior-provider-worker-migration
cp -r /path/to/mcp-server-check/example-skills/prior-provider-worker-migration/* \
  .claude/commands/prior-provider-worker-migration/
```

Then invoke it in Claude Code:

```
/prior-provider-worker-migration
```

## Structure

```
example-skills/
└── prior-provider-worker-migration/
    ├── SKILL.md              # Main skill prompt (with frontmatter metadata)
    └── references/           # Format-specific parsing guides loaded on demand
        ├── tabular.md
        ├── multiline-cell.md
        ├── pdf-details.md
        └── pdf-list.md
```

- **`SKILL.md`** — The entry point. Contains YAML frontmatter (`name`, `model`, `description`) and the full step-by-step instructions the agent follows.
- **`references/`** — Supplementary documents the skill reads at runtime based on the detected input format. This keeps the main prompt focused and avoids loading unnecessary context.

## Writing New Skills

To add a new skill, create a directory under `example-skills/` with a `SKILL.md`:

```yaml
---
name: my-skill-name
description: >
  What the skill does and when to use it.
---

# Skill Title

Instructions go here...
```

If the skill needs detailed reference material that should only be loaded conditionally, put it in a `references/` subdirectory and have the skill read the relevant file based on the situation.
