import os
import fnmatch
from typing import Dict, Any

DEFAULT_CONFIG = {
    "enabled": True,
    "trigger_tools": ["Write", "Edit"],
    "skip_paths": [
        "*.md", "*.json", "*.yaml", "*.yml", "*.lock", "*.txt",
        "node_modules/**", ".git/**", "__pycache__/**"
    ],
    "min_change_lines": 5,
    "debate_rounds": 2,
    "stop_debate_rounds": 1,
    "models": ["gemini", "codex"],
    "cli_timeout": 90,
    "subagent_consensus_enabled": True,
    "prompt_consensus_enabled": False,
    "prompt_consensus_min_length": 100,
}


def extract_frontmatter(content: str) -> Dict[str, Any]:
    if not content.startswith("---"):
        return {}
    parts = content.split("---", 2)
    if len(parts) < 3:
        return {}
    result = {}
    current_key = None
    current_list = []
    in_list = False
    for line in parts[1].split("\n"):
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        indent = len(line) - len(line.lstrip())
        if indent == 0 and ":" in line and not stripped.startswith("-"):
            if in_list and current_key:
                result[current_key] = current_list
                current_list = []
                in_list = False
            key, value = line.split(":", 1)
            key = key.strip()
            value = value.strip()
            if not value:
                current_key = key
                in_list = True
                current_list = []
            else:
                value = value.strip("\"'")
                if value.lower() == "true":
                    value = True
                elif value.lower() == "false":
                    value = False
                elif value.isdigit():
                    value = int(value)
                result[key] = value
        elif stripped.startswith("-") and in_list:
            current_list.append(stripped[1:].strip().strip("\"'"))
    if in_list and current_key:
        result[current_key] = current_list
    return result


def load_config(config_dir: str = ".claude") -> Dict[str, Any]:
    config = dict(DEFAULT_CONFIG)
    config_path = os.path.join(config_dir, "concensus.local.md")
    if os.path.exists(config_path):
        with open(config_path, "r") as f:
            overrides = extract_frontmatter(f.read())
        config.update(overrides)
    return config


def should_skip_path(file_path: str, config: Dict[str, Any]) -> bool:
    basename = os.path.basename(file_path)
    for pattern in config.get("skip_paths", []):
        if fnmatch.fnmatch(basename, pattern):
            return True
        if fnmatch.fnmatch(file_path, pattern):
            return True
        if "/" in pattern:
            parts = file_path.replace("\\", "/").split("/")
            for i in range(len(parts)):
                suffix = "/".join(parts[i:])
                if fnmatch.fnmatch(suffix, pattern):
                    return True
    return False


def should_skip_change(content: str, config: Dict[str, Any]) -> bool:
    line_count = content.count("\n") + (1 if content and not content.endswith("\n") else 0)
    return line_count < config.get("min_change_lines", 5)
