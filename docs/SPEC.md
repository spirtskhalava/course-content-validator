# Spec: Course Content Validator v0.1

**Status:** Implemented · **Owner:** Sandro · **Last updated:** 2026-10-28

## 1. Problem

Course content goes out of date without anyone noticing. Learners are usually the
first to find a dead link, a lesson that tells them to install a Python version we no
longer support, or a quiz question whose "correct" answer isn't one of the options.
Each of these costs a support ticket and some learner trust. Today, reviewers catch
them by reading, which doesn't scale and isn't repeatable.

## 2. Goal

Catch these problems automatically before content is published, in the same pull
request where they're introduced.

### Success criteria

- A pull request that adds any defect from section 4 fails CI with a message naming
  the file, line (where applicable), and problem.
- A course of 200 lessons validates in under 10 seconds without external link checks.
- No false positives on the example course's clean lesson (`01-setup.md`).

### Non-goals (v0.1)

- Checking factual accuracy of prose (needs an LLM or a human; candidate for v0.2).
- Auto-fixing problems.
- Formats other than Markdown lessons and YAML quizzes.

## 3. Users

| User | Need |
|---|---|
| Content author | Know what to fix before asking for review |
| Reviewer / QA | Trust that mechanical problems are already caught, focus on substance |
| Release manager | One pass/fail signal per course |
| AI agent (Claude Code via MCP) | A structured way to verify its own content edits |

## 4. Functional requirements

| ID | Requirement | Severity |
|---|---|---|
| FR-1 | Every lesson has YAML front matter with the configured required fields | error |
| FR-2 | `last_reviewed` is an ISO date; older than `max_age_days` → stale | warning (invalid date: error) |
| FR-3 | Mentions of a configured tool below its minimum version are flagged, in text and code blocks. Versions compare numerically (3.9 < 3.10) | warning |
| FR-4 | Relative links and images resolve to an existing file; in-page anchors and `mailto:` are ignored; links inside code fences are ignored | error |
| FR-5 | When enabled, each unique external URL is requested once. HTTP ≥ 400 → error. Timeout/network failure → warning | error / warning |
| FR-6 | Quiz: ≥ 1 question; unique ids; non-empty prompt; ≥ 2 unique options; answer key present and every answer is an option; linked lesson exists | error |
| FR-7 | Quiz where every option is marked correct | warning |
| FR-8 | Output formats: text, JSON, GitHub Actions annotations | — |
| FR-9 | Exit code 0/1/2 = clean / findings ≥ `--fail-on` / usage or config error | — |
| FR-10 | Unknown keys in `ccv.yaml` are a config error (exit 2) | — |

## 5. Acceptance examples

```gherkin
Given a lesson with last_reviewed: 2026-04-30 and max_age_days: 180
When validated on 2026-10-28
Then a "freshness" warning is reported (181 days)

Given min_versions: {python: "3.10"}
When a lesson says "Python 3.9"
Then an "outdated-version" warning is reported
And "Python 3.11" produces no finding

Given a quiz question with options [Tbilisi, Batumi] and answer Kutaisi
Then an error "answer ['Kutaisi'] is not one of the options" is reported
```

Every example above is an automated test in `tests/`.

## 6. Open questions

- Should stale content become an error N days after the warning? Proposed: configurable
  `max_age_days_error`, decide after one release cycle of data.
- Who owns the `min_versions` list per course? Proposed: the course `owner` field.
