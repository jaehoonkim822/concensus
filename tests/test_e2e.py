import os
import sys
import json
import subprocess
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
PLUGIN_ROOT = os.path.dirname(os.path.dirname(__file__))


def test_posttooluse_hook_triggers():
    input_data = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {
            "file_path": "/tmp/test_consensus.py",
            "content": "\n".join([f"line_{i} = {i}" for i in range(10)]),
        },
    }
    proc = subprocess.run(
        ["python3", os.path.join(PLUGIN_ROOT, "hooks", "posttooluse.py")],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        timeout=120,
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": PLUGIN_ROOT},
    )
    assert proc.returncode == 0
    output = json.loads(proc.stdout)
    assert isinstance(output, dict)


def test_posttooluse_hook_skips_markdown():
    input_data = {
        "hook_event_name": "PostToolUse",
        "tool_name": "Write",
        "tool_input": {
            "file_path": "/tmp/README.md",
            "content": "a\nb\nc\nd\ne\nf\ng\nh\ni\nj\n",
        },
    }
    proc = subprocess.run(
        ["python3", os.path.join(PLUGIN_ROOT, "hooks", "posttooluse.py")],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": PLUGIN_ROOT},
    )
    assert proc.returncode == 0
    output = json.loads(proc.stdout)
    assert output == {}


def test_stop_hook_detects_design():
    input_data = {
        "hook_event_name": "Stop",
        "reason": "I recommend we use a microservices architecture with Redis for caching and PostgreSQL for persistence.",
    }
    proc = subprocess.run(
        ["python3", os.path.join(PLUGIN_ROOT, "hooks", "stop.py")],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": PLUGIN_ROOT},
    )
    assert proc.returncode == 0
    output = json.loads(proc.stdout)
    assert "systemMessage" in output


def test_stop_hook_ignores_simple():
    input_data = {"hook_event_name": "Stop", "reason": "Done."}
    proc = subprocess.run(
        ["python3", os.path.join(PLUGIN_ROOT, "hooks", "stop.py")],
        input=json.dumps(input_data),
        capture_output=True,
        text=True,
        timeout=10,
        env={**os.environ, "CLAUDE_PLUGIN_ROOT": PLUGIN_ROOT},
    )
    assert proc.returncode == 0
    output = json.loads(proc.stdout)
    assert output == {}
