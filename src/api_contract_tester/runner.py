"""Execute HTTP requests for test cases with concurrency support."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import requests

from .test_generator import TestCase


class TestRunner:
    """Runs test cases against a live API."""

    def __init__(self, timeout: int = 10, retries: int = 0, retry_delay: float = 1.0) -> None:
        self.timeout: int = timeout
        self.retries: int = retries
        self.retry_delay: float = retry_delay

    def run(self, test_case: TestCase) -> dict[str, Any]:
        """Execute a single test case, with optional retries on failure."""
        last_result: dict[str, Any] = {}
        for attempt in range(self.retries + 1):
            result: dict[str, Any] = self._run_once(test_case)
            if result.get("error") is None:
                return result
            last_result = result
            if attempt < self.retries:
                time.sleep(self.retry_delay)
        return last_result

    def _run_once(self, test_case: TestCase) -> dict[str, Any]:
        """Execute a single HTTP request."""
        path: str = test_case.path
        for key, value in test_case.path_params.items():
            path = path.replace("{" + key + "}", str(value))

        url: str = test_case.base_url + path
        result: dict[str, Any] = {
            "test_case": test_case,
            "passed": False,
            "status_code": None,
            "response_time_ms": 0,
            "error": None,
        }

        try:
            response: requests.Response = requests.request(
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

    def run_all(self, test_cases: list[TestCase]) -> list[dict[str, Any]]:
        """Run all test cases sequentially."""
        return [self.run(tc) for tc in test_cases]

    def run_all_concurrent(self, test_cases: list[TestCase], workers: int = 5) -> list[dict[str, Any]]:
        """Run all test cases concurrently with ThreadPoolExecutor."""
        results_map: dict[int, dict[str, Any]] = {}

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures: dict = {executor.submit(self.run, tc): i for i, tc in enumerate(test_cases)}
            for future in as_completed(futures):
                idx: int = futures[future]
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
