"""MCP server so an AI agent (e.g. Claude Code) can validate course content as a tool.

Run:  ccv-mcp            (stdio transport)
Register in Claude Code:
    claude mcp add course-validator -- ccv-mcp
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from mcp.server.mcpserver import MCPServer

from .config import Config
from .runner import validate_course

server = MCPServer(
    name="course-content-validator",
    instructions=(
        "Validates a folder of Markdown lessons and YAML quizzes. Use validate_course "
        "before publishing content, then fix errors first and warnings second."
    ),
)


@server.tool(name="validate_course")
def validate_course_tool(course_path: str, max_age_days: int | None = None) -> dict[str, Any]:
    """Validate a course folder. Returns a summary and a list of findings
    (check, severity, file, line, message). Does not request external URLs."""
    root = Path(course_path).expanduser()
    cfg = Config.load(root.resolve())
    if max_age_days is not None:
        cfg.max_age_days = max_age_days
    return validate_course(root, cfg).to_dict()


@server.tool()
def list_stale_lessons(course_path: str, max_age_days: int = 180) -> list[str]:
    """Return lesson files whose last_reviewed date is older than max_age_days."""
    root = Path(course_path).expanduser()
    cfg = Config.load(root.resolve())
    cfg.max_age_days = max_age_days
    report = validate_course(root, cfg)
    return sorted({f.file for f in report.findings if f.check == "freshness"})


def main() -> None:
    server.run("stdio")


if __name__ == "__main__":
    main()
