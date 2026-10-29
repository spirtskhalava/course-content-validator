"""Flag mentions of tool versions older than the course's supported minimum.

Example: with min_versions = {"python": "3.10"}, the text "install Python 3.8"
produces a warning, while "Python 3.12" passes.
"""

from __future__ import annotations

import re

from ..config import Config
from ..models import Finding, Lesson, Severity


def _parse(version: str) -> tuple[int, ...]:
    return tuple(int(p) for p in version.split("."))


def _pattern(tool: str) -> re.Pattern[str]:
    # "Python 3.8", "python3.8", "Node.js 16", "node v18.2"
    return re.compile(rf"\b{re.escape(tool)}(?:\.js)?\s*v?(\d+(?:\.\d+){{0,2}})\b", re.IGNORECASE)


def check_versions(lesson: Lesson, cfg: Config) -> list[Finding]:
    findings: list[Finding] = []
    in_fence = False
    for offset, line in enumerate(lesson.body.splitlines()):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
        for tool, minimum in cfg.min_versions.items():
            min_v = _parse(str(minimum))
            for m in _pattern(tool).finditer(line):
                found = _parse(m.group(1))
                # Compare only as many components as the minimum specifies.
                if found[: len(min_v)] < min_v:
                    where = "code block" if in_fence else "text"
                    findings.append(Finding(
                        "outdated-version", Severity.WARNING, str(lesson.path),
                        f"{tool} {m.group(1)} in {where} is below supported minimum {minimum}",
                        lesson.body_start_line + offset,
                    ))
    return findings
