import json

from ccv.cli import main


def test_example_course_end_to_end(example_course, capsys):
    code = main([str(example_course), "--format", "json"])
    out = json.loads(capsys.readouterr().out)

    assert code == 1  # the example course intentionally contains errors
    assert out["files_checked"] == 3
    checks = {(f["check"], f["file"]) for f in out["findings"]}
    assert ("metadata", "lessons/02-variables.md") in checks
    assert ("freshness", "lessons/02-variables.md") in checks
    assert ("outdated-version", "lessons/02-variables.md") in checks
    assert ("broken-link", "lessons/02-variables.md") in checks
    assert ("quiz", "quizzes/02-variables.yaml") in checks
    # 01-setup is clean apart from freshness, which depends on today's date.
    assert not any(f["file"] == "lessons/01-setup.md" and f["check"] != "freshness" for f in out["findings"])


def test_exit_code_respects_fail_on(course, capsys):
    course.lesson("a.md", last_reviewed="2020-01-01")  # stale -> warning only
    assert main([str(course.root)]) == 0
    assert main([str(course.root), "--fail-on", "warning"]) == 1


def test_github_annotations(course, capsys):
    course.lesson("a.md", body="[x](nope.md)\n")
    main([str(course.root), "--format", "github"])
    assert capsys.readouterr().out.strip() == (
        "::error file=lessons/a.md,line=6,title=broken-link::Relative link target not found: nope.md"
    )


def test_missing_folder_returns_2(tmp_path, capsys):
    assert main([str(tmp_path / "nope")]) == 2
