#!/usr/bin/env python3
import os
import sys
import json

PLUGIN_ROOT = os.environ.get(
    "CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from core.config import load_config
from core.consensus_engine import run_consensus

VALIDATED_AGENT_TYPES = {"Explore", "Plan"}
MIN_MESSAGE_LENGTH = 200


def should_trigger(input_data: dict, config: dict) -> bool:
    if not config.get("enabled", True):
        return False
    if not config.get("subagent_consensus_enabled", True):
        return False
    agent_type = input_data.get("agent_type", "")
    if agent_type not in VALIDATED_AGENT_TYPES:
        return False
    message = input_data.get("last_assistant_message", "")
    if len(message) < MIN_MESSAGE_LENGTH:
        return False
    return True


def format_hook_output(consensus_summary: str) -> str:
    return json.dumps({
        "systemMessage": f"[CONSENSUS REVIEW - SUBAGENT]\n{consensus_summary}"
    })


def main():
    try:
        input_data = json.load(sys.stdin)
        config = load_config()

        if not should_trigger(input_data, config):
            print(json.dumps({}))
            return

        message = input_data.get("last_assistant_message", "")
        result = run_consensus(
            mode="research",
            context=message[:4000],
            config=config,
        )
        print(format_hook_output(result.summary))
    except Exception as e:
        print(json.dumps({"systemMessage": f"[Concensus subagentstop hook error: {e}]"}))
    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
