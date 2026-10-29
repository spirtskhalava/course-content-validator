from pathlib import Path

import pytest

from ccv import Config
from ccv.checks.versions import check_versions
from ccv.models import Lesson

CFG = Config(min_versions={"python": "3.10", "node": "18"})


def run(body: str):
    return check_versions(Lesson(Path("l.md"), {}, body, body_start_line=10), CFG)


@pytest.mark.parametrize("text", ["Python 3.8", "python3.9", "Node.js 16", "node v14.2.0"])
def test_old_versions_flagged(text):
    assert len(run(f"Use {text} for this.")) == 1


@pytest.mark.parametrize("text", ["Python 3.10", "Python 3.12.1", "Node 20", "node v18.0.1"])
def test_supported_versions_pass(text):
    assert run(f"Use {text} for this.") == []


def test_compares_numerically_not_as_strings():
    # "3.9" > "3.10" as strings, but 3.9 < 3.10 as versions.
    assert len(run("Python 3.9")) == 1
    assert run("Python 3.11") == []


def test_line_numbers_point_into_file():
    findings = run("intro\n\nPython 3.7 here")
    assert findings[0].line == 12  # body starts at line 10, third line of body


def test_code_block_mentions_are_labeled():
    findings = run("```\npython3.8 -m venv .venv\n```")
    assert "code block" in findings[0].message
