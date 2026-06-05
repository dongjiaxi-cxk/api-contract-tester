"""Execute HTTP requests for test cases."""

import requests
from .test_generator import TestCase


class TestRunner:
    """Runs test cases against a live API."""

    def __init__(self, timeout: int = 10):
        self.timeout = timeout

    def run(self, test_case: TestCase) -> dict:
        """Execute a single test case and return the result."""
        # Replace path parameters like {petId} with actual values
        path = test_case.path
        for key, value in test_case.path_params.items():
            path = path.replace("{" + key + "}", str(value))

        url = test_case.base_url + path
        result = {
            "test_case": test_case,
            "passed": False,
            "status_code": None,
            "response_time_ms": 0,
            "error": None,
        }

        try:
            response = requests.request(
                method=test_case.method,
                url=url,
                params=test_case.params,
                json=test_case.body,
                headers=test_case.headers,
                timeout=self.timeout,
            )
            result["status_code"] = response.status_code
            result["response_time_ms"] = round(response.elapsed.total_seconds() * 1000)
            result["response"] = response

        except requests.exceptions.Timeout:
            result["error"] = "Request timed out"
        except requests.exceptions.ConnectionError:
            result["error"] = "Connection failed"
        except requests.exceptions.RequestException as e:
            result["error"] = str(e)

        return result

    def run_all(self, test_cases: list) -> list:
        """Run all test cases and return results."""
        return [self.run(tc) for tc in test_cases]