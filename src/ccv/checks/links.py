"""Link checks: relative links must resolve; external links optionally must respond."""

from __future__ import annotations

import re
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

from ..config import Config
from ..models import Finding, Lesson, Severity

# [text](target) and ![alt](target); ignores the optional "title" part.
MD_LINK = re.compile(r"!?\[[^\]]*\]\(\s*<?([^)\s>]+)>?(?:\s+\"[^\"]*\")?\s*\)")

# status_code or None on network failure
HttpProbe = Callable[[str, float], int | None]


def extract_links(lesson: Lesson) -> list[tuple[str, int]]:
    links: list[tuple[str, int]] = []
    in_fence = False
    for offset, line in enumerate(lesson.body.splitlines()):
        if line.lstrip().startswith("```"):
            in_fence = not in_fence
            continue
        if in_fence:
            continue
        for m in MD_LINK.finditer(line):
            links.append((m.group(1), lesson.body_start_line + offset))
    return links


def check_relative_links(lesson: Lesson) -> list[Finding]:
    findings = []
    for target, line in extract_links(lesson):
        if re.match(r"^[a-z][a-z0-9+.-]*:", target, re.IGNORECASE) or target.startswith("#"):
            continue  # external URL, mailto:, or in-page anchor
        file_part = target.split("#", 1)[0]
        resolved = (lesson.path.parent / file_part).resolve()
        if not resolved.exists():
            findings.append(Finding("broken-link", Severity.ERROR, str(lesson.path),
                                    f"Relative link target not found: {target}", line))
    return findings


def default_probe(url: str, timeout: float) -> int | None:
    headers = {"User-Agent": "course-content-validator/0.1"}
    try:
        r = requests.head(url, timeout=timeout, allow_redirects=True, headers=headers)
        if r.status_code in (403, 405):  # some servers reject HEAD; retry with GET
            r = requests.get(url, timeout=timeout, allow_redirects=True, headers=headers, stream=True)
        return r.status_code
    except requests.RequestException:
        return None


def check_external_links(
    lessons: list[Lesson], cfg: Config, probe: HttpProbe = default_probe
) -> list[Finding]:
    """Check every unique external URL once, in parallel."""
    occurrences: dict[str, list[tuple[Path, int]]] = {}
    for lesson in lessons:
        for target, line in extract_links(lesson):
            if not target.startswith(("http://", "https://")):
                continue
            if any(target.startswith(p) for p in cfg.link_allowlist):
                continue
            occurrences.setdefault(target, []).append((lesson.path, line))

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = pool.map(lambda u: probe(u, cfg.link_timeout_seconds), occurrences)
        statuses = dict(zip(occurrences, results, strict=True))

    findings = []
    for url, status in statuses.items():
        if status is not None and status < 400:
            continue
        # Network errors are warnings (could be flaky); a 4xx/5xx answer is a real break.
        sev = Severity.WARNING if status is None else Severity.ERROR
        msg = f"External link unreachable: {url}" if status is None else f"External link returned HTTP {status}: {url}"
        for path, line in occurrences[url]:
            findings.append(Finding("broken-link", sev, str(path), msg, line))
    return findings
