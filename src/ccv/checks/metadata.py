"""Required front-matter fields and freshness (last_reviewed date)."""

from __future__ import annotations

import datetime as dt

from ..config import Config
from ..models import Finding, Lesson, Severity


def check_required_fields(lesson: Lesson, cfg: Config) -> list[Finding]:
    missing = [f for f in cfg.required_fields if lesson.meta.get(f) in (None, "")]
    return [
        Finding("metadata", Severity.ERROR, str(lesson.path), f"Missing required field '{f}'", 1)
        for f in missing
    ]


def _to_date(value: object) -> dt.date | None:
    if isinstance(value, dt.datetime):
        return value.date()
    if isinstance(value, dt.date):
        return value
    if isinstance(value, str):
        try:
            return dt.date.fromisoformat(value)
        except ValueError:
            return None
    return None


def check_freshness(lesson: Lesson, cfg: Config, today: dt.date | None = None) -> list[Finding]:
    today = today or dt.date.today()
    raw = lesson.meta.get("last_reviewed")
    if raw is None:
        return []  # reported by check_required_fields when configured as required

    reviewed = _to_date(raw)
    if reviewed is None:
        return [Finding("freshness", Severity.ERROR, str(lesson.path),
                        f"last_reviewed '{raw}' is not an ISO date (YYYY-MM-DD)", 1)]
    if reviewed > today:
        return [Finding("freshness", Severity.WARNING, str(lesson.path),
                        f"last_reviewed {reviewed} is in the future", 1)]

    age = (today - reviewed).days
    if age > cfg.max_age_days:
        return [Finding("freshness", Severity.WARNING, str(lesson.path),
                        f"Content is stale: last reviewed {age} days ago (limit {cfg.max_age_days})", 1)]
    return []
