from __future__ import annotations

import textwrap
from pathlib import Path

import pytest


class CourseBuilder:
    """Builds a throwaway course folder so each test states exactly what it needs."""

    def __init__(self, root: Path):
        self.root = root

    def lesson(self, name: str, body: str = "# Lesson\n", **meta: object) -> Path:
        meta = {"title": "T", "last_reviewed": "2026-10-01", "owner": "qa", **meta}
        fm = "\n".join(f"{k}: {v}" for k, v in meta.items() if v is not None)
        return self.write(f"lessons/{name}", f"---\n{fm}\n---\n{textwrap.dedent(body)}")

    def write(self, rel: str, content: str) -> Path:
        path = self.root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(textwrap.dedent(content), encoding="utf-8")
        return path


@pytest.fixture
def course(tmp_path: Path) -> CourseBuilder:
    return CourseBuilder(tmp_path)


EXAMPLE_COURSE = Path(__file__).resolve().parent.parent / "examples" / "python-basics"


@pytest.fixture
def example_course() -> Path:
    return EXAMPLE_COURSE
