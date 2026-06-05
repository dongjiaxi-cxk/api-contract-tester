"""Validate API responses against expected contracts."""

import jsonschema


class ResponseValidator:
    """Validates API response against test expectations."""

    def validate(self, result: dict) -> dict:
        """Validate a test result and mark it passed/failed."""
        messages = []
        errors = []
        test_case = result["test_case"]

        # Check for connection/network errors
        if result["error"]:
            messages.append("[FAIL] Error: " + result["error"])
            result["passed"] = False
            result["messages"] = messages
            return result

        status = result["status_code"]
        expected = test_case.expected_status

        # 1. Validate status code
        if status == expected:
            messages.append("[PASS] Status: " + str(status) + " (expected " + str(expected) + ")")
        else:
            messages.append("[FAIL] Status: " + str(status) + " (expected " + str(expected) + ")")
            errors.append("status_mismatch")

        # 2. Validate response time
        if result["response_time_ms"] > 2000:
            messages.append("[WARN] Slow response: " + str(result["response_time_ms"]) + "ms")
        else:
            messages.append("[PASS] Response time: " + str(result["response_time_ms"]) + "ms")

        # 3. Validate Content-Type
        response = result.get("response")
        if response is not None and test_case.expected_content_type:
            content_type = response.headers.get("Content-Type", "")
            if test_case.expected_content_type in content_type:
                messages.append("[PASS] Content-Type: " + content_type)
            else:
                messages.append("[FAIL] Content-Type: " + content_type)
                errors.append("content_type_mismatch")

        # 4. Validate response body against JSON Schema
        if response is not None and test_case.response_schema:
            try:
                response_json = response.json()
                jsonschema.validate(instance=response_json, schema=test_case.response_schema)
                messages.append("[PASS] Response body matches schema")
            except jsonschema.ValidationError as e:
                messages.append("[FAIL] Schema validation: " + str(e.message)[:100])
                errors.append("schema_mismatch")
            except ValueError:
                messages.append("[WARN] Response is not valid JSON, skipping schema check")

        result["passed"] = status == expected and len(errors) == 0
        result["messages"] = messages
        return result

    def validate_all(self, results: list) -> list:
        """Validate all test results."""
        return [self.validate(r) for r in results]