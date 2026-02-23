# Concensus

**Multi-LLM cross-validation plugin for Claude Code**

Concensus automatically verifies Claude's outputs by running parallel evaluations with **Gemini CLI** and **Codex CLI**, then reaching consensus through iterative debate. When Claude writes code or makes design decisions, Concensus triggers all three models to independently review the work and converge on a shared verdict.

Inspired by [ReConcile (ACL 2024)](https://arxiv.org/abs/2309.13007) and [ICE (2025)](https://arxiv.org/abs/2408.00721) — multi-agent debate protocols that improve LLM reasoning through structured disagreement.

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
- [Gemini CLI](https://github.com/google-gemini/gemini-cli) — `npm install -g @anthropic-ai/gemini-cli` or equivalent
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
