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
@click.option("--concurrency", "-c", default=1, help="Number of concurrent workers")
@click.option("--retry", "-r", default=0, help="Retry count on failure")
@click.option("--retry-delay", default=1.0, help="Seconds between retries")
@click.option("--no-ssl", is_flag=True, help="Disable SSL verification")
@click.option("--header", "-H", multiple=True, help="Extra header (key:value)")
@click.option("--json-report", "-j", is_flag=True, help="Output JSON report")
@click.option("--html-report", is_flag=True, help="Output HTML report")
@click.option("--output", "-o", default=None, help="Save report to file")
def main(spec_file, base_url, timeout, concurrency, retry, retry_delay,
         no_ssl, header, json_report, html_report, output):
    """Test an API against its OpenAPI specification.

    SPEC_FILE: Path to OpenAPI 3.x spec file (YAML or JSON).

    Supports $VAR and ${VAR} environment variable substitution in specs.

    \b
    Examples:
      act openapi.yaml
      act openapi.yaml -c 5 --retry 2 --no-ssl
      act openapi.yaml -H "Authorization:Bearer $TOKEN" --html-report -o report.html
    """
    # Parse custom headers
    custom_headers = {}
    for h in header:
        if ":" in h:
            key, val = h.split(":", 1)
            custom_headers[key.strip()] = val.strip()

    # 1. Load spec
    click.echo("[SPEC] Loading: " + spec_file)
    try:
        loader = SpecLoader(spec_file)
    except Exception as e:
        click.echo("[ERROR] Failed to load spec: " + str(e))
        sys.exit(1)

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
    if not endpoints:
        click.echo("[ERROR] No endpoints found in spec.")
        sys.exit(1)

    click.echo("[ENDPOINTS] Found " + str(len(endpoints)))
    generator = TestGenerator(api_base_url, endpoints, default_headers=custom_headers)
    test_cases = generator.generate()

    # Apply --no-ssl to all test cases
    if no_ssl:
        for tc in test_cases:
            tc.verify_ssl = False

    click.echo("[TESTS] Generated " + str(len(test_cases)) + " test cases")

    # 3. Run tests
    click.echo("\n[RUN] Executing tests...")
    if concurrency > 1:
        click.echo("[RUN] Using " + str(concurrency) + " concurrent workers")
    click.echo("")

    runner = TestRunner(timeout=timeout, retries=retry, retry_delay=retry_delay)

    if concurrency > 1:
        results = runner.run_all_concurrent(test_cases, workers=concurrency)
    else:
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

    # Summary line
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    click.echo("\n[SUMMARY] " + str(total) + " tests | " +
               str(passed) + " passed | " + str(failed) + " failed")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()