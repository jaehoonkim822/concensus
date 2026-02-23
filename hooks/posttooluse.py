#!/usr/bin/env python3
import os
import sys
import json

PLUGIN_ROOT = os.environ.get(
    "CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from core.config import load_config, should_skip_path, should_skip_change
from core.consensus_engine import run_consensus


def should_trigger(input_data: dict, config: dict) -> bool:
    if not config.get("enabled", True):
        return False
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    if should_skip_path(file_path, config):
        return False
    content = _get_change_content(input_data)
    if should_skip_change(content, config):
        return False
    return True


def _get_change_content(input_data: dict) -> str:
    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    if tool_name == "Write":
        return tool_input.get("content", "")
    elif tool_name == "Edit":
        return tool_input.get("new_string", "")
    return ""


def build_context_from_input(input_data: dict) -> dict:
    tool_input = input_data.get("tool_input", {})
    file_path = tool_input.get("file_path", "")
    content = _get_change_content(input_data)
    return {"mode": "code", "file_path": file_path, "content": content}


def format_hook_output(consensus_summary: str) -> str:
    return json.dumps({"systemMessage": f"[CONSENSUS REVIEW]\n{consensus_summary}"})


def main():
    try:
        input_data = json.load(sys.stdin)
        config = load_config()
        if not should_trigger(input_data, config):
            print(json.dumps({}))
            return
        ctx = build_context_from_input(input_data)
        result = run_consensus(
            mode=ctx["mode"],
            context=ctx["content"],
            file_path=ctx["file_path"],
            config=config,
        )
        print(format_hook_output(result.summary))
    except Exception as e:
        print(json.dumps({"systemMessage": f"[Concensus error: {e}]"}))
    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
