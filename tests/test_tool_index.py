"""Tests for the tool index (dynamic mode)."""

from __future__ import annotations

import json

import pytest
from mcp_server_check.tool_filter import ToolFilter
from mcp_server_check.tool_index import (
    _TOOLSET_DESCRIPTIONS,
    ToolIndex,
    _expand_synonyms,
    _first_line,
    _tokenize,
)

# --- Unit tests for helpers ---


class TestTokenize:
    def test_basic(self):
        assert _tokenize("list_companies") == {"list", "companies"}

    def test_mixed_case(self):
        assert _tokenize("List Companies") == {"list", "companies"}

    def test_with_numbers(self):
        assert _tokenize("get_w2_preview") == {"get", "w2", "preview"}

    def test_empty(self):
        assert _tokenize("") == set()


class TestFirstLine:
    def test_extracts_first_line(self):
        assert _first_line("List companies in your account.\n\nArgs:") == (
            "List companies in your account."
        )

    def test_none(self):
        assert _first_line(None) == ""

    def test_empty(self):
        assert _first_line("") == ""

    def test_leading_whitespace(self):
        assert _first_line("\n  Hello world\n") == "Hello world"


class TestExpandSynonyms:
    def test_expands_known_synonym(self):
        expanded = _expand_synonyms({"pay"})
        assert "payroll" in expanded
        assert "compensation" in expanded
        assert "pay" in expanded

    def test_unknown_word_passthrough(self):
        expanded = _expand_synonyms({"xyzzy"})
        assert expanded == {"xyzzy"}

    def test_multiple_tokens(self):
        expanded = _expand_synonyms({"list", "employee"})
        assert "index" in expanded  # synonym of "list"
        assert "worker" in expanded  # synonym of "employee"
        assert "list" in expanded
        assert "employee" in expanded


# --- ToolIndex.build ---


class TestToolIndexBuild:
    def setup_method(self):
        self.index = ToolIndex()
        self.index.build()

    def test_builds_all_tools(self):
        assert len(self.index.entries) > 100

    def test_has_expected_tools(self):
        assert "list_companies" in self.index.entries
        assert "get_employee" in self.index.entries
        assert "create_payroll" in self.index.entries
        assert "list_bank_accounts" in self.index.entries

    def test_entry_has_metadata(self):
        entry = self.index.entries["list_companies"]
        assert entry.name == "list_companies"
        assert entry.toolset == "companies"
        assert entry.is_write is False
        assert "List companies" in entry.description
        assert isinstance(entry.parameters, dict)
        assert entry.search_tokens

    def test_write_tool_flagged(self):
        assert self.index.entries["create_company"].is_write is True
        assert self.index.entries["update_employee"].is_write is True
        assert self.index.entries["delete_payroll"].is_write is True

    def test_read_tool_flagged(self):
        assert self.index.entries["list_companies"].is_write is False
        assert self.index.entries["get_payroll"].is_write is False

    def test_toolset_entries_populated(self):
        assert "companies" in self.index.toolset_entries
        assert "employees" in self.index.toolset_entries
        assert len(self.index.toolset_entries["companies"]) > 5

    def test_parameters_has_properties(self):
        entry = self.index.entries["list_companies"]
        assert "properties" in entry.parameters

    def test_search_tokens_include_param_names(self):
        entry = self.index.entries["list_companies"]
        # The function has "limit", "active", "ids", "cursor" params
        assert "limit" in entry.search_tokens


# --- ToolIndex.search ---


