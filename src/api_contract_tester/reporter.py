"""Generate test reports in various formats."""

import json
from datetime import datetime


class Reporter:
    """Generates test reports from validation results."""

    def console_report(self, results: list) -> str:
        """Generate a colorful console report."""
        total = len(results)
        passed = sum(1 for r in results if r["passed"])
        failed = total - passed
        total_time = sum(r.get("response_time_ms", 0) for r in results)

        lines = []
        lines.append("")
        lines.append("=" * 60)
        lines.append("  API Contract Test Report")
        lines.append("=" * 60)
        lines.append(f"  Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"  Total: {total} | PASS: {passed} | FAIL: {failed}")
        lines.append(f"  Total response time: {total_time}ms")
        lines.append("-" * 60)

        for r in results:
            tc = r["test_case"]
            status_icon = "PASS" if r["passed"] else "FAIL"
            lines.append(f"\n  [{status_icon}] {tc.method} {tc.path}")
            for msg in r.get("messages", []):
                lines.append(f"     {msg}")

        lines.append("")
        lines.append("=" * 60)

        return "\n".join(lines)

    def json_report(self, results: list) -> str:
        """Generate a JSON report."""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total": len(results),
                "passed": sum(1 for r in results if r["passed"]),
                "failed": sum(1 for r in results if not r["passed"]),
            },
            "results": [
                {
                    "name": r["test_case"].name,
                    "method": r["test_case"].method,
                    "path": r["test_case"].path,
                    "passed": r["passed"],
                    "status_code": r.get("status_code"),
                    "response_time_ms": r.get("response_time_ms"),
                    "messages": r.get("messages", []),
                }
                for r in results
            ],
        }
        return json.dumps(report, indent=2, ensure_ascii=False)