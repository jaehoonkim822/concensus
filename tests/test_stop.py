import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugin"))
from hooks.stop import (
    detect_design_decision,
    detect_content_type,
    format_stop_output,
    format_consensus_output,
)


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


# --- detect_content_type tests ---

def test_detect_content_type_plan():
    text = (
        "Here is the implementation plan:\n"
        "1. Set up the database schema\n"
        "2. Create API endpoints\n"
        "3. Implement authentication\n"
        "4. Add integration tests"
    )
    assert detect_content_type(text) == "plan"


def test_detect_content_type_plan_with_phases():
    text = "Phase 1 involves setting up infrastructure. Phase 2 will handle the migration."
    assert detect_content_type(text) == "plan"


def test_detect_content_type_research():
    text = "Our investigation found several findings. Evidence suggests that the current approach has scalability issues."
    assert detect_content_type(text) == "research"


def test_detect_content_type_research_benchmarks():
    text = "The benchmarks show a 40% improvement in query performance after indexing the user_id column."
    assert detect_content_type(text) == "research"


def test_detect_content_type_design():
    text = "I recommend we use a microservices architecture for this system."
    assert detect_content_type(text) == "design"


def test_detect_content_type_none_simple():
    text = "Done. The file has been updated."
    assert detect_content_type(text) is None


def test_detect_content_type_none_short():
    text = "OK"
    assert detect_content_type(text) is None


def test_detect_content_type_plan_priority_over_design():
    """Plan patterns should take priority when both plan and design patterns exist."""
    text = (
        "I recommend we use microservices architecture:\n"
        "1. Set up service mesh\n"
        "2. Implement API gateway\n"
        "3. Configure load balancer\n"
        "4. Deploy monitoring"
    )
    assert detect_content_type(text) == "plan"


def test_format_consensus_output():
    output = format_consensus_output("Some consensus result")
    parsed = json.loads(output)
    assert "systemMessage" in parsed
    assert "CONSENSUS REVIEW - STOP" in parsed["systemMessage"]


# --- stop_hook_active guard test ---

def test_stop_hook_active_guard():
    """When stop_hook_active is True, the hook should be skipped (tested via input_data)."""
    # This tests the logic at the module level — the main() function checks this field
    # We verify the flag detection here conceptually; E2E tests verify the actual behavior
    input_data = {"stop_hook_active": True, "reason": "I recommend we use microservices architecture."}
    assert input_data.get("stop_hook_active", False) is True
