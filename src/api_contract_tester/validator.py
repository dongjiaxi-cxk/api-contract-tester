"""Validate API responses against expected contracts."""


class ResponseValidator:
    """Validates API response against test expectations."""

    def validate(self, result: dict) -> dict:
        """Validate a test result and mark it passed/failed.

        Returns the result dict with 'passed' and 'messages' fields added.
        """
        messages = []
        test_case = result["test_case"]

        # Check for connection/network errors
        if result["error"]:
            messages.append(f"[FAIL] Error: {result['error']}")
            result["passed"] = False
            result["messages"] = messages
            return result

        status = result["status_code"]
        expected = test_case.expected_status

        # Validate status code
        if status == expected:
            messages.append(f"[PASS] Status: {status} (expected {expected})")
        else:
            messages.append(f"[FAIL] Status: {status} (expected {expected})")

        # Validate response time (warn if > 2 seconds)
        if result["response_time_ms"] > 2000:
            messages.append(f"[WARN] Slow response: {result['response_time_ms']}ms")
        else:
            messages.append(f"[PASS] Response time: {result['response_time_ms']}ms")

        # Validate Content-Type if expected
        response = result.get("response")
        if response is not None and test_case.expected_content_type:
            content_type = response.headers.get("Content-Type", "")
            if test_case.expected_content_type in content_type:
                messages.append(f"[PASS] Content-Type: {content_type}")
            else:
                messages.append(
                    f"[FAIL] Content-Type: {content_type} (expected {test_case.expected_content_type})"
                )

        result["passed"] = status == expected
        result["messages"] = messages
        return result

    def validate_all(self, results: list) -> list:
        """Validate all test results."""
        return [self.validate(r) for r in results]