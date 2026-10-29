import datetime as dt
from pathlib import Path

import pytest

from ccv import Config, Severity, validate_course
from ccv.checks.metadata import check_freshness
from ccv.models import Lesson

TODAY = dt.date(2026, 10, 28)


def _lesson(**meta):
    return Lesson(path=Path("x.md"), meta=meta, body="", body_start_line=5)


def test_missing_required_field_is_error(course):
    course.lesson("a.md", owner=None)
    report = validate_course(course.root, Config(), today=TODAY)
    assert [(f.check, f.severity, f.message) for f in report.findings] == [
        ("metadata", Severity.ERROR, "Missing required field 'owner'")
    ]


def test_missing_front_matter(course):
    course.write("lessons/raw.md", "# no front matter\n")
    report = validate_course(course.root, Config(), today=TODAY)
    assert report.findings[0].message == "Missing YAML front matter"


def test_unclosed_front_matter(course):
    course.write("lessons/raw.md", "---\ntitle: x\n# body\n")
    report = validate_course(course.root, Config(), today=TODAY)
    assert "not closed" in report.findings[0].message


@pytest.mark.parametrize(
    "reviewed, expected",
    [
        (dt.date(2026, 10, 1), None),             # fresh
        (dt.date(2026, 5, 1), None),              # exactly 180 days -> still ok
        (dt.date(2026, 4, 30), Severity.WARNING), # 181 days -> stale
        (dt.date(2027, 1, 1), Severity.WARNING),  # future date
        ("10/01/2026", Severity.ERROR),           # not ISO
    ],
)
def test_freshness_boundaries(reviewed, expected):
    findings = check_freshness(_lesson(last_reviewed=reviewed), Config(max_age_days=180), TODAY)
    assert (findings[0].severity if findings else None) == expected


def test_yaml_dates_and_strings_are_both_accepted():
    assert check_freshness(_lesson(last_reviewed="2026-10-01"), Config(), TODAY) == []
    assert check_freshness(_lesson(last_reviewed=dt.date(2026, 10, 1)), Config(), TODAY) == []


def test_readme_is_not_treated_as_lesson(course):
    course.write("README.md", "# About this course\n")
    assert validate_course(course.root, Config(), today=TODAY).findings == []


def test_unknown_config_key_is_rejected(course):
    course.write("ccv.yaml", "max_age_dayz: 10\n")
    with pytest.raises(ValueError, match="max_age_dayz"):
        Config.load(course.root)
