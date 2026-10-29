from ccv import Config, validate_course


def quiz_messages(course):
    report = validate_course(course.root, Config())
    return sorted(f.message for f in report.findings if f.check == "quiz")


def test_valid_quiz_has_no_findings(course):
    course.lesson("01.md")
    course.write("quizzes/01.yaml", """
        lesson: lessons/01.md
        questions:
          - id: q1
            prompt: "2 + 2?"
            options: [3, 4]
            answer: 4
          - id: q2
            prompt: "Pick even numbers"
            options: [1, 2, 4]
            answer: [2, 4]
    """)
    assert quiz_messages(course) == []


def test_answer_key_problems(course):
    course.write("quizzes/bad.yaml", """
        lesson: lessons/ghost.md
        questions:
          - id: q1
            prompt: "Capital of Georgia?"
            options: [Tbilisi, Batumi]
            answer: Kutaisi
          - id: q1
            prompt: ""
            options: [only]
          - id: q3
            prompt: "All?"
            options: [a, a]
            answer: [a, a]
    """)
    assert quiz_messages(course) == sorted([
        "Linked lesson not found: lessons/ghost.md",
        "Question q1: answer ['Kutaisi'] is not one of the options",
        "Duplicate question id 'q1'",
        "Question q1 has an empty prompt",
        "Question q1 needs at least 2 options",
        "Question q1 has no answer key",
        "Question q3 has duplicate options",
        "Question q3: every option is marked correct",
    ])


def test_invalid_yaml(course):
    course.write("quizzes/broken.yaml", "questions: [unclosed\n")
    assert quiz_messages(course)[0].startswith("Invalid YAML")


def test_empty_quiz(course):
    course.write("quizzes/empty.yaml", "lesson: null\nquestions: []\n")
    assert quiz_messages(course) == ["Quiz has no questions"]
