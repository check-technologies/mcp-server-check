"""Tool metadata index for dynamic 2-tool MCP mode.

Builds a searchable index of all tool functions, enabling LLMs to discover
and execute tools on-demand via search_tools + run_tool instead of receiving
all tool schemas upfront.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from mcp.server.fastmcp.tools.base import Tool

from mcp_server_check.tool_filter import ToolFilter, is_write_tool
from mcp_server_check.tools import collect_all_tools

# Synonym groups: searching for any word in a group also matches others.
_SYNONYMS: dict[str, set[str]] = {}
_SYNONYM_GROUPS: list[set[str]] = [
    {"pay", "payroll", "compensation", "earnings", "wages", "salary"},
    {"employee", "worker", "staff", "team"},
    {"company", "employer", "business", "organization"},
    {"contractor", "vendor", "1099"},
    {"create", "add", "new", "setup", "set"},
    {"delete", "remove", "destroy"},
    {"update", "edit", "modify", "change", "patch"},
    {"list", "index", "all", "browse"},
    {"get", "show", "view", "read", "fetch", "retrieve", "detail", "details"},
    {"payment", "disbursement", "deposit", "transfer"},
    {"tax", "withholding", "filing", "w2", "w4"},
    {"bank", "account", "ach", "routing"},
    {"report", "summary", "journal", "export"},
    {"webhook", "callback", "event", "notification"},
    {"approve", "submit", "confirm"},
    {"simulate", "sandbox", "test"},
]

# Build the synonym lookup
for group in _SYNONYM_GROUPS:
    for word in group:
        _SYNONYMS[word] = group


def _expand_synonyms(tokens: set[str]) -> set[str]:
    """Expand a set of tokens with synonyms."""
    expanded = set(tokens)
    for token in tokens:
        if token in _SYNONYMS:
            expanded |= _SYNONYMS[token]
    return expanded


@dataclass
class ToolEntry:
    """Metadata for a single tool in the index."""

    name: str
    description: str
    toolset: str
    is_write: bool
    parameters: dict[str, Any]
    tool: Tool
    search_tokens: set[str] = field(default_factory=set)


def _tokenize(text: str) -> set[str]:
    """Split text into lowercase tokens for search matching."""
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _first_line(docstring: str | None) -> str:
    """Extract the first non-empty line from a docstring."""
    if not docstring:
        return ""
    for line in docstring.strip().split("\n"):
        stripped = line.strip()
        if stripped:
            return stripped
    return ""


# Toolset descriptions for the overview
_TOOLSET_DESCRIPTIONS: dict[str, str] = {
    "bank_accounts": "Create, update, delete, and view bank accounts for companies, employees, and contractors.",
    "companies": "Manage companies, signatories, enrollment profiles, reports, and EIN verifications.",
    "compensation": "Manage earning rates, earning codes, benefits, post-tax deductions, net pay splits, and pay schedules.",
    "components": "Generate embedded UI component URLs for company, employee, and contractor onboarding flows.",
    "contractor_payments": "Create, update, delete, and view contractor payment records.",
    "contractors": "Manage 1099 contractors, their forms, and tax documents.",
    "documents": "Access company tax documents, authorization documents, employee/contractor tax documents, and setup documents.",
    "employees": "Manage W-2 employees, their forms, paystubs, attributes, and reciprocity elections.",
    "external_payrolls": "Create and manage external (imported) payrolls for historical data.",
    "forms": "List and render tax forms (W-4, state withholding, etc.).",
    "payments": "View payments, payment attempts, and retry/refund/cancel payments.",
    "payroll_items": "Create, update, and delete individual payroll line items within a payroll.",
    "payrolls": "Create, preview, approve, and manage payroll runs. Includes sandbox simulation tools.",
    "platform": "Platform-level tools: notifications, communications, usage, integrations, accounting, setups, and requirements.",
    "tax": "Manage company and employee tax parameters, elections, filings, exemptions, and tax statements.",
    "webhooks": "Create, update, delete, and test webhook configurations.",
    "workflows": "Composite tools that combine multiple API calls: company overview, employee snapshot, payment diagnostics.",
    "workplaces": "Create, update, and view company workplace locations.",
}


class ToolIndex:
    """Searchable index of all tool functions."""

    def __init__(self) -> None:
        self._entries: dict[str, ToolEntry] = {}
        self._toolset_entries: dict[str, list[ToolEntry]] = {}

    def build(self) -> None:
        """Build the index from all registered toolsets."""
        all_tools = collect_all_tools()
        for toolset_name, functions in all_tools.items():
            toolset_list: list[ToolEntry] = []
            for fn in functions:
                tool = Tool.from_function(fn)
                description = _first_line(fn.__doc__)
                # Include parameter names in search tokens for richer matching
                param_names = set()
                props = tool.parameters.get("properties", {})
                for pname in props:
                    param_names |= _tokenize(pname)
                tokens = (
                    _tokenize(tool.name)
                    | _tokenize(toolset_name)
                    | _tokenize(description)
                    | param_names
                )
                entry = ToolEntry(
                    name=tool.name,
                    description=description,
                    toolset=toolset_name,
                    is_write=is_write_tool(tool.name),
                    parameters=tool.parameters,
                    tool=tool,
                    search_tokens=tokens,
                )
                self._entries[tool.name] = entry
                toolset_list.append(entry)
            self._toolset_entries[toolset_name] = toolset_list

    def search(
        self,
        query: str,
        tool_filter: ToolFilter,
        toolset: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Search tools by keyword query.

        Args:
            query: Search keywords (e.g. "list companies"). Empty returns overview.
            tool_filter: Active ToolFilter for visibility checks.
            toolset: Optional toolset name to restrict search.
            limit: Maximum results to return.

        Returns:
            List of tool metadata dicts with name, description, toolset, parameters.
        """
        if not query.strip():
            return self._toolset_overview(tool_filter, toolset)

        query_tokens = _tokenize(query)
        if not query_tokens:
            return self._toolset_overview(tool_filter, toolset)

        # Expand query tokens with synonyms for broader matching
        expanded_query = _expand_synonyms(query_tokens)

        scored: list[tuple[float, ToolEntry]] = []
        query_lower = query.lower().replace(" ", "_")

        for entry in self._entries.values():
            if not tool_filter.is_tool_allowed(entry.name, entry.toolset):
                continue
            if toolset and entry.toolset != toolset:
                continue

            # Direct token overlap (original query, no expansion)
            direct_overlap = len(query_tokens & entry.search_tokens)
            # Expanded token overlap (with synonyms)
            expanded_overlap = len(expanded_query & entry.search_tokens)

            if direct_overlap == 0 and expanded_overlap == 0:
                continue

            # Direct matches score higher than synonym matches
            score = direct_overlap / len(query_tokens)
            if expanded_overlap > direct_overlap:
                score += (expanded_overlap - direct_overlap) / len(query_tokens) * 0.5

            # Boost exact name match
            if entry.name == query_lower:
                score += 10.0
            # Boost substring match in name
            elif query_lower in entry.name:
                score += 3.0
            # Boost if name contains query as substring
            elif entry.name in query_lower:
                score += 1.0

            scored.append((score, entry))

        scored.sort(key=lambda x: (-x[0], x[1].name))
        return [
            {
                "name": entry.name,
                "description": entry.description,
                "toolset": entry.toolset,
                "parameters": entry.parameters,
            }
            for _, entry in scored[:limit]
        ]

    def _toolset_overview(
        self, tool_filter: ToolFilter, toolset: str | None = None
    ) -> list[dict[str, Any]]:
        """Return a summary of available toolsets when no query is given."""
        result: list[dict[str, Any]] = []
        for ts_name, entries in sorted(self._toolset_entries.items()):
            if toolset and ts_name != toolset:
                continue
            allowed = [
                e for e in entries if tool_filter.is_tool_allowed(e.name, e.toolset)
            ]
            if not allowed:
                continue
            example_names = [e.name for e in allowed[:3]]
            result.append(
                {
                    "toolset": ts_name,
                    "description": _TOOLSET_DESCRIPTIONS.get(ts_name, ""),
                    "tool_count": len(allowed),
                    "example_tools": example_names,
                }
            )
        return result

    def get_toolset_names(self) -> list[str]:
        """Return sorted list of all toolset names."""
        return sorted(self._toolset_entries.keys())

    async def run(
        self,
        name: str,
        arguments: dict[str, Any],
        context: Any,
        tool_filter: ToolFilter,
    ) -> Any:
        """Look up and execute a tool by name.

        Args:
            name: Tool name to execute.
            arguments: Tool arguments dict.
            context: MCP Context object to inject.
            tool_filter: Active ToolFilter for authorization.

        Returns:
            Tool execution result.

        Raises:
            ValueError: If tool not found or not allowed.
        """
        entry = self._entries.get(name)
        if entry is None:
            suggestion = self._suggest_tool(name)
            msg = f"Unknown tool: '{name}'"
            if suggestion:
                msg += f". Did you mean '{suggestion}'?"
            raise ValueError(msg)
        if not tool_filter.is_tool_allowed(entry.name, entry.toolset):
            raise ValueError(
                f"Tool '{name}' is not available in the current configuration"
            )
        return await entry.tool.run(arguments, context=context)

    def _suggest_tool(self, name: str) -> str | None:
        """Find the closest matching tool name for error messages."""
        tokens = _tokenize(name)
        if not tokens:
            return None
        best_name = None
        best_score = 0
        for entry in self._entries.values():
            overlap = len(tokens & _tokenize(entry.name))
            if overlap > best_score:
                best_score = overlap
                best_name = entry.name
        return best_name if best_score > 0 else None

    def get_entry(self, name: str) -> ToolEntry | None:
        """Get a tool entry by name."""
        return self._entries.get(name)

    @property
    def entries(self) -> dict[str, ToolEntry]:
        """All indexed tool entries."""
        return self._entries

    @property
    def toolset_entries(self) -> dict[str, list[ToolEntry]]:
        """Tool entries grouped by toolset."""
        return self._toolset_entries