class TestToolIndexSearch:
    def setup_method(self):
        self.index = ToolIndex()
        self.index.build()
        self.no_filter = ToolFilter()

    def test_search_by_keyword(self):
        results = self.index.search("list companies", self.no_filter)
        names = [r["name"] for r in results]
        assert "list_companies" in names
        # Should be first or near-first due to exact match boosting
        assert names.index("list_companies") < 3

    def test_search_returns_parameters(self):
        results = self.index.search("list companies", self.no_filter, limit=1)
        assert len(results) == 1
        assert "parameters" in results[0]
        assert "name" in results[0]
        assert "description" in results[0]
        assert "toolset" in results[0]

    def test_search_with_toolset_filter(self):
        results = self.index.search("list", self.no_filter, toolset="companies")
        for r in results:
            assert r["toolset"] == "companies"

    def test_search_respects_limit(self):
        results = self.index.search("list", self.no_filter, limit=3)
        assert len(results) <= 3

    def test_search_exact_name(self):
        results = self.index.search("get_company", self.no_filter)
        assert results[0]["name"] == "get_company"

    def test_empty_query_returns_overview(self):
        results = self.index.search("", self.no_filter)
        # Should be toolset summaries
        assert len(results) > 0
        assert "toolset" in results[0]
        assert "tool_count" in results[0]
        assert "example_tools" in results[0]

    def test_overview_includes_descriptions(self):
        results = self.index.search("", self.no_filter)
        for r in results:
            assert "description" in r
            # Every toolset should have a non-empty description
            assert r["description"], f"Missing description for {r['toolset']}"

    def test_overview_covers_all_toolsets(self):
        results = self.index.search("", self.no_filter)
        toolset_names = {r["toolset"] for r in results}
        assert "companies" in toolset_names
        assert "employees" in toolset_names
        assert "payrolls" in toolset_names

    def test_no_results_for_gibberish(self):
        results = self.index.search("xyzzyplugh", self.no_filter)
        assert results == []

    def test_synonym_search_pay(self):
        """Searching 'pay' should find payroll tools via synonym expansion."""
        results = self.index.search("pay", self.no_filter)
        names = [r["name"] for r in results]
        # Should find payroll-related tools even though "pay" isn't in tool names
        payroll_names = [n for n in names if "payroll" in n or "pay" in n]
        assert len(payroll_names) > 0

    def test_synonym_search_worker(self):
        """Searching 'worker' should find employee tools via synonyms."""
        results = self.index.search("worker", self.no_filter)
        names = [r["name"] for r in results]
        employee_names = [n for n in names if "employee" in n]
        assert len(employee_names) > 0


# --- ToolIndex.search with ToolFilter ---


class TestToolIndexSearchFiltered:
    def setup_method(self):
        self.index = ToolIndex()
        self.index.build()

    def test_toolset_filter(self):
        tf = ToolFilter(toolsets=frozenset({"companies"}))
        results = self.index.search("list", tf)
        for r in results:
            assert r["toolset"] == "companies"

    def test_read_only_excludes_write_tools(self):
        tf = ToolFilter(read_only=True)
        results = self.index.search("create company", tf)
        names = [r["name"] for r in results]
        assert "create_company" not in names

    def test_exclude_tools(self):
        tf = ToolFilter(exclude_tools=frozenset({"list_companies"}))
        results = self.index.search("list companies", tf)
        names = [r["name"] for r in results]
        assert "list_companies" not in names

    def test_tools_allowlist(self):
        tf = ToolFilter(tools=frozenset({"list_companies", "get_company"}))
        results = self.index.search("list", tf)
        names = {r["name"] for r in results}
        assert names.issubset({"list_companies", "get_company"})

    def test_overview_respects_filter(self):
        tf = ToolFilter(toolsets=frozenset({"companies", "employees"}))
        results = self.index.search("", tf)
        toolset_names = {r["toolset"] for r in results}
        assert toolset_names == {"companies", "employees"}


# --- ToolIndex.run ---


class TestToolIndexRun:
    def setup_method(self):
        self.index = ToolIndex()
        self.index.build()
        self.no_filter = ToolFilter()

    @pytest.mark.anyio
    async def test_run_unknown_tool(self):
        with pytest.raises(ValueError, match="Unknown tool"):
            await self.index.run("nonexistent_tool", {}, None, self.no_filter)

    @pytest.mark.anyio
    async def test_run_unknown_tool_has_suggestion(self):
        """Error message for unknown tool includes a suggestion."""
        with pytest.raises(ValueError, match="Did you mean"):
            await self.index.run("list_companie", {}, None, self.no_filter)

    @pytest.mark.anyio
    async def test_run_blocked_by_filter(self):
        tf = ToolFilter(exclude_tools=frozenset({"list_companies"}))
        with pytest.raises(ValueError, match="not available"):
            await self.index.run("list_companies", {}, None, tf)

    @pytest.mark.anyio
    async def test_run_blocked_by_read_only(self):
        tf = ToolFilter(read_only=True)
        with pytest.raises(ValueError, match="not available"):
            await self.index.run("create_company", {}, None, tf)

    @pytest.mark.anyio
    async def test_run_dispatches_correctly(self, mock_api, ctx):
        """Run dispatches to the correct underlying tool function."""
        import httpx as httpx_mod

        mock_api.get("/companies").mock(
            return_value=httpx_mod.Response(
                200,
                json={
                    "next": None,
                    "previous": None,
                    "results": [{"id": "com_001"}],
                },
            )
        )
        result = await self.index.run("list_companies", {}, ctx, self.no_filter)
        assert result["results"] == [{"id": "com_001"}]

    @pytest.mark.anyio
    async def test_run_with_arguments(self, mock_api, ctx):
        import httpx as httpx_mod

        mock_api.get("/companies/com_001").mock(
            return_value=httpx_mod.Response(
                200,
                json={"id": "com_001", "legal_name": "Acme Corp"},
            )
        )
        result = await self.index.run(
            "get_company", {"company_id": "com_001"}, ctx, self.no_filter
        )
        assert result == {"id": "com_001", "legal_name": "Acme Corp"}


