import os
import sys
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.consensus_engine import (
    ConsensusResult,
    ConsensusStatus,
    build_verification_prompt,
    build_debate_prompt,
    determine_consensus,
    run_consensus,
)
from core.cli_runner import CLIResult


def test_consensus_status_values():
    assert ConsensusStatus.FULL_CONSENSUS.value == "FULL_CONSENSUS"
    assert ConsensusStatus.MAJORITY_AGREE.value == "MAJORITY_AGREE"
    assert ConsensusStatus.NO_CONSENSUS.value == "NO_CONSENSUS"
    assert ConsensusStatus.SKIPPED.value == "SKIPPED"


def test_build_verification_prompt_code():
    prompt = build_verification_prompt(
        mode="code",
        context="def add(a, b):\n    return a + b",
        file_path="math.py",
    )
    assert "math.py" in prompt
    assert "def add" in prompt
    assert "Review" in prompt or "review" in prompt


def test_build_debate_prompt():
    prompt = build_debate_prompt(
        original_context="def add(a, b): return a+b",
        responses={
            "claude": "Looks good",
            "gemini": "Missing type hints",
            "codex": "Needs docstring",
        },
        model_name="gemini",
    )
    assert "claude" in prompt.lower() or "Claude" in prompt
    assert "codex" in prompt.lower() or "Codex" in prompt
    assert "Missing type hints" in prompt or "gemini" in prompt


def test_determine_consensus_full():
    responses = {
        "claude": "VERDICT: APPROVE\nThe code is correct.",
        "gemini": "VERDICT: APPROVE\nLooks good.",
        "codex": "VERDICT: APPROVE\nNo issues found.",
    }
    status = determine_consensus(responses)
    assert status == ConsensusStatus.FULL_CONSENSUS


def test_determine_consensus_majority_concerns():
    responses = {
        "claude": "VERDICT: APPROVE\nThe code is perfect.",
        "gemini": "VERDICT: CONCERNS\n- Off-by-one error in loop.",
        "codex": "VERDICT: CONCERNS\n- Bug: loop iterates one too many times.",
    }
    status = determine_consensus(responses)
    assert status == ConsensusStatus.MAJORITY_AGREE


def test_determine_consensus_all_concerns():
    responses = {
        "claude": "VERDICT: CONCERNS\nMissing validation.",
        "gemini": "VERDICT: CONCERNS\n- Off-by-one error.",
        "codex": "VERDICT: CONCERNS\n- Bug in loop.",
    }
    status = determine_consensus(responses)
    assert status == ConsensusStatus.FULL_CONSENSUS


def test_run_consensus_integration():
    """Integration test - runs actual CLI calls."""
    result = run_consensus(
        mode="code",
        context="def add(a, b):\n    return a + b",
        file_path="math.py",
        config={"models": ["gemini", "codex"], "debate_rounds": 1, "cli_timeout": 90},
    )
    assert isinstance(result, ConsensusResult)
    assert result.status in ConsensusStatus
    assert result.round >= 0
    assert isinstance(result.summary, str)
    assert len(result.summary) > 0
