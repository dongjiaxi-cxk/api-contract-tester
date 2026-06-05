"""Tests for v0.3.0 features: env vars, concurrency, retry, headers, SSL."""

import os
import pytest
from api_contract_tester.test_generator import (
    TestCase, resolve_env, resolve_env_in_dict, TestGenerator
)
from api_contract_tester.runner import TestRunner


class TestEnvVarResolution:
    def test_resolve_simple_var(self):
        os.environ["ACT_TEST_VAR"] = "hello"
        assert resolve_env("$ACT_TEST_VAR") == "hello"
        assert resolve_env("${ACT_TEST_VAR}") == "hello"

    def test_resolve_missing_var(self):
        assert resolve_env("$NONEXISTENT_VAR_XYZ") == ""

    def test_resolve_in_string(self):
        os.environ["ACT_HOST"] = "api.example.com"
        result = resolve_env("https://${ACT_HOST}/v1")
        assert result == "https://api.example.com/v1"

    def test_resolve_in_dict(self):
        os.environ["ACT_KEY"] = "secret123"
        data = {"url": "https://host/${ACT_KEY}", "nested": {"key": "$ACT_KEY"}}
        result = resolve_env_in_dict(data)
        assert result["url"] == "https://host/secret123"
        assert result["nested"]["key"] == "secret123"


class TestConcurrentExecution:
    def test_run_all_concurrent(self):
        cases = [
            TestCase(name=f"test_{i}", method="GET", path="/",
                     base_url="http://localhost:19999")
            for i in range(5)
        ]
        runner = TestRunner(timeout=1)
        results = runner.run_all_concurrent(cases, workers=3)
        assert len(results) == 5
        for r in results:
            assert r["error"] is not None  # all fail (no server)

    def test_concurrent_order_preserved(self):
        cases = [
            TestCase(name=f"tc_{i}", method="GET", path=f"/{i}",
                     base_url="http://localhost:19999")
            for i in range(3)
        ]
        runner = TestRunner(timeout=1)
        results = runner.run_all_concurrent(cases, workers=2)
        for i, r in enumerate(results):
            assert r["test_case"].name == f"tc_{i}"


class TestRetry:
    def test_retry_on_failure(self):
        case = TestCase(name="retry_test", method="GET", path="/",
                        base_url="http://localhost:19999")
        runner = TestRunner(timeout=1, retries=2, retry_delay=0.1)
        result = runner.run(case)
        assert result["error"] is not None

    def test_no_retry_on_zero(self):
        case = TestCase(name="no_retry", method="GET", path="/",
                        base_url="http://localhost:19999")
        runner = TestRunner(timeout=1, retries=0)
        result = runner.run(case)
        assert result["error"] is not None


class TestVerifySSL:
    def test_verify_ssl_default_true(self):
        case = TestCase(name="ssl", method="GET", path="/",
                        base_url="http://localhost:19999")
        assert case.verify_ssl is True

    def test_verify_ssl_false(self):
        case = TestCase(name="ssl", method="GET", path="/",
                        base_url="http://localhost:19999", verify_ssl=False)
        assert case.verify_ssl is False


class TestCustomHeaders:
    def test_generator_accepts_default_headers(self):
        gen = TestGenerator("http://localhost", [], {"Authorization": "Bearer xxx"})
        cases = gen.generate()
        assert len(cases) == 0

    def test_generated_case_has_headers(self):
        endpoints = [{
            "method": "GET", "path": "/test",
            "operation_id": "testOp",
            "parameters": [], "responses": {"200": {"description": "ok"}},
        }]
        gen = TestGenerator("http://localhost", endpoints,
                            {"X-API-Key": "secret"})
        cases = gen.generate()
        assert cases[0].headers == {"X-API-Key": "secret"}