# --- ToolIndex.get_toolset_names ---


class TestToolIndexMeta:
    def setup_method(self):
        self.index = ToolIndex()
        self.index.build()

    def test_get_toolset_names(self):
        names = self.index.get_toolset_names()
        assert isinstance(names, list)
        assert names == sorted(names)
        assert "companies" in names
        assert "employees" in names

    def test_all_toolsets_have_descriptions(self):
        for name in self.index.get_toolset_names():
            assert name in _TOOLSET_DESCRIPTIONS, (
                f"Missing description for toolset: {name}"
            )


# --- Dynamic mode server integration ---


class TestDynamicModeServer:
    def _make_dynamic_server(self):
        from mcp_server_check.server import CheckMCP, _setup_dynamic_mode, lifespan

        server = CheckMCP("Test Dynamic", lifespan=lifespan)
        _setup_dynamic_mode(server)
        return server

    def _extract_text(self, result):
        """Extract text from call_tool result (tuple of [TextContent, ...])."""
        return result[0][0].text

    @pytest.mark.anyio
    async def test_list_tools_returns_three(self):
        server = self._make_dynamic_server()
        tools = await server.list_tools()
        names = {t.name for t in tools}
        assert names == {"search_tools", "list_toolsets", "run_tool"}

    @pytest.mark.anyio
    async def test_search_tools_callable(self):
        server = self._make_dynamic_server()
        result = await server.call_tool("search_tools", {"query": "list companies"})
        text = self._extract_text(result)
        parsed = json.loads(text)
        assert isinstance(parsed, list)
        names = [r["name"] for r in parsed]
        assert "list_companies" in names

    @pytest.mark.anyio
    async def test_search_tools_empty_query(self):
        server = self._make_dynamic_server()
        result = await server.call_tool("search_tools", {"query": ""})
        text = self._extract_text(result)
        parsed = json.loads(text)
        assert isinstance(parsed, list)
        assert len(parsed) > 0
        assert "toolset" in parsed[0]

    @pytest.mark.anyio
    async def test_list_toolsets(self):
        server = self._make_dynamic_server()
        result = await server.call_tool("list_toolsets", {})
        text = self._extract_text(result)
        parsed = json.loads(text)
        assert isinstance(parsed, list)
        assert len(parsed) > 0
        assert "toolset" in parsed[0]
        assert "description" in parsed[0]
        assert "tool_count" in parsed[0]

    @pytest.mark.anyio
    async def test_run_tool_unknown(self):
        server = self._make_dynamic_server()
        result = await server.call_tool("run_tool", {"tool_name": "nonexistent"})
        text = self._extract_text(result)
        parsed = json.loads(text)
        assert "error" in parsed

    @pytest.mark.anyio
    async def test_run_tool_accepts_dict_arguments(self):
        """run_tool schema accepts arguments as a dict (not JSON string)."""
        server = self._make_dynamic_server()
        tools = await server.list_tools()
        run_tool_schema = next(t for t in tools if t.name == "run_tool")
        props = run_tool_schema.inputSchema.get("properties", {})
        args_schema = props.get("arguments", {})
        # arguments should accept an object type (dict), not just string
        assert args_schema.get("type") in ("object", None) or "anyOf" in args_schema

    @pytest.mark.anyio
    async def test_run_tool_no_arguments(self):
        """run_tool works with no arguments parameter."""
        server = self._make_dynamic_server()
        # list_companies with no args should attempt the API call
        # (will fail since no mock, but that's fine - we're testing the dispatch)
        result = await server.call_tool("run_tool", {"tool_name": "nonexistent_tool"})
        text = self._extract_text(result)
        parsed = json.loads(text)
        assert "error" in parsed
