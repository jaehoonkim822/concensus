import os
import re
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.cli_runner import run_models_parallel, run_gemini, run_codex


class ConsensusStatus(Enum):
    FULL_CONSENSUS = "FULL_CONSENSUS"
    MAJORITY_AGREE = "MAJORITY_AGREE"
    NO_CONSENSUS = "NO_CONSENSUS"
    SKIPPED = "SKIPPED"


@dataclass
class ConsensusResult:
    status: ConsensusStatus
    round: int
    summary: str
    responses: Dict[str, str] = field(default_factory=dict)
    recommendation: str = ""


PLUGIN_ROOT = os.environ.get(
    "CLAUDE_PLUGIN_ROOT", os.path.dirname(os.path.dirname(__file__))
)


def _load_template(name: str) -> str:
    path = os.path.join(PLUGIN_ROOT, "templates", name)
    with open(path, "r") as f:
        return f.read()


def build_verification_prompt(mode: str, context: str, file_path: str = "") -> str:
    template_name = "verify-code.txt" if mode == "code" else "verify-design.txt"
    template = _load_template(template_name)
    return template.replace("{{context}}", context).replace("{{file_path}}", file_path)


def build_debate_prompt(
    original_context: str, responses: Dict[str, str], model_name: str
) -> str:
    template = _load_template("debate-round.txt")
    own_response = responses.get(model_name, "")
    other_lines = []
    for name, resp in responses.items():
        if name != model_name:
            other_lines.append(f"[{name}]: {resp}")
    return (
        template.replace("{{original_context}}", original_context)
        .replace("{{own_response}}", own_response)
        .replace("{{other_responses}}", "\n\n".join(other_lines))
    )


def _extract_verdict(text: str) -> str:
    match = re.search(r"VERDICT:\s*(APPROVE|CONCERNS)", text, re.IGNORECASE)
    if match:
        return match.group(1).upper()
    if any(w in text.lower() for w in ["bug", "issue", "error", "concern", "problem"]):
        return "CONCERNS"
    return "APPROVE"


def determine_consensus(responses: Dict[str, str]) -> ConsensusStatus:
    verdicts = {name: _extract_verdict(text) for name, text in responses.items()}
    approve_count = sum(1 for v in verdicts.values() if v == "APPROVE")
    total = len(verdicts)
    if approve_count == total:
        return ConsensusStatus.FULL_CONSENSUS
    if approve_count == 0:
        return ConsensusStatus.FULL_CONSENSUS  # all have concerns = consensus on concerns
    return ConsensusStatus.MAJORITY_AGREE


def _format_result(
    status: ConsensusStatus, round_num: int, responses: Dict[str, str]
) -> ConsensusResult:
    verdicts = {name: _extract_verdict(text) for name, text in responses.items()}
    lines = [f"Status: {status.value} (round {round_num})"]
    approve_models = [n for n, v in verdicts.items() if v == "APPROVE"]
    concern_models = [n for n, v in verdicts.items() if v == "CONCERNS"]
    if approve_models:
        lines.append(f"Approve: {', '.join(approve_models)}")
    if concern_models:
        lines.append(f"Concerns raised by: {', '.join(concern_models)}")
        for model in concern_models:
            lines.append(f"  [{model}]: {responses[model][:300]}")
    recommendation = ""
    if status == ConsensusStatus.FULL_CONSENSUS and not concern_models:
        recommendation = "All models agree. Proceed as-is."
    elif concern_models:
        recommendation = f"Review concerns raised by {', '.join(concern_models)} before proceeding."
    return ConsensusResult(
        status=status,
        round=round_num,
        summary="\n".join(lines),
        responses=responses,
        recommendation=recommendation,
    )


def run_consensus(
    mode: str, context: str, file_path: str = "", config: Optional[Dict] = None
) -> ConsensusResult:
    config = config or {}
    models = config.get("models", ["gemini", "codex"])
    max_rounds = config.get("debate_rounds", 2)
    cli_timeout = config.get("cli_timeout", 90)

    prompt = build_verification_prompt(mode, context, file_path)
    cli_results = run_models_parallel(prompt, models, timeout=cli_timeout)

    responses = {"claude": f"(Original author of the code at {file_path})"}
    for r in cli_results:
        if r.success:
            responses[r.model] = r.output
        else:
            responses[r.model] = f"[Error: {r.error}]"

    successful = [r for r in cli_results if r.success]
    if not successful:
        return ConsensusResult(
            status=ConsensusStatus.SKIPPED,
            round=0,
            summary="No models responded successfully. Skipping consensus.",
            responses=responses,
            recommendation="Consensus unavailable. Proceed with caution.",
        )

    active_responses = {k: v for k, v in responses.items() if not v.startswith("[Error")}
    status = determine_consensus(active_responses)
    if status == ConsensusStatus.FULL_CONSENSUS:
        return _format_result(status, 0, responses)

    for round_num in range(1, max_rounds + 1):
        debate_prompts = {}
        for model in models:
            if model in responses and not responses[model].startswith("[Error"):
                debate_prompts[model] = build_debate_prompt(context, responses, model)
        for model, dprompt in debate_prompts.items():
            runner = run_gemini if model == "gemini" else run_codex
            result = runner(dprompt, timeout=cli_timeout)
            if result.success:
                responses[result.model] = result.output
        active_responses = {k: v for k, v in responses.items() if not v.startswith("[Error")}
        status = determine_consensus(active_responses)
        if status == ConsensusStatus.FULL_CONSENSUS:
            return _format_result(status, round_num, responses)

    return _format_result(status, max_rounds, responses)
