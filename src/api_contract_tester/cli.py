"""CLI entry point for API Contract Tester."""

import os
import sys

import click

from .spec_loader import SpecLoader
from .test_generator import TestGenerator
from .runner import TestRunner
from .validator import ResponseValidator
from .reporter import Reporter


def _load_config():
    """Load .act.toml from current directory if it exists."""
    config = {}
    for path in (".act.toml", "act.toml"):
        if os.path.exists(path):
            try:
                import tomllib
            except ImportError:
                import tomli as tomllib
            with open(path, "rb") as f:
                data = tomllib.load(f)
                cfg = data.get("act", data)
                for key in ("base_url", "timeout", "concurrency", "retry",
                           "retry_delay", "no_ssl", "max_response_time"):
                    if key in cfg:
                        config[key] = cfg[key]
                if "headers" in cfg:
                    config["headers"] = cfg["headers"]
            break
    return config


@click.command()
@click.argument("spec_file", type=click.Path(exists=True))
@click.option("--base-url", "-b", default=None, help="Override API base URL")
@click.option("--timeout", "-t", default=None, type=int, help="Request timeout in seconds")
@click.option("--concurrency", "-c", default=None, type=int, help="Number of concurrent workers")
@click.option("--retry", "-r", default=None, type=int, help="Retry count on failure")
@click.option("--retry-delay", default=None, type=float, help="Seconds between retries")
@click.option("--no-ssl", is_flag=True, default=None, help="Disable SSL verification")
@click.option("--max-response-time", default=None, type=int, help="Max acceptable response time in ms")
@click.option("--header", "-H", multiple=True, help="Extra header (key:value)")
@click.option("--json-report", "-j", is_flag=True, help="Output JSON report")
@click.option("--html-report", is_flag=True, help="Output HTML report")
@click.option("--md-report", is_flag=True, help="Output Markdown report")
@click.option("--dry-run", is_flag=True, help="Show test cases without executing")
@click.option("--output", "-o", default=None, help="Save report to file")
def main(spec_file, base_url, timeout, concurrency, retry, retry_delay,
         no_ssl, max_response_time, header, json_report, html_report, md_report,
         dry_run, output):
    """Test an API against its OpenAPI specification.

    SPEC_FILE: Path to OpenAPI 3.x spec file (YAML or JSON).

    Reads .act.toml for default options. CLI flags override config.

    \b
    Examples:
      act openapi.yaml
      act openapi.yaml -c 5 --dry-run
      act openapi.yaml --md-report -o REPORT.md
    """
    # Load config file
    cfg = _load_config()
    timeout = timeout if timeout is not None else cfg.get("timeout", 10)
    concurrency = concurrency if concurrency is not None else cfg.get("concurrency", 1)
    retry = retry if retry is not None else cfg.get("retry", 0)
    retry_delay = retry_delay if retry_delay is not None else cfg.get("retry_delay", 1.0)
    no_ssl = no_ssl if no_ssl is not False else cfg.get("no_ssl", False)
    max_response_time = max_response_time if max_response_time is not None else cfg.get("max_response_time")
    if base_url is None:
        base_url = cfg.get("base_url")

    # Parse custom headers (CLI overrides config)
    custom_headers = {}
    config_headers = cfg.get("headers", {})
    if isinstance(config_headers, dict):
        custom_headers.update(config_headers)
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

    api_base_url = base_url or loader.get_base_url()
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

    if no_ssl:
        for tc in test_cases:
            tc.verify_ssl = False

    click.echo("[TESTS] Generated " + str(len(test_cases)) + " test cases")

    # --- Dry run: just print what would be tested ---
    if dry_run:
        click.echo("\n[Dry Run] The following endpoints would be tested:\n")
        for tc in test_cases:
            body_str = " (with body)" if tc.body else ""
            ssl_str = " [no-ssl]" if not tc.verify_ssl else ""
            click.echo(f"  {tc.method:6s} {tc.path}{body_str}{ssl_str}")
        click.echo(f"\n[Dry Run] {len(test_cases)} test cases, 0 executed.")
        return

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
    validator = ResponseValidator(max_response_time_ms=max_response_time)
    results = validator.validate_all(results)

    # 5. Report
    reporter = Reporter()
    if html_report:
        report = reporter.html_report(results)
    elif json_report:
        report = reporter.json_report(results)
    elif md_report:
        report = reporter.markdown_report(results)
    else:
        report = reporter.console_report(results)

    click.echo(report if not html_report else "[OK] HTML report generated")

    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(report)
        click.echo("\n[FILE] Report saved to: " + output)

    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed
    click.echo("\n[SUMMARY] " + str(total) + " tests | " +
               str(passed) + " passed | " + str(failed) + " failed")

    sys.exit(0 if failed == 0 else 1)


if __name__ == "__main__":
    main()