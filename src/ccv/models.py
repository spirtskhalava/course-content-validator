"""Core data types shared by all checks."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any


class Severity(str, Enum):
    ERROR = "error"      # blocks a release
    WARNING = "warning"  # should be fixed, does not block
    INFO = "info"

    @property
    def rank(self) -> int:
        return {"error": 2, "warning": 1, "info": 0}[self.value]


@dataclass(frozen=True)
class Finding:
    check: str
    severity: Severity
    file: str
    message: str
    line: int | None = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["severity"] = self.severity.value
        return d


@dataclass
class Lesson:
    path: Path
    meta: dict[str, Any]
    body: str
    body_start_line: int  # 1-based line where the body starts (after front matter)


@dataclass
class Quiz:
    path: Path
    data: dict[str, Any]


@dataclass
class Report:
    findings: list[Finding] = field(default_factory=list)
    files_checked: int = 0

    def extend(self, items: list[Finding]) -> None:
        self.findings.extend(items)

    def count(self, severity: Severity) -> int:
        return sum(1 for f in self.findings if f.severity == severity)

    def has_blocking(self, fail_on: Severity = Severity.ERROR) -> bool:
        return any(f.severity.rank >= fail_on.rank for f in self.findings)

    def to_dict(self) -> dict[str, Any]:
        return {
            "files_checked": self.files_checked,
            "summary": {s.value: self.count(s) for s in Severity},
            "findings": [f.to_dict() for f in sorted(
                self.findings, key=lambda f: (-f.severity.rank, f.file, f.line or 0)
            )],
        }
