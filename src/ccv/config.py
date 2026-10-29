"""Validator configuration, loaded from `ccv.yaml` in the course root (optional)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


@dataclass
class Config:
    required_fields: list[str] = field(
        default_factory=lambda: ["title", "last_reviewed", "owner"]
    )
    # Content not reviewed within this many days is flagged as stale.
    max_age_days: int = 180
    # Minimum supported versions, e.g. {"python": "3.10"}. Mentions of older
    # versions in lesson text ("Python 3.7") are reported as outdated.
    min_versions: dict[str, str] = field(default_factory=dict)
    check_external_links: bool = False
    link_timeout_seconds: float = 5.0
    # URL prefixes that are never requested (e.g. internal hosts, rate-limited sites).
    link_allowlist: list[str] = field(default_factory=list)

    @classmethod
    def load(cls, course_root: Path) -> Config:
        path = course_root / "ccv.yaml"
        if not path.exists():
            return cls()
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        known = {k: v for k, v in raw.items() if k in cls.__dataclass_fields__}
        unknown = set(raw) - set(known)
        if unknown:
            raise ValueError(f"Unknown keys in {path}: {sorted(unknown)}")
        return cls(**known)
