import os
import re
import json
import time
from datetime import datetime, timezone

SNAPSHOTS_DIR = os.path.join(os.path.dirname(__file__), "snapshots")
BASELINES_DIR = os.path.join(SNAPSHOTS_DIR, "baselines")
RUNS_DIR = os.path.join(SNAPSHOTS_DIR, "runs")


def validate_schema(output: dict, schema_name: str) -> dict:
    """Validate hook output against a baseline schema.

    Args:
        output: The hook output dictionary to validate.
        schema_name: Name of the schema file (without .schema.json extension).

    Returns:
        Dictionary with 'passed' (bool) and 'check_results' (dict of check name to bool).
    """
    schema_path = os.path.join(BASELINES_DIR, f"{schema_name}.schema.json")
    with open(schema_path) as f:
        schema = json.load(f)

    check_results = {}
    passed = True

    if schema.get("expect_empty", False):
        is_empty = output == {}
        check_results["is_empty"] = is_empty
        if not is_empty:
            passed = False
        return {"passed": passed, "check_results": check_results}

    for key in schema.get("required_keys", []):
        present = key in output
        check_results[f"required_key_{key}"] = present
        if not present:
            passed = False

    text = json.dumps(output)
    for name, pattern in schema.get("pattern_checks", {}).items():
        matched = bool(re.search(pattern, text))
        check_results[name] = matched
        if not matched:
            passed = False

    return {"passed": passed, "check_results": check_results}


def save_run_log(
    test_name: str,
    input_data: dict,
    output: dict,
    exit_code: int,
    duration_ms: int,
    schema_result: dict,
) -> str:
    """Save a test run log to the snapshots/runs directory.

    Args:
        test_name: Name of the test that produced this run.
        input_data: The input data passed to the hook.
        output: The hook output dictionary.
        exit_code: Process exit code (0 for success).
        duration_ms: Duration of the hook invocation in milliseconds.
        schema_result: Result from validate_schema().

    Returns:
        Absolute path to the saved log file.
    """
    os.makedirs(RUNS_DIR, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H-%M-%S")
    filename = f"{timestamp}_{test_name}.json"
    log_path = os.path.join(RUNS_DIR, filename)

    log_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "test_name": test_name,
        "input": input_data,
        "output": output,
        "exit_code": exit_code,
        "duration_ms": duration_ms,
        "schema_validation": "PASS" if schema_result["passed"] else "FAIL",
        "check_results": schema_result.get("check_results", {}),
    }

    with open(log_path, "w") as f:
        json.dump(log_entry, f, indent=2, ensure_ascii=False)

    return log_path
