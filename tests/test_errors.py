"""Tests for tool errors and their logging."""

from __future__ import annotations

import json
import logging

import pytest
from mcp_server_check.errors import (
    CheckAPIError,
    CheckToolError,
    ResponseTooLargeError,
)
from mcp_server_check.recovery import Failure, Hint, Remedies


class TestCheckToolError:
    def test_fastmcp_logs_it_at_debug(self):
        assert CheckToolError({"error": "bad"}).log_level == logging.DEBUG

    def test_message_is_the_json_payload(self):
        error = CheckToolError({"error": "bad"})

        assert json.loads(str(error)) == {"error": "bad"}

    @pytest.mark.parametrize(
        ("error", "failure"),
        [
            (ResponseTooLargeError("get_company", 10, 5), Failure.TOO_LARGE),
            (CheckAPIError({"error": True, "timeout": True}), Failure.TIMED_OUT),
            (CheckAPIError({"error": True, "status_code": 400}), None),
        ],
    )
    def test_failure(self, error, failure):
        assert error.failure is failure

    def test_remedies_are_part_of_payload_and_message(self):
        error = ResponseTooLargeError("get_company", 10, 5)
        base = dict(error.payload)

        error.remedies = Remedies(
            hints=(Hint(tool="get_company", description="Ask for less."),)
        )

        assert error.payload == {
            **base,
            "alternatives": [],
            "hints": [
                {"tool": "get_company", "description": "Ask for less.", "arguments": []}
            ],
        }
        assert json.loads(str(error)) == error.payload
        assert error.failure is Failure.TOO_LARGE


class TestCheckAPIError:
    @pytest.mark.parametrize(
        "result", [{"id": "com_001"}, {"error": "text"}, "plain", None]
    )
    def test_from_result_ignores_success(self, result):
        assert CheckAPIError.from_result(result) is None

    def test_from_result_wraps_error_dict(self):
        error = CheckAPIError.from_result({"error": True, "status_code": 404})

        assert error.payload == {"error": True, "status_code": 404}
