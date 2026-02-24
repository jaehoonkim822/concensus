import os
import sys
import json
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "plugin"))
from hooks.userpromptsubmit import (
    should_trigger,
    format_hook_output,
    count_signal_words,
    is_pure_question,
)


def test_should_trigger_substantial_prompt():
    prompt = (
        "I want to implement a new microservices architecture and migrate "
        "the existing monolith. We need to refactor the authentication system "
        "and restructure the database layer for better scalability."
    )
    config = {"enabled": True, "prompt_consensus_enabled": True, "prompt_consensus_min_length": 100}
    assert should_trigger(prompt, config) is True


def test_should_skip_short_prompt():
    prompt = "implement this feature"
    config = {"enabled": True, "prompt_consensus_enabled": True, "prompt_consensus_min_length": 100}
    assert should_trigger(prompt, config) is False


def test_should_skip_pure_question():
    prompt = (
        "What is the difference between microservices and monolith architectures? "
        "How do they compare in terms of scalability and maintainability for large teams?"
    )
    config = {"enabled": True, "prompt_consensus_enabled": True, "prompt_consensus_min_length": 100}
    assert should_trigger(prompt, config) is False


def test_should_skip_when_opt_in_disabled():
    prompt = (
        "I want to implement a new microservices architecture and migrate "
        "the existing monolith. We need to refactor the authentication system."
    )
    config = {"enabled": True, "prompt_consensus_enabled": False, "prompt_consensus_min_length": 100}
    assert should_trigger(prompt, config) is False


def test_should_skip_when_globally_disabled():
    prompt = (
        "I want to implement a new microservices architecture and migrate "
        "the existing monolith. We need to refactor the authentication system."
    )
    config = {"enabled": False, "prompt_consensus_enabled": True, "prompt_consensus_min_length": 100}
    assert should_trigger(prompt, config) is False


def test_one_signal_word_long_prompt():
    prompt = (
        "We should implement a comprehensive logging system that captures all API requests, "
        "response times, error rates, and user interactions across the entire platform. "
        "This needs to support structured logging with correlation IDs for distributed tracing."
    )
    config = {"enabled": True, "prompt_consensus_enabled": True, "prompt_consensus_min_length": 100}
    assert should_trigger(prompt, config) is True


def test_one_signal_word_short_prompt():
    prompt = "We need to implement a new logging system for API requests and error tracking."
    config = {"enabled": True, "prompt_consensus_enabled": True, "prompt_consensus_min_length": 50}
    assert should_trigger(prompt, config) is False


def test_count_signal_words():
    assert count_signal_words("implement and refactor the system") == 2
    assert count_signal_words("fix the typo") == 0
    assert count_signal_words("design and build a new API") == 2
    assert count_signal_words("implement, design, and build a new API") == 3


def test_is_pure_question_true():
    assert is_pure_question("What is the best database for this use case?") is True
    assert is_pure_question("How does Redis handle persistence?") is True


def test_is_pure_question_false_with_action():
    assert is_pure_question("How do I implement caching with Redis?") is False


def test_is_pure_question_false_not_question():
    assert is_pure_question("Let's build a new API gateway") is False


def test_format_hook_output():
    output = format_hook_output("Some consensus result")
    parsed = json.loads(output)
    assert "systemMessage" in parsed
    assert "CONSENSUS PRE-CHECK" in parsed["systemMessage"]
