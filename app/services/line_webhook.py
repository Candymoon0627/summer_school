import hashlib
import json

from sqlalchemy.orm import Session

from app.repositories.lesson import LessonRepository
from app.repositories.line import LineEventRepository
from app.repositories.org import OrgRepository
from app.services.language import (
    DEFAULT_LANGUAGE,
    detect_language_selection,
    is_change_language_command,
    normalize_language,
    normalize_menu_command,
)
from app.services.language import (
    text as localized_text,
)
from app.services.lesson_requests import LessonRequestService
from app.services.line_messaging import LineMessagingService
from app.services.onboarding import OnboardingService
from app.services.submissions import SubmissionService, detect_submission_text

LESSON_FLOW_PREFIX = "line_lesson_flow:"
GRADE_CHOICES = (1, 2, 3, 4, 5, 6)
SUBJECT_CHOICES = ("math", "science")

LESSON_FLOW_TEXT = {
    "choose_grade": {
        "th": "เลือกชั้นเรียน",
        "ms": "Pilih darjah.",
        "en": "Choose a grade.",
    },
    "choose_subject": {
        "th": "เลือกวิชา",
        "ms": "Pilih subjek.",
        "en": "Choose a subject.",
    },
    "enter_topic": {
        "th": "พิมพ์หัวข้อที่ต้องการสร้างแผนสอน",
        "ms": "Taip topik untuk rancangan mengajar.",
        "en": "Type the topic for the lesson plan.",
    },
    "submission_format": {
        "th": "รูปแบบการส่งข้อความ:\nsubmit: เนื้อหาความรู้ท้องถิ่นของคุณ",
        "ms": "Format hantaran:\nsubmit: kandungan ilmu tempatan anda",
        "en": "Submission format:\nsubmit: your local knowledge content",
    },
    "submission_example": {
        "th": "ตัวอย่าง:\nsubmit: Use a local market example for measuring weight.",
        "ms": "Contoh:\nsubmit: Use a local market example for measuring weight.",
        "en": "Example:\nsubmit: Use a local market example for measuring weight.",
    },
    "submission_start": {
        "th": "พิมพ์ข้อความใหม่โดยขึ้นต้นด้วย submit: แล้วตามด้วยเนื้อหา",
        "ms": "Taip mesej baru bermula dengan submit: diikuti kandungan.",
        "en": "Send a new message starting with submit: followed by your content.",
    },
}

SUBJECT_LABELS = {
    "math": {"th": "คณิตศาสตร์", "ms": "Matematik", "en": "Math"},
    "science": {"th": "วิทยาศาสตร์", "ms": "Sains", "en": "Science"},
}


