import os
import sys
import tempfile
import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from core.config import load_config, DEFAULT_CONFIG


def test_default_config_when_no_file():
    config = load_config(config_dir="/nonexistent")
    assert config["enabled"] is True
    assert config["min_change_lines"] == 5
    assert config["debate_rounds"] == 2
    assert "gemini" in config["models"]
    assert "codex" in config["models"]
    assert "*.md" in config["skip_paths"]


def test_load_config_from_file():
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = os.path.join(tmpdir, "concensus.local.md")
        with open(config_path, "w") as f:
            f.write("---\nenabled: false\nmin_change_lines: 10\n---\n")
        config = load_config(config_dir=tmpdir)
        assert config["enabled"] is False
        assert config["min_change_lines"] == 10
        assert config["debate_rounds"] == 2  # default preserved


def test_skip_paths_matching():
    from core.config import should_skip_path
    config = load_config(config_dir="/nonexistent")
    assert should_skip_path("README.md", config) is True
    assert should_skip_path("package.json", config) is True
    assert should_skip_path("node_modules/foo/bar.js", config) is True
    assert should_skip_path("src/main.py", config) is False
    assert should_skip_path("/project/src/README.md", config) is True
    assert should_skip_path("/project/node_modules/foo/bar.js", config) is True
    assert should_skip_path("/project/src/main.py", config) is False


def test_min_change_lines_filter():
    from core.config import should_skip_change
    config = load_config(config_dir="/nonexistent")
    assert should_skip_change("a\nb\nc", config) is True   # 3 lines < 5
    assert should_skip_change("a\nb\nc\nd\ne\nf", config) is False  # 6 lines >= 5
