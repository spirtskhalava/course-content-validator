"""Quiz integrity: every question is answerable and the answer key is consistent.

Expected quiz format:

    lesson: lessons/01-intro.md
    questions:
      - id: q1
        prompt: "What does `len([1, 2])` return?"
        options: ["1", "2", "3"]
        answer: "2"            # single choice, or a list for multi-select
"""

from __future__ import annotations

from pathlib import Path

from ..models import Finding, Quiz, Severity


def check_quiz(quiz: Quiz, course_root: Path | None = None) -> list[Finding]:
    """`lesson:` paths are resolved relative to the course root."""
    path = str(quiz.path)
    out: list[Finding] = []

    def err(msg: str) -> None:
        out.append(Finding("quiz", Severity.ERROR, path, msg))

    lesson_ref = quiz.data.get("lesson")
    root = course_root or quiz.path.parent
    if lesson_ref and not (root / lesson_ref).exists():
        err(f"Linked lesson not found: {lesson_ref}")

    questions = quiz.data.get("questions")
    if not isinstance(questions, list) or not questions:
        err("Quiz has no questions")
        return out

    seen_ids: set[str] = set()
    for idx, q in enumerate(questions, start=1):
        qid = str(q.get("id", f"#{idx}")) if isinstance(q, dict) else f"#{idx}"
        if not isinstance(q, dict):
            err(f"Question {qid} must be a mapping")
            continue
        if qid in seen_ids:
            err(f"Duplicate question id '{qid}'")
        seen_ids.add(qid)

        if not str(q.get("prompt", "")).strip():
            err(f"Question {qid} has an empty prompt")

        options = q.get("options") or []
        if len(options) < 2:
            err(f"Question {qid} needs at least 2 options")
        if len(set(map(str, options))) != len(options):
            err(f"Question {qid} has duplicate options")

        answer = q.get("answer")
        answers = answer if isinstance(answer, list) else [answer]
        if answer is None or answers == []:
            err(f"Question {qid} has no answer key")
            continue
        not_in_options = [a for a in answers if str(a) not in map(str, options)]
        if not_in_options:
            err(f"Question {qid}: answer {not_in_options} is not one of the options")
        if len(answers) == len(options) and len(options) > 1:
            out.append(Finding("quiz", Severity.WARNING, path,
                               f"Question {qid}: every option is marked correct"))
    return out
