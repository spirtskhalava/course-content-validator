from ccv import Config, Severity, validate_course
from ccv.checks.links import check_external_links, extract_links
from ccv.loader import parse_lesson


def test_relative_links(course):
    course.lesson("b.md")
    course.lesson("a.md", body="""
        [ok](b.md) [ok with anchor](b.md#part) [same page](#top)
        [broken](missing.md) ![img](img/none.png)
        [ext](https://example.com) [mail](mailto:a@b.c)
    """)
    report = validate_course(course.root, Config())
    broken = sorted(f.message for f in report.findings if f.check == "broken-link")
    assert broken == [
        "Relative link target not found: img/none.png",
        "Relative link target not found: missing.md",
    ]


def test_links_inside_code_fences_are_ignored(course):
    path = course.lesson("a.md", body="```\n[x](nope.md)\n```\n")
    lesson, _ = parse_lesson(path)
    assert extract_links(lesson) == []


def test_external_links_deduplicated_and_classified(course):
    calls = []

    def fake_probe(url, timeout):
        calls.append(url)
        return {"https://ok.test": 200, "https://gone.test": 404}.get(url)  # others -> network error

    a = course.lesson("a.md", body="[x](https://ok.test) [y](https://gone.test) [z](https://down.test)")
    b = course.lesson("b.md", body="[x](https://gone.test) [i](https://internal.corp/page)")
    lessons = [parse_lesson(p)[0] for p in (a, b)]

    cfg = Config(link_allowlist=["https://internal.corp"])
    findings = check_external_links(lessons, cfg, probe=fake_probe)

    assert sorted(calls) == ["https://down.test", "https://gone.test", "https://ok.test"]  # once each
    by_sev = {(f.severity, f.message.split()[-1]) for f in findings}
    assert by_sev == {
        (Severity.ERROR, "https://gone.test"),    # 404: definitely broken
        (Severity.WARNING, "https://down.test"),  # network error: maybe flaky
    }
    assert sum("gone.test" in f.message for f in findings) == 2  # reported in both files


def test_external_links_off_by_default(course):
    course.lesson("a.md", body="[x](https://does-not-exist.invalid)")
    called = []
    validate_course(course.root, Config(), probe=lambda u, t: called.append(u))
    assert called == []
