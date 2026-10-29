"""Command line entry point: `ccv path/to/course`."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .config import Config
from .models import Report, Severity
from .runner import validate_course

COLORS = {Severity.ERROR: "\033[31m", Severity.WARNING: "\033[33m", Severity.INFO: "\033[36m"}
RESET = "\033[0m"


def format_text(report: Report, color: bool) -> str:
    lines = []
    for f in report.to_dict()["findings"]:
        sev = Severity(f["severity"])
        tag = f"{COLORS[sev]}{sev.value:<7}{RESET}" if color else f"{sev.value:<7}"
        loc = f"{f['file']}:{f['line']}" if f["line"] else f["file"]
        lines.append(f"{tag} {loc}  [{f['check']}] {f['message']}")
    s = report.to_dict()["summary"]
    lines.append(
        f"\n{report.files_checked} files checked: "
        f"{s['error']} errors, {s['warning']} warnings"
    )
    return "\n".join(lines)


def format_github(report: Report) -> str:
    """GitHub Actions workflow commands: findings show up as PR annotations."""
    out = []
    for f in report.findings:
        kind = {"error": "error", "warning": "warning", "info": "notice"}[f.severity.value]
        line = f",line={f.line}" if f.line else ""
        out.append(f"::{kind} file={f.file}{line},title={f.check}::{f.message}")
    return "\n".join(out)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="ccv", description="Validate course content for accuracy and freshness.")
    p.add_argument("course", type=Path, help="Path to the course folder")
    p.add_argument("--format", choices=["text", "json", "github"], default="text")
    p.add_argument("--fail-on", choices=["error", "warning"], default="error",
                   help="Lowest severity that makes the command exit with code 1")
    p.add_argument("--check-links", action="store_true", help="Also request external URLs")
    p.add_argument("--max-age-days", type=int, help="Override the staleness threshold")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        cfg = Config.load(args.course.resolve())
    except ValueError as exc:
        print(f"Config error: {exc}", file=sys.stderr)
        return 2
    if args.check_links:
        cfg.check_external_links = True
    if args.max_age_days is not None:
        cfg.max_age_days = args.max_age_days

    try:
        report = validate_course(args.course, cfg)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(report.to_dict(), indent=2))
    elif args.format == "github":
        print(format_github(report))
    else:
        print(format_text(report, color=sys.stdout.isatty()))

    return 1 if report.has_blocking(Severity(args.fail_on)) else 0


if __name__ == "__main__":
    raise SystemExit(main())
