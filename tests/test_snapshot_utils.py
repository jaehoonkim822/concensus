import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(__file__))
from snapshot_utils import validate_schema, save_run_log

BASELINES_DIR = os.path.join(os.path.dirname(__file__), "snapshots", "baselines")
RUNS_DIR = os.path.join(os.path.dirname(__file__), "snapshots", "runs")


def test_validate_schema_passes_for_valid_trigger_output():
    output = {
        "systemMessage": (
            "[CONSENSUS REVIEW]\n"
            "  ⟐ Queried: gemini, codex\n"
            "  ⟐ Responses: gemini ✓, codex ✓\n"
            "  ⟐ Round 0 → full consensus\n"
            "\n"
            "Result: FULL_CONSENSUS (round 0)\n"
            "  Approve: claude, codex, gemini\n"
            "  → All models agree. Proceed as-is."
        )
    }
    result = validate_schema(output, "posttooluse_trigger")
    assert result["passed"] is True
    assert all(v is True for v in result["check_results"].values())


def test_validate_schema_fails_missing_required_key():
    output = {"other_key": "value"}
    result = validate_schema(output, "posttooluse_trigger")
    assert result["passed"] is False


def test_validate_schema_fails_missing_pattern():
    output = {"systemMessage": "some random text without expected patterns"}
    result = validate_schema(output, "posttooluse_trigger")
    assert result["passed"] is False


def test_validate_schema_passes_for_empty_skip():
    output = {}
    result = validate_schema(output, "posttooluse_skip")
    assert result["passed"] is True


def test_validate_schema_fails_nonempty_for_skip():
    output = {"systemMessage": "unexpected"}
    result = validate_schema(output, "posttooluse_skip")
    assert result["passed"] is False


def test_validate_schema_stop_detect():
    output = {
        "systemMessage": (
            "[CONSENSUS RECOMMENDED] This response contains an architectural/design decision. "
            "Before proceeding, consider cross-validating this decision with other models. "
            "Key context: I recommend we use microservices"
        )
    }
    result = validate_schema(output, "stop_detect")
    assert result["passed"] is True


def test_validate_schema_stop_ignore():
    output = {}
    result = validate_schema(output, "stop_ignore")
    assert result["passed"] is True


def test_save_run_log_creates_file():
    log_path = save_run_log(
        test_name="test_example",
        input_data={"tool_name": "Write"},
        output={"systemMessage": "test"},
        exit_code=0,
        duration_ms=100,
        schema_result={"passed": True, "check_results": {}},
    )
    assert os.path.exists(log_path)
    with open(log_path) as f:
        log = json.load(f)
    assert log["test_name"] == "test_example"
    assert log["exit_code"] == 0
    assert log["duration_ms"] == 100
    assert log["schema_validation"] == "PASS"
    assert "timestamp" in log
    os.remove(log_path)
