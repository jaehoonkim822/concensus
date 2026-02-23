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

DESIGN_PATTERNS = [
    r"\b(architect(?:ure|ural))\b",
    r"\b(design pattern|observer|singleton|factory|strategy)\b",
    r"\b(microservice|monolith|event[- ]driven|serverless)\b",
    r"\b(trade[- ]?off|pros?\s+and\s+cons?)\b",
    r"\b(I (?:recommend|suggest|propose)\s+(?:we|to)\s+(?:use|implement|adopt))\b",
    r"\b((?:two|three|multiple)\s+(?:options?|approaches?|alternatives?))\b",
    r"\b(database\s+(?:schema|design|model))\b",
    r"\b(API\s+(?:design|structure|contract))\b",
    r"\b(state\s+management|caching\s+strategy|auth(?:entication)?\s+(?:flow|method))\b",
]

DESIGN_REGEX = re.compile("|".join(DESIGN_PATTERNS), re.IGNORECASE)


def detect_design_decision(text: str) -> bool:
    if len(text) < 50:
        return False
    return bool(DESIGN_REGEX.search(text))


def format_stop_output(context: str) -> str:
    snippet = context[:200].replace('"', "'")
    return json.dumps({
        "systemMessage": (
            "[CONSENSUS RECOMMENDED] This response contains an architectural/design decision. "
            "Before proceeding, consider cross-validating this decision with other models. "
            f"Key context: {snippet}"
        )
    })


def main():
    try:
        input_data = json.load(sys.stdin)
        config = load_config()
        if not config.get("enabled", True):
            print(json.dumps({}))
            sys.exit(0)
        transcript_path = input_data.get("transcript_path", "")
        reason = input_data.get("reason", "")
        assistant_text = reason
        if transcript_path and os.path.exists(transcript_path):
            try:
                with open(transcript_path, "r") as f:
                    content = f.read()
                assistant_text = content[-2000:] if len(content) > 2000 else content
            except (IOError, UnicodeDecodeError):
                pass
        if detect_design_decision(assistant_text):
            print(format_stop_output(assistant_text[:500]))
        else:
            print(json.dumps({}))
    except Exception as e:
        print(json.dumps({"systemMessage": f"[Concensus stop hook error: {e}]"}))
    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
