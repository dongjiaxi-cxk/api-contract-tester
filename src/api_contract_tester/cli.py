"""CLI entry point for API Contract Tester."""

import sys

import click

from .spec_loader import SpecLoader
from .test_generator import TestGenerator
from .runner import TestRunner
from .validator import ResponseValidator
from .reporter import Reporter


@click.command()
@click.argument("spec_file", type=click.Path(exists=True))
@click.option("--base-url", "-b", default=None, help="Override API base URL")
@click.option("--timeout", "-t", default=10, help="Request timeout in seconds")
@click.option("--json-report", "-j", is_flag=True, help="Output JSON report")
@click.option("--html-report", is_flag=True, help="Output HTML report")
@click.option("--output", "-o", default=None, help="Save report to file")
def main(spec_file, base_url, timeout, json_report, html_report, output):
    """Test an API against its OpenAPI specification.

    SPEC_FILE: Path to OpenAPI 3.x spec file (YAML or JSON).
    """
    # 1. Load spec
    click.echo("[SPEC] Loading: " + spec_file)
    loader = SpecLoader(spec_file)
    if base_url:
        api_base_url = base_url
    else:
        api_base_url = loader.get_base_url()

    if not api_base_url:
        click.echo("[ERROR] No base URL found. Use --base-url or add servers to spec.")
        sys.exit(1)

    click.echo("[URL] " + api_base_url)

    # 2. Generate test cases
    endpoints = loader.get_endpoints()
    click.echo("[ENDPOINTS] Found " + str(len(endpoints)))
    generator = TestGenerator(api_base_url, endpoints)
    test_cases = generator.generate()
    click.echo("[TESTS] Generated " + str(len(test_cases)) + " test cases")

    # 3. Run tests
    click.echo("\n[RUN] Executing tests...\n")
    runner = TestRunner(timeout=timeout)
    results = runner.run_all(test_cases)

    # 4. Validate
    validator = ResponseValidator()
    results = validator.validate_all(results)

    # 5. Report
    reporter = Reporter()

    if html_report:
        report = reporter.html_report(results)
    elif json_report:
        report = reporter.json_report(results)
    else:
        report = reporter.console_report(results)

    click.echo(report if not html_report else "[OK] HTML report generated")

    # Save to file
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(report)
        click.echo("\n[FILE] Report saved to: " + output)

    # Exit code
    failed = sum(1 for r in results if not r["passed"])
    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()