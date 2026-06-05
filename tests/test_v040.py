"""Tests for v0.4.0: dry-run, markdown report, max-response-time, config."""

import os, tempfile, subprocess, sys
from pathlib import Path
from api_contract_tester.validator import ResponseValidator
from api_contract_tester.reporter import Reporter
from api_contract_tester.test_generator import TestCase


class TestMaxResponseTime:
    def test_pass_within_threshold(self):
        v = ResponseValidator(max_response_time_ms=500)
        case = TestCase(name="t", method="GET", path="/", base_url="http://x")
        result = {"test_case": case, "passed": False, "status_code": 200,
                  "response_time_ms": 100, "error": None, "response": _fake_response(200)}
        v.validate(result)
        assert result["passed"] is True

    def test_fail_exceeds_threshold(self):
        v = ResponseValidator(max_response_time_ms=200)
        case = TestCase(name="t", method="GET", path="/", base_url="http://x")
        result = {"test_case": case, "passed": False, "status_code": 200,
                  "response_time_ms": 500, "error": None, "response": _fake_response(200)}
        v.validate(result)
        assert result["passed"] is False
        assert any("threshold" in m for m in result["messages"])

    def test_no_threshold_just_warns(self):
        v = ResponseValidator(max_response_time_ms=None)
        case = TestCase(name="t", method="GET", path="/", base_url="http://x")
        result = {"test_case": case, "passed": False, "status_code": 200,
                  "response_time_ms": 3000, "error": None, "response": _fake_response(200)}
        v.validate(result)
        assert any("WARN" in m for m in result["messages"])
        # No threshold set, so slow is just a warning, test still passes on status
        assert result["passed"] is True


def _fake_response(status=200):
    class FakeResp:
        status_code = status
        headers = {"Content-Type": "application/json"}
        elapsed = type("e", (), {"total_seconds": lambda: 0.1})()
        def json(self):
            return {}
    return FakeResp()


class TestMarkdownReport:
    def test_generates_markdown(self):
        v = ResponseValidator()
        case = TestCase(name="getUsers", method="GET", path="/users", base_url="http://x")
        result = {"test_case": case, "passed": True, "status_code": 200,
                  "response_time_ms": 50, "error": None, "response": _fake_response(200),
                  "messages": ["[PASS] Status: 200 (expected 200)"]}
        v.validate(result)
        
        r = Reporter()
        md = r.markdown_report([result])
        assert "# API Contract Test Report" in md
        assert "GET" in md
        assert "/users" in md
        assert "PASS" in md
        assert "|" in md  # markdown table

    def test_json_report_still_works(self):
        case = TestCase(name="t", method="GET", path="/", base_url="http://x")
        result = {"test_case": case, "passed": True, "status_code": 200,
                  "response_time_ms": 10, "error": None,
                  "messages": []}
        r = Reporter()
        j = r.json_report([result])
        assert '"total": 1' in j


class TestDryRun:
    def test_dry_run_flag(self):
        import tempfile
        tmp_path = Path(tempfile.mkdtemp())
        spec = tmp_path / "api.yaml"
        spec.write_text("""\
openapi: "3.0.0"
info:
  title: Test
  version: "1.0"
servers:
  - url: http://localhost:9999
paths:
  /items:
    get:
      operationId: getItems
      responses:
        "200":
          description: ok
""", encoding="utf-8")

        result = subprocess.run(
            [sys.executable, "-m", "api_contract_tester.cli", str(spec), "--dry-run"],
            capture_output=True, text=True, cwd=str(tmp_path),
        )
        assert "Dry Run" in result.stdout
        assert "GET" in result.stdout
        assert "/items" in result.stdout
        assert "0 executed" in result.stdout
        import shutil; shutil.rmtree(str(tmp_path), ignore_errors=True)


class TestConfigFile:
    def test_config_loads(self):
        import os, tempfile
        tmp = tempfile.mkdtemp()
        orig = os.getcwd()
        os.chdir(tmp)
        cfg = Path(tmp) / ".act.toml"
        cfg.write_text("""\
[act]
base_url = "http://config-url.com"
timeout = 30
concurrency = 4
""", encoding="utf-8")

        from api_contract_tester.cli import _load_config
        config = _load_config()
        assert config["base_url"] == "http://config-url.com"
        assert config["timeout"] == 30
        assert config["concurrency"] == 4
        os.chdir(orig)
        import shutil; shutil.rmtree(tmp, ignore_errors=True)