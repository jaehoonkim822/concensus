import os
import sys
import subprocess
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.cli_runner import run_gemini, run_codex, run_models_parallel, CLIResult


def test_cli_result_dataclass():
    r = CLIResult(model="gemini", output="hello", success=True, error=None)
    assert r.model == "gemini"
    assert r.output == "hello"
    assert r.success is True


def test_run_gemini_returns_result():
    result = run_gemini("What is 2+2? Reply with just the number.", timeout=90)
    assert isinstance(result, CLIResult)
    assert result.model == "gemini"
    assert result.success is True
    assert "4" in result.output


def test_run_codex_returns_result():
    result = run_codex("What is 2+2? Reply with just the number.", timeout=90)
    assert isinstance(result, CLIResult)
    assert result.model == "codex"
    assert result.success is True
    assert "4" in result.output


def test_run_models_parallel():
    results = run_models_parallel(
        "What is 2+2? Reply with just the number.",
        models=["gemini", "codex"],
        timeout=120,
    )
    assert len(results) == 2
    assert all(r.success for r in results)


def test_run_gemini_timeout():
    result = run_gemini("Count to a million slowly", timeout=1)
    assert result.success is False
    assert result.error is not None
