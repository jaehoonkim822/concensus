#!/usr/bin/env python3
import os
import sys
import json
import re

PLUGIN_ROOT = os.environ.get(
    "CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if PLUGIN_ROOT not in sys.path:
    sys.path.insert(0, PLUGIN_ROOT)

from core.config import load_config
from core.consensus_engine import run_consensus

SIGNAL_WORDS = re.compile(
    r"\b(implement|design|architect|build|create|migrate|refactor|"
    r"restructure|overhaul|integrate|deploy|introduce|establish|"
    r"replace|rewrite|convert)\b",
    re.IGNORECASE,
)

QUESTION_START = re.compile(
    r"^\s*(what|how|why|where|when|who|which|can|could|is|are|do|does)\b",
    re.IGNORECASE,
)

ACTION_WORDS = re.compile(
    r"\b(implement|build|create|make|add|set up|deploy|migrate|refactor)\b",
    re.IGNORECASE,
)


def count_signal_words(text: str) -> int:
    return len(SIGNAL_WORDS.findall(text))


def is_pure_question(text: str) -> bool:
    """Detect pure questions with no actionable intent."""
    if not QUESTION_START.search(text):
        return False
    if ACTION_WORDS.search(text):
        return False
    return True


def should_trigger(prompt: str, config: dict) -> bool:
    if not config.get("enabled", True):
        return False
    if not config.get("prompt_consensus_enabled", False):
        return False
    min_length = config.get("prompt_consensus_min_length", 100)
    if len(prompt) < min_length:
        return False
    if is_pure_question(prompt):
        return False
    signal_count = count_signal_words(prompt)
    if signal_count >= 2:
        return True
    if signal_count >= 1 and len(prompt) >= 200:
        return True
    return False


def format_hook_output(consensus_summary: str) -> str:
    return json.dumps({
        "systemMessage": f"[CONSENSUS PRE-CHECK]\n{consensus_summary}"
    })


def main():
    try:
        input_data = json.load(sys.stdin)
        config = load_config()
        prompt = input_data.get("prompt", "")

        if not should_trigger(prompt, config):
            print(json.dumps({}))
            return

        result = run_consensus(
            mode="direction",
            context=prompt,
            config=config,
        )
        print(format_hook_output(result.summary))
    except Exception as e:
        print(json.dumps({"systemMessage": f"[Concensus userpromptsubmit hook error: {e}]"}))
    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
