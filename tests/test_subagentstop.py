import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugin"))
from hooks.subagentstop import should_trigger, format_hook_output


def test_should_trigger_explore_agent():
    input_data = {
        "agent_type": "Explore",
        "last_assistant_message": "x" * 250,
    }
    config = {"enabled": True, "subagent_consensus_enabled": True}
    assert should_trigger(input_data, config) is True


def test_should_trigger_plan_agent():
    input_data = {
        "agent_type": "Plan",
        "last_assistant_message": "x" * 250,
    }
    config = {"enabled": True, "subagent_consensus_enabled": True}
    assert should_trigger(input_data, config) is True


def test_should_skip_bash_agent():
    input_data = {
        "agent_type": "Bash",
        "last_assistant_message": "x" * 250,
    }
    config = {"enabled": True, "subagent_consensus_enabled": True}
    assert should_trigger(input_data, config) is False


def test_should_skip_short_message():
    input_data = {
        "agent_type": "Explore",
        "last_assistant_message": "Short message",
    }
    config = {"enabled": True, "subagent_consensus_enabled": True}
    assert should_trigger(input_data, config) is False


def test_should_skip_when_disabled():
    input_data = {
        "agent_type": "Explore",
        "last_assistant_message": "x" * 250,
    }
    config = {"enabled": True, "subagent_consensus_enabled": False}
    assert should_trigger(input_data, config) is False


def test_should_skip_when_globally_disabled():
    input_data = {
        "agent_type": "Explore",
        "last_assistant_message": "x" * 250,
    }
    config = {"enabled": False, "subagent_consensus_enabled": True}
    assert should_trigger(input_data, config) is False


def test_format_hook_output():
    output = format_hook_output("Some consensus result")
    parsed = json.loads(output)
    assert "systemMessage" in parsed
    assert "CONSENSUS REVIEW - SUBAGENT" in parsed["systemMessage"]
