"""Validate API responses against expected contracts."""

import jsonschema


class ResponseValidator:
    """Validates API response against test expectations."""

    def __init__(self, max_response_time_ms: int | None = None):
        self.max_response_time_ms = max_response_time_ms

    def validate(self, result: dict) -> dict:
        """Validate a test result and mark it passed/failed."""
        messages = []
        errors = []
        test_case = result["test_case"]

        if result["error"]:
            messages.append("[FAIL] Error: " + result["error"])
            result["passed"] = False
            result["messages"] = messages
            return result

        status = result["status_code"]
        expected = test_case.expected_status

        # 1. Status code
        if status == expected:
            messages.append("[PASS] Status: {} (expected {})".format(status, expected))
        else:
            messages.append("[FAIL] Status: {} (expected {})".format(status, expected))
            errors.append("status_mismatch")

        # 2. Response time
        rt = result["response_time_ms"]
        if self.max_response_time_ms and rt > self.max_response_time_ms:
            messages.append("[FAIL] Response time: {}ms > {}ms threshold".format(
                rt, self.max_response_time_ms))
            errors.append("response_time")
        elif rt > 2000:
            messages.append("[WARN] Slow response: {}ms".format(rt))
        else:
            messages.append("[PASS] Response time: {}ms".format(rt))

        # 3. Content-Type
        response = result.get("response")
        if response is not None and test_case.expected_content_type:
            ct = response.headers.get("Content-Type", "")
            if test_case.expected_content_type in ct:
                messages.append("[PASS] Content-Type: " + ct)
            else:
                messages.append("[FAIL] Content-Type: " + ct)
                errors.append("content_type_mismatch")

        # 4. JSON Schema
        if response is not None and test_case.response_schema:
            try:
                body = response.json()
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

    def validate_all(self, results: list) -> list:
        """Validate all test results."""
        return [self.validate(r) for r in results]