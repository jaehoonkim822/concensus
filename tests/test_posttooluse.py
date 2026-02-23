import os
import sys
import json
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from hooks.posttooluse import should_trigger, build_context_from_input, format_hook_output


def test_should_trigger_write():
    input_data = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": "/project/src/main.py",
            "content": "line1\nline2\nline3\nline4\nline5\nline6\n",
        },
    }
    config = {"enabled": True, "skip_paths": ["*.md"], "min_change_lines": 5}
    assert should_trigger(input_data, config) is True


def test_should_not_trigger_markdown():
    input_data = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": "/project/README.md",
            "content": "a\nb\nc\nd\ne\nf\n",
        },
    }
    config = {"enabled": True, "skip_paths": ["*.md"], "min_change_lines": 5}
    assert should_trigger(input_data, config) is False


def test_should_not_trigger_small_change():
    input_data = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "/project/src/main.py",
            "new_string": "x = 1\n",
            "old_string": "x = 0\n",
        },
    }
    config = {"enabled": True, "skip_paths": [], "min_change_lines": 5}
    assert should_trigger(input_data, config) is False


def test_should_not_trigger_disabled():
    input_data = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": "/project/src/main.py",
            "content": "a\nb\nc\nd\ne\nf\n",
        },
    }
    config = {"enabled": False, "skip_paths": [], "min_change_lines": 5}
    assert should_trigger(input_data, config) is False


def test_build_context_write():
    input_data = {
        "tool_name": "Write",
        "tool_input": {
            "file_path": "/project/src/main.py",
            "content": "def hello():\n    print('hi')\n",
        },
    }
    ctx = build_context_from_input(input_data)
    assert ctx["mode"] == "code"
    assert ctx["file_path"] == "/project/src/main.py"
    assert "def hello" in ctx["content"]


def test_build_context_edit():
    input_data = {
        "tool_name": "Edit",
        "tool_input": {
            "file_path": "/project/src/main.py",
            "old_string": "x = 0",
            "new_string": "x = 1\ny = 2\nz = 3\n",
        },
    }
    ctx = build_context_from_input(input_data)
    assert ctx["mode"] == "code"
    assert "x = 1" in ctx["content"]


def test_format_hook_output():
    output = format_hook_output("Some consensus result")
    parsed = json.loads(output)
    assert "systemMessage" in parsed
    assert "CONSENSUS" in parsed["systemMessage"]
