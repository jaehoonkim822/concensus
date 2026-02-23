# Concensus

**Multi-LLM cross-validation plugin for Claude Code**

Concensus automatically verifies Claude's outputs by running parallel evaluations with **Gemini CLI** and **Codex CLI**, then reaching consensus through iterative debate. When Claude writes code or makes design decisions, Concensus triggers all three models to independently review the work and converge on a shared verdict.

## Theoretical Background

Concensus builds on a growing body of research showing that **multiple LLMs debating each other produce better results than any single model alone**. The core insight: when models with different training data and architectures independently review the same code, their diverse failure modes cancel out, surfacing real issues while filtering false positives.

### Foundational Concept

The multi-agent approach traces back to Marvin Minsky's [*The Society of Mind*](https://en.wikipedia.org/wiki/Society_of_Mind) (1986) — the idea that intelligence emerges from the interaction of many simple, individually limited agents. Concensus applies this principle to LLM-based code review: Claude, Gemini, and Codex each bring different strengths and blind spots, and their structured disagreement produces more reliable judgments than any single model.

### Core Research

| Paper | Venue | Key Finding | How Concensus Uses It |
|-------|-------|-------------|----------------------|
| [**Improving Factuality and Reasoning through Multiagent Debate**](https://arxiv.org/abs/2305.14325) (Du et al., 2023) | ICML 2024 | Multiple LLM instances debating over rounds reduces hallucinations and improves factual validity. More agents and more rounds = better results. | The fundamental premise: multi-round debate between models catches errors that individual models miss. |
| [**ReConcile: Round-Table Conference Improves Reasoning via Consensus among Diverse LLMs**](https://arxiv.org/abs/2309.13007) (Chen et al., 2023) | ACL 2024 | A round-table conference with confidence-weighted voting across diverse LLM families (ChatGPT, Bard, Claude) improves reasoning by up to 11.4%. **Model diversity is the primary driver of improvement.** | Concensus's debate protocol directly follows ReConcile's structure: independent responses → share all positions → iterative refinement → consensus vote. |
| [**ICE: Iterative Consensus Ensemble**](https://www.sciencedirect.com/science/article/abs/pii/S0010482525010820) (2025) | Computers in Biology and Medicine | Three LLMs critiquing each other converge in 2-3 rounds on average, achieving up to 27% accuracy improvement with no fine-tuning. | Validates our default of `debate_rounds: 2` — most consensus emerges within 2-3 rounds, with diminishing returns after. |
| [**Debate or Vote: Which Yields Better Decisions in Multi-Agent LLMs?**](https://arxiv.org/abs/2508.17536) (Choi et al., 2025) | NeurIPS 2025 Spotlight | Majority voting alone accounts for most performance gains in multi-agent systems. Multi-round debate adds marginal benefit in some settings. Debate induces a martingale over belief trajectories. | Informs our hybrid approach: we use majority voting as the fast path (`FULL_CONSENSUS` / `MAJORITY_AGREE`) and only trigger debate rounds when initial votes disagree. |
| [**Mixture-of-Agents Enhances LLM Capabilities**](https://arxiv.org/abs/2406.04692) (Wang et al., 2024) | arXiv | A layered proposer-aggregator architecture where models improve when presented with other models' outputs — termed "collaborativeness of LLMs." Open-source models outperformed GPT-4o on AlpacaEval. | Validates that even less-capable models provide useful signal as reviewers when their output is aggregated by a stronger model. |
| [**A Survey on LLM-as-a-Judge**](https://arxiv.org/abs/2411.15594) (Zheng et al., 2024) | arXiv | Comprehensive survey on using LLMs as evaluators. Key challenge: single-model judges exhibit systematic biases (position, verbosity, self-preference). | Motivates using multiple diverse models as judges rather than relying on Claude alone for code review. Cross-model validation reduces individual model biases. |

### Why Three Different Model Families?

ReConcile's key finding is that **model diversity matters more than model capability**. Three instances of the same model debating each other show less improvement than three different models. Concensus leverages this by combining:

- **Claude** (Anthropic) — the author of the code, strong at structured reasoning
- **Gemini** (Google) — trained on different data, different architecture
- **Codex** (OpenAI) — code-specialized, different training distribution

This maximizes the "collaborative intelligence" effect described in the Mixture-of-Agents paper.

### Design Decisions Informed by Research

| Decision | Research Basis |
|----------|---------------|
| Default 2 debate rounds | ICE shows convergence at 2.3 rounds average |
| Parallel execution in Round 0 | Independent initial judgments before seeing others (ReConcile) |
| Majority vote as fast path | "Debate or Vote" shows voting captures most gains |
| Share all responses in debate | ReConcile's "discussion prompt" with grouped answers |
| Three model families | ReConcile's finding: diversity > capability |

## How It Works

```
Claude writes code (Write/Edit)
        |
   PostToolUse Hook fires
        |
   +---------+---------+
   |         |         |
 Claude   Gemini    Codex      <-- Round 0: Independent review
   |         |         |
   +---------+---------+
        |
   Consensus check
        |
   Agree? ──yes──> Done (inject result as system message)
        |
       no
        |
   +---------+---------+
   |         |         |
 Claude   Gemini    Codex      <-- Round 1-2: Debate (see others' responses)
   |         |         |
   +---------+---------+
        |
   Final verdict injected
```

### Two Hook Types

| Hook | Trigger | Timeout | Purpose |
|------|---------|---------|---------|
| **PostToolUse** | `Write` or `Edit` tool | 120s | Cross-validates code changes with 5+ lines |
| **Stop** | End of Claude response | 10s | Detects architecture/design decisions and recommends cross-validation |

### Consensus Statuses

| Status | Meaning |
|--------|---------|
| `FULL_CONSENSUS` | All models agree (all approve or all raise concerns) |
| `MAJORITY_AGREE` | 2 of 3 models share the same verdict |
| `NO_CONSENSUS` | Models disagree — review carefully |

## Prerequisites

- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (v2.0+)
- [Gemini CLI](https://geminicli.com/) — `npm install -g @google/gemini-cli`
- [Codex CLI](https://github.com/openai/codex) — `npm install -g @openai/codex`
- Python 3.10+

Verify both CLIs are installed:

```bash
gemini -p "hello"
codex exec --json "hello"
```

## Installation

### Step 1: Add the marketplace

```bash
claude plugin marketplace add jaehoonkim822/concensus
```

### Step 2: Install the plugin

```bash
claude plugin install concensus
```

That's it. The plugin is now active for all your Claude Code sessions.

### Alternative: Development mode

For local development or testing:

```bash
git clone https://github.com/jaehoonkim822/concensus.git
claude --plugin-dir ./concensus/plugin
```

## Configuration

Create `.claude/concensus.local.md` in your project root to override defaults:

```markdown
---
enabled: true
min_change_lines: 5
debate_rounds: 2
models:
  - gemini
  - codex
cli_timeout: 45
skip_paths:
  - "*.md"
  - "*.json"
  - "*.yaml"
  - "*.yml"
  - "*.lock"
  - "*.txt"
  - "node_modules/**"
  - ".git/**"
  - "__pycache__/**"
---

Optional notes about your project's consensus preferences.
```

### Configuration Options

| Option | Default | Description |
|--------|---------|-------------|
| `enabled` | `true` | Enable/disable the plugin |
| `min_change_lines` | `5` | Minimum lines changed to trigger review |
| `debate_rounds` | `2` | Maximum debate rounds (0-3) |
| `models` | `[gemini, codex]` | Which external models to consult |
| `cli_timeout` | `45` | Timeout per CLI call in seconds |
| `skip_paths` | See above | Glob patterns for files to skip |

## Architecture

```
concensus/
├── .claude-plugin/
│   └── marketplace.json       # Marketplace registration
├── plugin/
│   ├── .claude-plugin/
│   │   └── plugin.json        # Plugin manifest
│   ├── hooks/
│   │   ├── hooks.json         # Hook registration (PostToolUse + Stop)
│   │   ├── posttooluse.py     # Code change validator
│   │   └── stop.py            # Design decision detector
│   ├── core/
│   │   ├── config.py          # Config loader (YAML frontmatter)
│   │   ├── cli_runner.py      # Gemini/Codex CLI wrapper
│   │   └── consensus_engine.py # Debate protocol orchestration
│   ├── templates/
│   │   ├── verify-code.txt    # Code review prompt
│   │   ├── verify-design.txt  # Design review prompt
│   │   └── debate-round.txt   # Debate round prompt
│   └── config/
│       └── defaults.yaml      # Default config reference
├── tests/                     # Test suite (29 unit + 4 E2E tests)
└── docs/plans/                # Design documents
```

### Data Flow

1. **Hook fires** — Claude Code calls the hook script via `python3` with JSON on stdin
2. **Filter** — Check if file type, change size, and config allow triggering
3. **Round 0** — Build verification prompt, run Gemini + Codex in parallel via `ThreadPoolExecutor`
4. **Consensus check** — Extract `VERDICT: APPROVE/CONCERNS` from each response
5. **Debate rounds** — If no consensus, share responses between models and re-evaluate (parallel)
6. **Result injection** — Output JSON to stdout with `systemMessage` field, which Claude Code displays

### How the Stop Hook Works

The Stop hook scans Claude's response for architectural/design patterns using regex:

- Architecture keywords (microservices, monolith, event-driven)
- Design patterns (observer, singleton, factory)
- Trade-off language ("pros and cons", "two options")
- Database/API/auth design discussions

When detected, it injects an advisory system message recommending cross-validation.

## Development

```bash
git clone https://github.com/jaehoonkim822/concensus.git
cd concensus

# Run unit tests (fast, no CLI dependency)
python3 -m pytest tests/ -k "not (test_run_gemini_returns_result or test_run_codex_returns_result or test_run_models_parallel or integration)"

# Run all tests including CLI integration (requires gemini + codex installed)
python3 -m pytest tests/ -v
```

## How the Debate Protocol Works

The debate protocol is based on the ReConcile paper's approach:

**Round 0 (Independent Review):**
Each model independently reviews the code using a structured prompt that asks for a `VERDICT: APPROVE` or `VERDICT: CONCERNS` response.

**Round 1+ (Debate):**
If models disagree, each model receives:
- The original code context
- Its own previous response
- All other models' responses

Models then reconsider their position, potentially updating their verdict. This iterative refinement helps surface true issues while filtering out false positives.

**Convergence:**
The process stops when consensus is reached or the maximum debate rounds are exhausted.

## Limitations

- Gemini CLI has ~60s startup overhead per call (credential/skill loading)
- Total PostToolUse hook timeout is 120s — tight for 2 debate rounds
- Codex CLI requires `--json` mode for structured output parsing
- The verdict extraction uses regex + keyword fallback heuristic

## License

MIT
