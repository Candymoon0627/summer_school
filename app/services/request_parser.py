import re
from typing import ClassVar


class LessonRequestParser:
    subject_aliases: ClassVar[dict[str, list[str]]] = {
        "math": [
            "math",
            "mathematics",
            "คณิตศาสตร์",
            "คณิต",
            "เลข",
            "数学",
            "數學",
        ],
        "science": [
            "science",
            "วิทยาศาสตร์",
            "วิทยา",
            "科学",
            "科學",
        ],
    }
    thai_grade_words: ClassVar[dict[str, int]] = {
        "หนึ่ง": 1,
        "สอง": 2,
        "สาม": 3,
        "สี่": 4,
        "ห้า": 5,
        "หก": 6,
    }
    chinese_grade_words: ClassVar[dict[str, int]] = {
        "一年级": 1,
        "二年级": 2,
        "三年级": 3,
        "四年级": 4,
        "五年级": 5,
        "六年级": 6,
    }
    topic_aliases: ClassVar[dict[str, list[str]]] = {
        "fractions": ["fractions", "fraction", "เศษส่วน", "分数", "分數"],
        "equivalent fractions": ["equivalent fractions", "เศษส่วนที่เท่ากัน"],
        "water cycle": ["water cycle", "วัฏจักรน้ำ", "วงจรน้ำ", "水循环", "水循環"],
        "evaporation": ["evaporation", "การระเหย"],
        "plant parts": ["plant parts", "ส่วนของพืช"],
        "forces": ["forces", "แรง"],
        "area": ["area", "พื้นที่"],
        "perimeter": ["perimeter", "เส้นรอบรูป"],
    }

    def parse(self, text: str) -> dict:
        subject = self._parse_subject(text)
        grade = self._parse_grade(text)
        topic = self._parse_topic(text, subject, grade)
        missing = []
        if not subject:
            missing.append("subject")
        if not grade:
            missing.append("grade")
        if not topic:
            missing.append("topic")
        return {"subject": subject, "grade": grade, "topic": topic, "missing": missing}

    def _parse_subject(self, text: str) -> str | None:
        lowered = text.lower()
        for subject, aliases in self.subject_aliases.items():
            if any(alias.lower() in lowered for alias in aliases):
                return subject
        return None

    def _parse_grade(self, text: str) -> int | None:
        patterns = [
            r"\bgrade\s*(\d{1,2})\b",
            r"\bg\s*(\d{1,2})\b",
            r"\bp\s*(\d{1,2})\b",
            r"ป\.?\s*(\d{1,2})",
            r"ประถม(?:ศึกษา)?(?:ปีที่)?\s*(\d{1,2})",
            r"ชั้น(?:ประถม(?:ศึกษา)?)?(?:ปีที่)?\s*(\d{1,2})",
            r"(\d{1,2})\s*年级",
        ]
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                grade = int(match.group(1))
                if 1 <= grade <= 12:
                    return grade

        for word, grade in self.thai_grade_words.items():
            if f"ป.{word}" in text or f"ปีที่{word}" in text or f"ประถม{word}" in text:
                return grade
        for word, grade in self.chinese_grade_words.items():
            if word in text:
                return grade
        return None

    def _parse_topic(self, text: str, subject: str | None, grade: int | None) -> str | None:
        lowered = text.lower()
        for topic, aliases in self.topic_aliases.items():
            if any(alias.lower() in lowered for alias in aliases):
                return topic

        cleaned = self._remove_known_parts(text, subject)
        del grade
        cleaned = cleaned.strip(" ,，。:：;；-/|")
        return cleaned or None

    def _remove_known_parts(self, text: str, subject: str | None) -> str:
        cleaned = text
        patterns = [
            r"\bgrade\s*\d{1,2}\b",
            r"\bg\s*\d{1,2}\b",
            r"\bp\s*\d{1,2}\b",
            r"ป\.?\s*\d{1,2}",
            r"ประถม(?:ศึกษา)?(?:ปีที่)?\s*\d{1,2}",
            r"ชั้น(?:ประถม(?:ศึกษา)?)?(?:ปีที่)?\s*\d{1,2}",
            r"\d{1,2}\s*年级",
            r"\d+\s*(?:minutes?|mins?|นาที)",
            r"low-resource classroom",
            r"low resource classroom",
        ]
        for pattern in patterns:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE)
        for word in list(self.thai_grade_words) + list(self.chinese_grade_words):
            cleaned = cleaned.replace(word, "")
        if subject:
            for alias in self.subject_aliases.get(subject, []):
                cleaned = re.sub(re.escape(alias), "", cleaned, flags=re.IGNORECASE)
        return re.sub(r"\s+", " ", cleaned)
