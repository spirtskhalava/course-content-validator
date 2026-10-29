# Course Content Validator

[![CI](https://github.com/spirtskhalava/course-content-validator/actions/workflows/ci.yml/badge.svg)](https://github.com/spirtskhalava/course-content-validator/actions/workflows/ci.yml)

Automated QA for online course content. It catches the problems that usually reach
learners first: stale lessons, references to unsupported tool versions, broken links,
and quizzes whose answer key doesn't match the options.

It runs as a **CLI**, as a **GitHub Actions gate** (findings show up as PR annotations),
and as an **MCP server**, so an AI agent such as Claude Code can check content before
proposing a change.

```text
$ ccv examples/python-basics
error   lessons/02-variables.md:1  [metadata] Missing required field 'owner'
error   lessons/02-variables.md:9  [broken-link] Relative link target not found: exercises/variables.pdf
error   quizzes/02-variables.yaml  [quiz] Question q2: answer ['second'] is not one of the options
error   quizzes/02-variables.yaml  [quiz] Duplicate question id 'q2'
warning lessons/02-variables.md:1  [freshness] Content is stale: last reviewed 1022 days ago (limit 180)
warning lessons/02-variables.md:7  [outdated-version] python 3.7 in text is below supported minimum 3.10
...
3 files checked: 6 errors, 3 warnings
```

## Checks

| Check | Severity | What it catches |
|---|---|---|
| `front-matter` | error | Missing, unclosed, or invalid YAML front matter |
| `metadata` | error | Required fields missing (`title`, `last_reviewed`, `owner` by default) |
| `freshness` | warning | `last_reviewed` older than `max_age_days`, in the future, or not an ISO date (error) |
| `outdated-version` | warning | "Python 3.8", "node v16" etc. below the course's supported minimum, in text and code blocks |
| `broken-link` | error | Relative links/images that don't resolve; external URLs returning 4xx/5xx |
| `broken-link` | warning | External URLs that time out (could be flaky, so they don't block) |
| `quiz` | error | Answer not among options, duplicate ids/options, empty prompts, <2 options, missing lesson |

## Quick start

```bash
pip install -e ".[dev]"
ccv examples/python-basics                 # human-readable
ccv examples/python-basics --format json   # for dashboards / other tools
ccv path/to/course --check-links --fail-on warning
```

Exit codes: `0` clean, `1` findings at or above `--fail-on`, `2` usage/config error.

### Docker

```bash
docker build -t ccv .
docker run --rm -v "$PWD/examples:/content" ccv /content/python-basics
```

### As an MCP server (Claude Code)

```bash
pip install -e ".[mcp]"
claude mcp add course-validator -- ccv-mcp
```

Tools exposed: `validate_course(course_path, max_age_days?)` and
`list_stale_lessons(course_path, max_age_days)`.

### As a CI gate in a course repo

See [`.github/workflows/validate-content.yml.example`](.github/workflows/validate-content.yml.example).

## Course format

```
my-course/
  ccv.yaml                 # optional config
  lessons/01-setup.md      # Markdown with YAML front matter
  quizzes/01-setup.yaml    # questions + answer key
```

```yaml
# ccv.yaml
required_fields: [title, last_reviewed, owner]
max_age_days: 180
min_versions: { python: "3.10", node: "18" }
check_external_links: false
link_allowlist: ["https://internal.example.com"]
```

Unknown config keys are rejected, so a typo like `max_age_dayz` fails loudly instead
of silently using the default.

## Design

- [`docs/SPEC.md`](docs/SPEC.md): the requirements spec this tool was built from.
- [`docs/DECISIONS.md`](docs/DECISIONS.md): trade-offs and why they were made.

Each check is a pure function `(item, config) -> list[Finding]`. The network is injected
(`probe` parameter), so link checking is tested without real HTTP calls and the test
suite runs in under a second.

## Development

```bash
pip install -e ".[dev,mcp]"
pytest --cov=ccv
ruff check .
```

CI runs lint and tests on Python 3.10, 3.12 and 3.13, then builds the Docker image and
runs it against the example course.
