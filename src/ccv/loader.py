"""Load lessons (Markdown + YAML front matter) and quizzes (YAML) from a course folder."""

from __future__ import annotations

from pathlib import Path

import yaml

from .models import Finding, Lesson, Quiz, Severity

FRONT_MATTER_DELIM = "---"


def parse_lesson(path: Path) -> tuple[Lesson | None, list[Finding]]:
    text = path.read_text(encoding="utf-8")
    lines = text.splitlines()
    rel = str(path)

    if not lines or lines[0].strip() != FRONT_MATTER_DELIM:
        return Lesson(path, {}, text, 1), [
            Finding("front-matter", Severity.ERROR, rel, "Missing YAML front matter", 1)
        ]

    try:
        end = next(i for i, line in enumerate(lines[1:], start=1) if line.strip() == FRONT_MATTER_DELIM)
    except StopIteration:
        return None, [Finding("front-matter", Severity.ERROR, rel, "Front matter is not closed with '---'", 1)]

    try:
        meta = yaml.safe_load("\n".join(lines[1:end])) or {}
    except yaml.YAMLError as exc:
        return None, [Finding("front-matter", Severity.ERROR, rel, f"Invalid YAML: {exc}", 1)]

    if not isinstance(meta, dict):
        return None, [Finding("front-matter", Severity.ERROR, rel, "Front matter must be a mapping", 1)]

    body = "\n".join(lines[end + 1:])
    return Lesson(path, meta, body, end + 2), []


def parse_quiz(path: Path) -> tuple[Quiz | None, list[Finding]]:
    try:
        data = yaml.safe_load(path.read_text(encoding="utf-8"))
    except yaml.YAMLError as exc:
        return None, [Finding("quiz", Severity.ERROR, str(path), f"Invalid YAML: {exc}")]
    if not isinstance(data, dict):
        return None, [Finding("quiz", Severity.ERROR, str(path), "Quiz file must be a mapping")]
    return Quiz(path, data), []


def discover(course_root: Path) -> tuple[list[Path], list[Path]]:
    lessons = sorted(course_root.rglob("*.md"))
    quizzes = sorted(p for p in course_root.rglob("*.y*ml") if p.name != "ccv.yaml")
    # README files describe the repo, they are not lessons.
    lessons = [p for p in lessons if p.name.lower() != "readme.md"]
    return lessons, quizzes
