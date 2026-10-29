"""Orchestrates discovery, parsing and all checks for one course folder."""

from __future__ import annotations

import datetime as dt
from pathlib import Path

from . import checks
from .checks.links import HttpProbe, default_probe
from .config import Config
from .loader import discover, parse_lesson, parse_quiz
from .models import Report


def validate_course(
    course_root: Path,
    cfg: Config | None = None,
    *,
    today: dt.date | None = None,
    probe: HttpProbe = default_probe,
) -> Report:
    course_root = course_root.resolve()
    if not course_root.is_dir():
        raise FileNotFoundError(f"Course folder not found: {course_root}")
    cfg = cfg or Config.load(course_root)
    report = Report()

    lesson_paths, quiz_paths = discover(course_root)
    lessons = []
    for path in lesson_paths:
        lesson, errors = parse_lesson(path)
        report.extend(errors)
        if lesson is None:
            continue
        lessons.append(lesson)
        report.extend(checks.check_required_fields(lesson, cfg))
        report.extend(checks.check_freshness(lesson, cfg, today))
        report.extend(checks.check_versions(lesson, cfg))
        report.extend(checks.check_relative_links(lesson))

    if cfg.check_external_links:
        report.extend(checks.check_external_links(lessons, cfg, probe))

    for path in quiz_paths:
        quiz, errors = parse_quiz(path)
        report.extend(errors)
        if quiz is not None:
            report.extend(checks.check_quiz(quiz, course_root))

    report.files_checked = len(lesson_paths) + len(quiz_paths)
    # Report paths relative to the course root: stable across machines and CI.
    report.findings = [
        type(f)(f.check, f.severity, _rel(f.file, course_root), f.message, f.line)
        for f in report.findings
    ]
    return report


def _rel(file: str, root: Path) -> str:
    try:
        return str(Path(file).resolve().relative_to(root))
    except ValueError:
        return file
