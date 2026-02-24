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

PLAN_PATTERNS = [
    r"\bstep\s+[1-9]\b",
    r"\bphase\s+[1-9]\b",
    r"\bimplementation\s+plan\b",
    r"\bmilestone\s+\d+\b",
    r"(?:^|\n)\s*\d+\.\s+\S.*(?:\n\s*\d+\.\s+\S.*){2,}",
]

RESEARCH_PATTERNS = [
    r"\bfindings?\b",
    r"\bevidence\s+suggests?\b",
    r"\bcomparison\s+of\b",
    r"\bbenchmarks?\b",
    r"\banalysis\s+(?:shows?|indicates?|reveals?)\b",
    r"\bour\s+investigation\b",
]

DESIGN_REGEX = re.compile("|".join(DESIGN_PATTERNS), re.IGNORECASE)
PLAN_REGEX = re.compile("|".join(PLAN_PATTERNS), re.IGNORECASE | re.MULTILINE)
RESEARCH_REGEX = re.compile("|".join(RESEARCH_PATTERNS), re.IGNORECASE)


def detect_design_decision(text: str) -> bool:
    if len(text) < 50:
        return False
    return bool(DESIGN_REGEX.search(text))


def detect_content_type(text: str) -> str | None:
    """Detect content type with priority: plan > research > design > None."""
    if len(text) < 50:
        return None
    if PLAN_REGEX.search(text):
        return "plan"
    if RESEARCH_REGEX.search(text):
        return "research"
    if DESIGN_REGEX.search(text):
        return "design"
    return None


def format_stop_output(context: str) -> str:
    snippet = context[:200].replace('"', "'")
    return json.dumps({
        "systemMessage": (
            "[CONSENSUS RECOMMENDED] This response contains an architectural/design decision. "
            "Before proceeding, consider cross-validating this decision with other models. "
            f"Key context: {snippet}"
        )
    })


def format_consensus_output(consensus_summary: str) -> str:
    return json.dumps({
        "systemMessage": f"[CONSENSUS REVIEW - STOP]\n{consensus_summary}"
    })


def main():
    try:
        input_data = json.load(sys.stdin)

        if input_data.get("stop_hook_active", False):
            print(json.dumps({}))
            sys.exit(0)

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

        content_type = detect_content_type(assistant_text)

        if content_type in ("plan", "research"):
            result = run_consensus(
                mode=content_type,
                context=assistant_text[:4000],
                config=config,
            )
            print(format_consensus_output(result.summary))
        elif content_type == "design":
            print(format_stop_output(assistant_text[:500]))
        else:
            print(json.dumps({}))
    except Exception as e:
        print(json.dumps({"systemMessage": f"[Concensus stop hook error: {e}]"}))
    finally:
        sys.exit(0)


if __name__ == "__main__":
    main()
