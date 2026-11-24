"""Tests for tool errors and their logging."""

from __future__ import annotations

import json
import logging

import pytest
from mcp_server_check.errors import (
    CheckAPIError,
    CheckToolError,
    ResponseTooLargeError,
    result_shape,
)
from mcp_server_check.recovery import Failure, Hint, Remedies


def compact(value) -> int:
    """Characters of a value as a tool result delivers it."""
    return len(json.dumps(value, separators=(",", ":")))


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

    def test_too_large_advice_fits_the_tool(self):
        """A program's result is what it returned, so filters and limits on a
        call are the wrong advice for run_code."""
        program = ResponseTooLargeError("run_code", 10, 5, unit="character")
        assert "inside the program" in program.payload["detail"]
        assert "Narrow the request" not in program.payload["detail"]
        call = ResponseTooLargeError("get_company", 10, 5)
        assert "Narrow the request" in call.payload["detail"]

    def test_too_large_names_the_largest_parts(self):
        error = ResponseTooLargeError(
            "run_code",
            10,
            5,
            unit="character",
            largest=["result[0]['response_body'] (9 characters)"],
        )
        assert error.payload["detail"].endswith(
            "Largest parts: result[0]['response_body'] (9 characters)."
        )

    def test_too_large_carries_the_shape_and_points_at_it(self):
        shape = {"type": "list", "size": 9, "length": 1, "item_keys": ["id"]}

        error = ResponseTooLargeError("run_code", 10, 5, unit="character", shape=shape)

        assert error.payload["shape"] == shape
        assert error.payload["detail"].endswith(
            '"shape" below describes the result, so the next program can pick '
            "its part without probing it first."
        )
        assert error.payload["response_too_large"] is True
        assert error.payload["size"] == 10
        assert error.payload["limit"] == 5

    def test_too_large_without_a_shape_has_no_shape_field(self):
        payload = ResponseTooLargeError("get_company", 10, 5).payload

        assert "shape" not in payload
        assert "shape" not in payload["detail"]

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


class TestResultShape:
    def test_dict_sizes_each_key_biggest_first(self):
        value = {
            "count": 2,
            "company": {"id": "com_1", "name": "Acme"},
            "employees": [{"id": "emp_1", "name": "x" * 300}] * 2,
            "note": "hi",
            "cursor": None,
        }

        shape = result_shape(value)

        assert shape["type"] == "dict"
        assert shape["length"] == 5
        assert shape["size"] == compact(value)
        assert list(shape["keys"]) == [
            "employees",
            "company",
            "note",
            "cursor",
            "count",
        ]
        assert shape["keys"]["employees"] == {
            "type": "list",
            "size": compact(value["employees"]),
            "length": 2,
            "item_keys": ["id", "name"],
        }
        assert shape["keys"]["company"] == {
            "type": "dict",
            "size": compact(value["company"]),
            "length": 2,
            "keys": ["id", "name"],
        }
        assert shape["keys"]["note"] == {"type": "str", "size": 4, "length": 2}
        assert shape["keys"]["cursor"] == {"type": "None", "size": 4}
        assert shape["keys"]["count"] == {"type": "int", "size": 1}
        assert "keys_omitted" not in shape

    def test_list_of_dicts_names_the_first_items_keys(self):
        value = [{"id": f"log_{i}", "response_body": "x" * 500} for i in range(3)]

        assert result_shape(value) == {
            "type": "list",
            "size": compact(value),
            "length": 3,
            "item_keys": ["id", "response_body"],
        }

    def test_list_of_scalars_names_the_item_type(self):
        assert result_shape(["a", "b"]) == {
            "type": "list",
            "size": 9,
            "length": 2,
            "item_type": "str",
        }
        assert result_shape([]) == {"type": "list", "size": 2, "length": 0}

    @pytest.mark.parametrize(
        ("value", "shape"),
        [
            ("x" * 40, {"type": "str", "size": 42, "length": 40}),
            (42, {"type": "int", "size": 2}),
            (True, {"type": "bool", "size": 4}),
            (None, {"type": "None", "size": 4}),
        ],
    )
    def test_scalar_is_its_type_and_length(self, value, shape):
        assert result_shape(value) == shape

    def test_nests_one_level_only(self):
        value = {
            "payroll": {
                "items": [{"earnings": [{"amount": "1.00"} for _ in range(50)]}],
                "totals": {"gross": {"cents": 100}},
            }
        }

        shape = result_shape(value)

        assert shape["keys"]["payroll"] == {
            "type": "dict",
            "size": compact(value["payroll"]),
            "length": 2,
            "keys": ["items", "totals"],
        }
        assert "earnings" not in json.dumps(shape)

    def test_keeps_the_biggest_keys_up_to_the_cap(self):
        value = {f"key_{i:02d}": "x" * i for i in range(40)}

        shape = result_shape(value, max_keys=25)

        assert len(shape["keys"]) == 25
        assert shape["keys_omitted"] == 15
        assert list(shape["keys"])[0] == "key_39"
        assert "key_14" not in shape["keys"]

    def test_first_item_keys_are_capped(self):
        value = [{f"k{i}": i for i in range(30)}]

        shape = result_shape(value, max_keys=25)

        assert len(shape["item_keys"]) == 25
        assert shape["item_keys_omitted"] == 5

    def test_stays_within_the_character_cap(self):
        value = {
            f"record_group_{i}": {f"inner_field_name_{j}": j for j in range(25)}
            for i in range(25)
        }

        shape = result_shape(value, max_chars=2_000)

        assert compact(shape) <= 2_000
        assert 0 < len(shape["keys"]) < 25
        assert shape["keys_omitted"] == 25 - len(shape["keys"])

    def test_list_item_keys_stay_within_the_character_cap(self):
        value = [{f"a_rather_long_field_name_{i}": i for i in range(25)}]

        shape = result_shape(value, max_chars=300)

        assert compact(shape) <= 300
        assert shape["item_keys_omitted"] == 25 - len(shape["item_keys"])

    def test_non_string_keys_are_named_as_strings(self):
        assert list(result_shape({1: "a"})["keys"]) == ["1"]


class TestCheckAPIError:
    @pytest.mark.parametrize(
        "result", [{"id": "com_001"}, {"error": "text"}, "plain", None]
    )
    def test_from_result_ignores_success(self, result):
        assert CheckAPIError.from_result(result) is None

    def test_from_result_wraps_error_dict(self):
        error = CheckAPIError.from_result({"error": True, "status_code": 404})

        assert error.payload == {"error": True, "status_code": 404}
