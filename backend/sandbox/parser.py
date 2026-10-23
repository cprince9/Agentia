import re
import json
from typing import List, Optional
import structlog
from ..graph.state import TestResults, TestError

logger = structlog.get_logger(__name__)


def parse_coverage(stdout: str) -> float:
    """
    Extract pytest-cov percentage from stdout (e.g. 'TOTAL ... 88%').
    """
    if not stdout:
        return 0.0

    # Pattern 1: pytest-cov table: "TOTAL   100   12   88%"
    match = re.search(r"TOTAL\s+\d+\s+\d+\s+(\d+)%", stdout)
    if match:
        return float(match.group(1))

    # Pattern 2: Coverage summary line
    match = re.search(r"coverage:\s*(\d+(?:\.\d+)?)%", stdout, re.IGNORECASE)
    if match:
        return float(match.group(1))

    return 0.0


def parse_pytest_output(stdout: str, stderr: str) -> TestResults:
    """
    Parse test execution stdout and stderr into structured TestResults.
    Attempts JSON report decoding first, falling back to regex text parsing.
    """
    raw_combined = f"{stdout}\n{stderr}".strip()
    passed = 0
    failed = 0
    errors: List[TestError] = []

    # 1. Try to extract JSON report if emitted (e.g. pytest-json-report or embedded JSON)
    json_match = re.search(r"\{[\s\S]*\"summary\":\s*\{[\s\S]*\}[\s\S]*\}", stdout)
    if json_match:
        try:
            report_data = json.loads(json_match.group(0))
            summary = report_data.get("summary", {})
            passed = summary.get("passed", 0)
            failed = summary.get("failed", 0) + summary.get("error", 0)

            # Parse tests array
            for test in report_data.get("tests", []):
                outcome = test.get("outcome")
                if outcome in ("failed", "error"):
                    nodeid = test.get("nodeid", "unknown_test")
                    call_info = test.get("call", {})
                    tb = call_info.get("traceback", "")
                    msg = call_info.get("crash", {}).get("message", "Test assertion or runtime error")
                    file_path = call_info.get("crash", {}).get("path", "")
                    line_num = call_info.get("crash", {}).get("lineno", 0)

                    errors.append(
                        TestError(
                            test_name=nodeid,
                            error=msg,
                            traceback=tb if isinstance(tb, str) else json.dumps(tb),
                            file=file_path,
                            line=line_num or 0,
                        )
                    )

            coverage = parse_coverage(stdout)
            all_passed = (failed == 0 and passed > 0)
            return TestResults(
                passed=passed,
                failed=failed,
                errors=errors,
                coverage_percent=coverage,
                all_passed=all_passed,
                raw_output=raw_combined,
            )
        except Exception as e:
            logger.debug("json_report_parse_failed_falling_back_to_regex", error=str(e))

    # 2. Text regex parsing
    # Extract passed count
    passed_match = re.search(r"(\d+)\s+passed", raw_combined)
    if passed_match:
        passed = int(passed_match.group(1))

    # Extract failed count
    failed_match = re.search(r"(\d+)\s+failed", raw_combined)
    if failed_match:
        failed += int(failed_match.group(1))

    # Extract errors count
    error_match = re.search(r"(\d+)\s+errors?", raw_combined)
    if error_match:
        failed += int(error_match.group(1))

    # Extract individual FAILURES blocks
    failure_blocks = re.split(r"_{10,}\s+([^\n_]+)\s+_{10,}", raw_combined)
    if len(failure_blocks) > 1:
        # Alternating test names and tracebacks
        for i in range(1, len(failure_blocks), 2):
            test_name = failure_blocks[i].strip()
            tb = failure_blocks[i + 1] if i + 1 < len(failure_blocks) else ""

            # Attempt to locate file and line
            file_match = re.search(r'File "([^"]+)", line (\d+)', tb)
            file_name = file_match.group(1) if file_match else ""
            line_no = int(file_match.group(2)) if file_match else 0

            # Find exception message
            err_line_match = re.search(r"([A-Za-z0-9_]+Error:.*|AssertionError.*)", tb)
            err_msg = err_line_match.group(1).strip() if err_line_match else "Test failure"

            errors.append(
                TestError(
                    test_name=test_name,
                    error=err_msg,
                    traceback=tb.strip(),
                    file=file_name,
                    line=line_no,
                )
            )

    # In case no passed or failed was found, but syntax error or exception in stderr
    if passed == 0 and failed == 0 and stderr:
        syntax_err = re.search(r"(SyntaxError|ImportError|ModuleNotFoundError|NameError):.*", stderr)
        if syntax_err:
            failed = 1
            errors.append(
                TestError(
                    test_name="compilation_or_import",
                    error=syntax_err.group(0),
                    traceback=stderr,
                    file="module",
                    line=1,
                )
            )

    coverage = parse_coverage(stdout)
    all_passed = (failed == 0 and passed > 0)

    return TestResults(
        passed=passed,
        failed=failed,
        errors=errors,
        coverage_percent=coverage,
        all_passed=all_passed,
        raw_output=raw_combined,
    )
