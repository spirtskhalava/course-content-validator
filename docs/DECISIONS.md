# Design decisions

Short records of the trade-offs behind this tool: what was chosen, what was given up.

## D1. Network failures are warnings, HTTP errors are errors

**Context.** External link checks in CI are a classic source of flaky builds: a site
is slow for 30 seconds and every content PR goes red.

**Decision.** A URL that answers 4xx/5xx is an error (it's definitely broken).
A timeout or connection failure is a warning. External checks are off by default and
enabled with `--check-links`.

**Trade-off.** A site that is permanently down but times out instead of returning
an error only gets a warning. Accepted: a scheduled nightly run with
`--fail-on warning` catches it without blocking authors' PRs.

## D2. Check external URLs once, in parallel

Courses link the same docs pages from many lessons. URLs are deduplicated and
checked with a thread pool of 8, then the result is reported at every occurrence.
This keeps the run proportional to unique URLs, not links, and limits load on
third-party sites.

## D3. Injected HTTP probe instead of mocking `requests`

`check_external_links` takes a `probe(url, timeout) -> status | None` function.
Tests pass a fake probe. This avoids patching library internals, keeps tests fast and
deterministic, and makes it easy to swap in a cached probe later.

## D4. Regex version detection, not an LLM

**Decision.** Version mentions are found with a regex per configured tool.

**Trade-off.** It misses phrasing like "the 3.8 release" without the tool name, and
`pyenv install 3.8.10` isn't flagged. In exchange, it is deterministic, free, offline,
and has no false positives on unrelated numbers. Prose accuracy checks are a v0.2
candidate where an LLM (via the MCP server) is a better fit.

## D5. Strict config

Unknown keys in `ccv.yaml` fail the run. A silently ignored typo (`max_age_dayz`)
means the course runs with defaults while the author believes otherwise, which is
worse than a loud error.

## D6. Paths relative to the course root in all output

Findings report `lessons/02-variables.md`, not `/home/runner/work/...`. Output is
stable across machines, diffable, and GitHub annotations attach to the right file.
