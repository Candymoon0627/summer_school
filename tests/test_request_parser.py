from app.services.request_parser import LessonRequestParser


def test_parse_english_lesson_request() -> None:
    parsed = LessonRequestParser().parse("Grade 4 science water cycle, 45 minutes")

    assert parsed == {
        "subject": "science",
        "grade": 4,
        "topic": "water cycle",
        "missing": [],
    }


def test_parse_thai_lesson_request() -> None:
    parsed = LessonRequestParser().parse("ขอแผนการสอน ป.4 วิทยาศาสตร์ เรื่องวัฏจักรน้ำ")

    assert parsed == {
        "subject": "science",
        "grade": 4,
        "topic": "water cycle",
        "missing": [],
    }


def test_parse_chinese_lesson_request() -> None:
    parsed = LessonRequestParser().parse("四年级数学 分数")

    assert parsed == {
        "subject": "math",
        "grade": 4,
        "topic": "fractions",
        "missing": [],
    }
