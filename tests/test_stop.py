import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugin"))
from hooks.stop import detect_design_decision, format_stop_output


def test_detect_architecture_keywords():
    text = "I recommend we use a microservices architecture for this system."
    assert detect_design_decision(text) is True


def test_detect_design_pattern():
    text = "Let's implement the observer pattern for event handling."
    assert detect_design_decision(text) is True


def test_no_design_decision_in_code():
    text = "Here's the updated function that fixes the bug:\ndef foo(): return 42"
    assert detect_design_decision(text) is False


def test_no_design_decision_in_simple_response():
    text = "Done. The file has been updated."
    assert detect_design_decision(text) is False


def test_detect_tradeoff_language():
    text = "We have two options: use Redis for caching or implement in-memory LRU. I suggest Redis because it scales better across instances."
    assert detect_design_decision(text) is True


def test_format_stop_output():
    output = format_stop_output("design decision context here")
    parsed = json.loads(output)
    assert "systemMessage" in parsed
    assert "CONSENSUS" in parsed["systemMessage"] or "cross-validate" in parsed["systemMessage"].lower()
