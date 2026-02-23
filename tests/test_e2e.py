import os
import sys
import json
import time
import subprocess
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugin"))
PLUGIN_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugin")


def _run_hook(hook_name, input_data, timeout=120):
    start = time.monotonic()
    proc = subprocess.run(
        ["python3", os.path.join(PLUGIN_ROOT, "hooks", hook_name)],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        timeout=timeout,
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": PLUGIN_ROOT},
    )
    duration_ms = int((time.monotonic() - start) * 1000)
    output = json.loads(proc.stdout) if proc.stdout.strip() else {}
    return output, proc.returncode, duration_ms


def test_posttooluse_hook_triggers(snapshot_e2e):
    input_data = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {
            "file_path": "/tmp/test_consensus.py",
            "content": "\n".join([f"line_{i} = {i}" for i in range(10)]),
        },
    }
    output, exit_code, duration_ms = _run_hook("posttooluse.py", input_data)
    assert exit_code == 0
    snapshot_e2e.validate(
        test_name="test_posttooluse_hook_triggers",
        schema_name="posttooluse_trigger",
        input_data=input_data,
        output=output,
        exit_code=exit_code,
        duration_ms=duration_ms,
    )


def test_posttooluse_hook_skips_markdown(snapshot_e2e):
    input_data = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {
            "file_path": "/tmp/README.md",
            "content": "a\nb\nc\nd\ne\nf\ng\nh\ni\nj\n",
        },
    }
    output, exit_code, duration_ms = _run_hook("posttooluse.py", input_data, timeout=10)
    assert exit_code == 0
    snapshot_e2e.validate(
        test_name="test_posttooluse_hook_skips_markdown",
        schema_name="posttooluse_skip",
        input_data=input_data,
        output=output,
        exit_code=exit_code,
        duration_ms=duration_ms,
    )


def test_stop_hook_detects_design(snapshot_e2e):
    input_data = {
        "hook_event_name": "Stop",
        "reason": "I recommend we use a microservices architecture with Redis for caching and PostgreSQL for persistence.",
    }
    output, exit_code, duration_ms = _run_hook("stop.py", input_data, timeout=10)
    assert exit_code == 0
    snapshot_e2e.validate(
        test_name="test_stop_hook_detects_design",
        schema_name="stop_detect",
        input_data=input_data,
        output=output,
        exit_code=exit_code,
        duration_ms=duration_ms,
    )


def test_stop_hook_ignores_simple(snapshot_e2e):
    input_data = {"hook_event_name": "Stop", "reason": "Done."}
    output, exit_code, duration_ms = _run_hook("stop.py", input_data, timeout=10)
    assert exit_code == 0
    snapshot_e2e.validate(
        test_name="test_stop_hook_ignores_simple",
        schema_name="stop_ignore",
        input_data=input_data,
        output=output,
        exit_code=exit_code,
        duration_ms=duration_ms,
    )
