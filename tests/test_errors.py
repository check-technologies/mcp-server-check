"""Tests for tool errors and their logging."""

from __future__ import annotations

import json
import logging

import pytest
from mcp_server_check.errors import (
    CheckAPIError,
    CheckToolError,
    ExpectedToolErrorFilter,
    ResponseTooLargeError,
)
from mcp_server_check.recovery import Failure, Hint, Remedies


class TestCheckToolError:
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

        error.remedies = Remedies(hints=(Hint("Ask for less."),))

        assert error.payload == {**base, "alternatives": [], "hints": ["Ask for less."]}
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


class TestExpectedToolErrorFilter:
    @staticmethod
    def record(error: Exception) -> logging.LogRecord:
        return logging.LogRecord(
            "fastmcp.server.server",
            logging.ERROR,
            __file__,
            1,
            "Error calling tool %r",
            ("get_company",),
            (type(error), error, None),
        )

    def test_check_tool_error_becomes_one_warning_line(self):
        record = self.record(CheckToolError({"error": "bad"}))

        assert ExpectedToolErrorFilter().filter(record) is True
        assert record.levelno == logging.WARNING
        assert record.exc_info is None
        assert record.getMessage() == (
            "Error calling tool 'get_company': " + json.dumps({"error": "bad"})
        )

    def test_other_errors_keep_their_traceback(self):
        record = self.record(RuntimeError("boom"))

        assert ExpectedToolErrorFilter().filter(record) is True
        assert record.levelno == logging.ERROR
        assert record.exc_info is not None

    def test_install_is_idempotent(self):
        logger = logging.getLogger("test_install_is_idempotent")

        ExpectedToolErrorFilter.install(logger)
        ExpectedToolErrorFilter.install(logger)

        assert len(logger.filters) == 1
