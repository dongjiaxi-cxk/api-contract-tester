"""Validate API responses against expected contracts."""

from __future__ import annotations

from typing import Any

import jsonschema


class ResponseValidator:
    """Validates API response against test expectations."""

    def __init__(self, max_response_time_ms: int | None = None) -> None:
        self.max_response_time_ms: int | None = max_response_time_ms

    def validate(self, result: dict[str, Any]) -> dict[str, Any]:
        """Validate a test result and mark it passed/failed."""
        messages: list[str] = []
        errors: list[str] = []
        test_case = result["test_case"]

        if result["error"]:
            messages.append("[FAIL] Error: " + result["error"])
            result["passed"] = False
            result["messages"] = messages
            return result

        status: int = result["status_code"]
        expected: int = test_case.expected_status

        if status == expected:
            messages.append(f"[PASS] Status: {status} (expected {expected})")
        else:
            messages.append(f"[FAIL] Status: {status} (expected {expected})")
            errors.append("status_mismatch")

        rt: int = result["response_time_ms"]
        if self.max_response_time_ms and rt > self.max_response_time_ms:
            messages.append(f"[FAIL] Response time: {rt}ms > {self.max_response_time_ms}ms threshold")
            errors.append("response_time")
        elif rt > 2000:
            messages.append(f"[WARN] Slow response: {rt}ms")
        else:
            messages.append(f"[PASS] Response time: {rt}ms")

        response = result.get("response")
        if response is not None and test_case.expected_content_type:
            ct: str = response.headers.get("Content-Type", "")
            if test_case.expected_content_type in ct:
                messages.append("[PASS] Content-Type: " + ct)
            else:
                messages.append("[FAIL] Content-Type: " + ct)
                errors.append("content_type_mismatch")

        if response is not None and test_case.response_schema:
            try:
                body: dict = response.json()
                jsonschema.validate(instance=body, schema=test_case.response_schema)
                messages.append("[PASS] Response body matches schema")
            except jsonschema.ValidationError as e:
                messages.append("[FAIL] Schema: " + str(e.message)[:100])
                errors.append("schema_mismatch")
            except ValueError:
                messages.append("[WARN] Not valid JSON, schema check skipped")

        result["passed"] = len(errors) == 0
        result["messages"] = messages
        return result

    def validate_all(self, results: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Validate all test results."""
        return [self.validate(r) for r in results]
