"""Execute HTTP requests for test cases with concurrency support."""

import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from .test_generator import TestCase


class TestRunner:
    """Runs test cases against a live API."""

    def __init__(self, timeout: int = 10, retries: int = 0, retry_delay: float = 1.0):
        self.timeout = timeout
        self.retries = retries
        self.retry_delay = retry_delay

    def run(self, test_case: TestCase) -> dict:
        """Execute a single test case, with optional retries on failure."""
        last_result = None
        for attempt in range(self.retries + 1):
            result = self._run_once(test_case)
            if result.get("error") is None:
                return result
            last_result = result
            if attempt < self.retries:
                import time
                time.sleep(self.retry_delay)
        return last_result

    def _run_once(self, test_case: TestCase) -> dict:
        """Execute a single HTTP request."""
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
                verify=test_case.verify_ssl,
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
        """Run all test cases sequentially."""
        return [self.run(tc) for tc in test_cases]

    def run_all_concurrent(self, test_cases: list, workers: int = 5) -> list:
        """Run all test cases concurrently with ThreadPoolExecutor.

        Args:
            test_cases: List of TestCase objects.
            workers: Number of concurrent workers (default 5).

        Returns:
            List of result dicts in the same order as test_cases.
        """
        results_map = {}

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {executor.submit(self.run, tc): i for i, tc in enumerate(test_cases)}
            for future in as_completed(futures):
                idx = futures[future]
                try:
                    results_map[idx] = future.result()
                except Exception as e:
                    results_map[idx] = {
                        "test_case": test_cases[idx],
                        "passed": False,
                        "status_code": None,
                        "response_time_ms": 0,
                        "error": str(e),
                    }

        return [results_map[i] for i in range(len(test_cases))]