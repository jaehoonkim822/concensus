import subprocess
import json
from dataclasses import dataclass
from typing import List, Optional
from concurrent.futures import ThreadPoolExecutor, as_completed


@dataclass
class CLIResult:
    model: str
    output: str
    success: bool
    error: Optional[str]


def run_gemini(prompt: str, timeout: int = 45) -> CLIResult:
    try:
        proc = subprocess.run(
            ["gemini", "-p", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode == 0:
            return CLIResult(
                model="gemini",
                output=proc.stdout.strip(),
                success=True,
                error=None,
            )
        return CLIResult(
            model="gemini",
            output="",
            success=False,
            error=proc.stderr.strip() or f"Exit code {proc.returncode}",
        )
    except subprocess.TimeoutExpired:
        return CLIResult(model="gemini", output="", success=False, error="Timeout")
    except FileNotFoundError:
        return CLIResult(
            model="gemini", output="", success=False, error="gemini CLI not found"
        )


def run_codex(prompt: str, timeout: int = 45) -> CLIResult:
    try:
        proc = subprocess.run(
            ["codex", "exec", "--json", prompt],
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        if proc.returncode == 0:
            text = _extract_codex_text(proc.stdout)
            return CLIResult(model="codex", output=text, success=True, error=None)
        return CLIResult(
            model="codex",
            output="",
            success=False,
            error=proc.stderr.strip() or f"Exit code {proc.returncode}",
        )
    except subprocess.TimeoutExpired:
        return CLIResult(model="codex", output="", success=False, error="Timeout")
    except FileNotFoundError:
        return CLIResult(
            model="codex", output="", success=False, error="codex CLI not found"
        )


def _extract_codex_text(jsonl_output: str) -> str:
    texts = []
    for line in jsonl_output.strip().split("\n"):
        if not line.strip():
            continue
        try:
            event = json.loads(line)
            if event.get("type") == "item.completed":
                item = event.get("item", {})
                if item.get("type") == "agent_message":
                    texts.append(item.get("text", ""))
        except json.JSONDecodeError:
            continue
    return "\n".join(texts).strip()


def run_models_parallel(
    prompt: str, models: List[str], timeout: int = 45
) -> List[CLIResult]:
    runners = {"gemini": run_gemini, "codex": run_codex}
    results = []
    with ThreadPoolExecutor(max_workers=len(models)) as executor:
        futures = {}
        for model in models:
            if model in runners:
                futures[executor.submit(runners[model], prompt, timeout)] = model
        for future in as_completed(futures):
            results.append(future.result())
    return results