class LineWebhookService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.events = LineEventRepository(db)
        self.lessons = LessonRepository(db)
        self.orgs = OrgRepository(db)
        self.messages = LineMessagingService()

    def handle_payload(self, payload: dict) -> dict:
        handled = 0
        skipped = 0
        for event in payload.get("events", []):
            if self._handle_event(event):
                handled += 1
            else:
                skipped += 1
        return {"handled": handled, "skipped": skipped}

    def _handle_event(self, event: dict) -> bool:
        event_key = self._event_key(event)
        source = event.get("source") or {}
        message = event.get("message") or {}
        line_user_id = source.get("userId")
        message_id = message.get("id")
        event_type = event.get("type", "unknown")
        is_new = self.events.mark_received(
            event_key=event_key,
            line_user_id=line_user_id,
            message_id=message_id,
            event_type=event_type,
        )
        if not is_new:
            return False

        if event_type != "message":
            return True
        reply_token = event.get("replyToken")
        message_type = message.get("type")

        if message_type == "text":
            self._handle_text(
                line_user_id=line_user_id,
                reply_token=reply_token,
                text=message.get("text", ""),
                message_id=message_id,
            )
            return True

        language = self._language_for_line_user(line_user_id)
        if message_type in {"image", "file"}:
            self.messages.reply_text(
                reply_token or "",
                localized_text("image_under_development", language),
            )
            return True

        self.messages.reply_text(
            reply_token or "",
            localized_text("unsupported_message_type", language),
        )
        return True

    def _handle_text(
        self,
        *,
        line_user_id: str | None,
        reply_token: str | None,
        text: str,
        message_id: str | None = None,
    ) -> None:
        if not line_user_id:
            return

        teacher = self.orgs.get_teacher_by_line_user_id(line_user_id)
        language = normalize_language(teacher.language_preference if teacher else DEFAULT_LANGUAGE)

        language_selection = detect_language_selection(text)
        if teacher and language_selection:
            self.orgs.update_teacher_language(teacher, language_selection)
            self.db.commit()
            self.messages.link_rich_menu_for_language(line_user_id, language_selection)
            self.messages.reply_text(
                reply_token or "",
                localized_text("language_changed", language_selection),
            )
            return

        if is_change_language_command(text):
            self.messages.reply_language_choices(
                reply_token or "",
                localized_text("choose_language", language),
            )
            return

        if not teacher:
            bound = OnboardingService(self.db).bind_teacher_by_school_code(
                line_user_id=line_user_id,
                school_code=text,
            )
            if not bound:
                self.messages.reply_text(
                    reply_token or "",
                    localized_text("invalid_school_code", language),
                )
                return
            self.messages.reply_text(
                reply_token or "",
                localized_text("bound_to_school", language, school_name=bound.school_name),
            )
            return

        if self._handle_lesson_flow_command(
            teacher=teacher,
            reply_token=reply_token,
            text=text,
            language=language,
        ):
            return

        menu_command = normalize_menu_command(text)
        if menu_command:
            self._handle_menu_command(
                teacher=teacher,
                reply_token=reply_token,
                command=menu_command,
            )
            return

        if self._handle_submission_helper_command(
            reply_token=reply_token,
            text=text,
            language=language,
        ):
            return

        if self._handle_pending_lesson_topic(
            teacher=teacher,
            line_user_id=line_user_id,
            reply_token=reply_token,
            topic=text,
            language=language,
        ):
            return

        submission_match = detect_submission_text(text)
        if submission_match.is_submission:
            if not submission_match.body:
                self.messages.reply_text(
                    reply_token or "",
                    localized_text("missing_submission_body", language),
                )
                return
            submission = SubmissionService(self.db).create_line_text_submission(
                line_user_id=line_user_id,
                text=text,
                source_message_id=message_id,
            )
            self.messages.reply_text(
                reply_token or "",
                localized_text("submission_received", language, submission_id=submission.id),
            )
            return

        result = LessonRequestService(self.db).create_from_teacher_text(
            line_user_id=line_user_id,
            text=text,
            enqueue=True,
            language=language,
        )
        self.messages.reply_text(reply_token or "", result["message"])

    def _handle_menu_command(self, *, teacher, reply_token: str | None, command: str) -> None:
        language = normalize_language(teacher.language_preference)
        if command == "history":
            self.messages.reply_text(
                reply_token or "",
                self._history_message(teacher_id=teacher.id, language=language),
            )
            return

        message_key = {
            "lesson": "lesson",
            "submit_text": "submit_text",
            "submit_image": "submit_image",
            "ai_experience": "ai_experience",
            "help": "help",
        }.get(command)
        if message_key:
            self.messages.reply_menu_card(
                reply_token or "",
                command=message_key,
                language=language,
            )

    def _handle_lesson_flow_command(
        self,
        *,
        teacher,
        reply_token: str | None,
        text: str,
        language: str,
    ) -> bool:
        normalized = text.strip().casefold()
        if normalized == "/lesson_choose_grade":
            self._clear_lesson_flow(teacher)
            self.db.commit()
            self._reply_grade_choices(reply_token=reply_token, language=language)
            return True

        if normalized.startswith("/lesson_grade_"):
            grade = self._parse_grade_command(normalized)
            if not grade:
                self._reply_grade_choices(reply_token=reply_token, language=language)
                return True
            self._set_lesson_flow(teacher, {"step": "subject", "grade": grade})
            self.db.commit()
            self._reply_subject_choices(reply_token=reply_token, language=language)
            return True

        if normalized.startswith("/lesson_subject_"):
            subject = normalized.removeprefix("/lesson_subject_")
            if subject not in SUBJECT_CHOICES:
                self._reply_subject_choices(reply_token=reply_token, language=language)
                return True
            state = self._lesson_flow_state(teacher)
            grade = state.get("grade")
            if not grade:
                self._set_lesson_flow(teacher, {"step": "grade"})
                self.db.commit()
                self._reply_grade_choices(reply_token=reply_token, language=language)
                return True
            self._set_lesson_flow(teacher, {"step": "topic", "grade": grade, "subject": subject})
            self.db.commit()
            self.messages.reply_text(
                reply_token or "",
                LESSON_FLOW_TEXT["enter_topic"][normalize_language(language)],
            )
            return True

        return False

    def _handle_submission_helper_command(
        self,
        *,
        reply_token: str | None,
        text: str,
        language: str,
    ) -> bool:
        normalized = text.strip().casefold()
        key = {
            "/submission_format": "submission_format",
            "/submission_example": "submission_example",
            "/submission_start": "submission_start",
        }.get(normalized)
        if not key:
            return False
        self.messages.reply_text(reply_token or "", LESSON_FLOW_TEXT[key][normalize_language(language)])
        return True

    def _handle_pending_lesson_topic(
        self,
        *,
        teacher,
        line_user_id: str,
        reply_token: str | None,
        topic: str,
        language: str,
    ) -> bool:
        state = self._lesson_flow_state(teacher)
        if state.get("step") != "topic" or not state.get("grade") or not state.get("subject"):
            return False
        lesson_text = f"Grade {state['grade']} {state['subject']} {topic}"
        self._clear_lesson_flow(teacher)
        self.db.commit()
        result = LessonRequestService(self.db).create_from_teacher_text(
            line_user_id=line_user_id,
            text=lesson_text,
            enqueue=True,
            language=language,
        )
        self.messages.reply_text(reply_token or "", result["message"])
        return True

    def _reply_grade_choices(self, *, reply_token: str | None, language: str) -> None:
        items = [(f"G{grade}", f"/lesson_grade_{grade}") for grade in GRADE_CHOICES]
        self.messages.reply_text(
            reply_token or "",
            LESSON_FLOW_TEXT["choose_grade"][normalize_language(language)],
            quick_reply_items=self.messages.message_quick_reply_items(items),
        )

    def _reply_subject_choices(self, *, reply_token: str | None, language: str) -> None:
        selected_language = normalize_language(language)
        items = [
            (SUBJECT_LABELS[subject][selected_language], f"/lesson_subject_{subject}")
            for subject in SUBJECT_CHOICES
        ]
        self.messages.reply_text(
            reply_token or "",
            LESSON_FLOW_TEXT["choose_subject"][selected_language],
            quick_reply_items=self.messages.message_quick_reply_items(items),
        )

    def _parse_grade_command(self, normalized: str) -> int | None:
        raw_grade = normalized.removeprefix("/lesson_grade_")
        if not raw_grade.isdigit():
            return None
        grade = int(raw_grade)
        return grade if grade in GRADE_CHOICES else None

    def _lesson_flow_state(self, teacher) -> dict:
        if not teacher.note or not teacher.note.startswith(LESSON_FLOW_PREFIX):
            return {}
        try:
            state = json.loads(teacher.note.removeprefix(LESSON_FLOW_PREFIX))
        except json.JSONDecodeError:
            return {}
        return state if isinstance(state, dict) else {}

    def _set_lesson_flow(self, teacher, state: dict) -> None:
        teacher.note = LESSON_FLOW_PREFIX + json.dumps(state, ensure_ascii=False, sort_keys=True)
        self.db.flush()

    def _clear_lesson_flow(self, teacher) -> None:
        if teacher.note and teacher.note.startswith(LESSON_FLOW_PREFIX):
            teacher.note = None
            self.db.flush()

    def _history_message(self, *, teacher_id, language: str) -> str:
        recent = self.lessons.recent_for_teacher(teacher_id, limit=5)
        if not recent:
            return localized_text("history_empty", language)
        lines = [localized_text("history_header", language)]
        for lesson in recent:
            subject = lesson.subject or "-"
            topic = lesson.topic or lesson.raw_user_input[:60]
            grade = lesson.grade or "-"
            lines.append(f"- G{grade} {subject}: {topic} [{lesson.status}]")
        return "\n".join(lines)

    def _language_for_line_user(self, line_user_id: str | None) -> str:
        if not line_user_id:
            return DEFAULT_LANGUAGE
        teacher = self.orgs.get_teacher_by_line_user_id(line_user_id)
        if not teacher:
            return DEFAULT_LANGUAGE
        return normalize_language(teacher.language_preference)

    def _event_key(self, event: dict) -> str:
        raw = json.dumps(event, sort_keys=True, ensure_ascii=False)
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
