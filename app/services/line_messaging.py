import logging
import time

import httpx

from app.core.config import get_settings
from app.services.language import LANGUAGE_QUICK_REPLY_LABELS, SupportedLanguage

logger = logging.getLogger(__name__)
LINE_RETRYABLE_STATUS_CODES = {429, 500, 502, 503, 504}
LINE_RETRY_DELAYS_SECONDS = (0.0, 0.5)


class LineMessagingService:
    def reply_text(
        self,
        reply_token: str,
        text: str,
        *,
        quick_reply_items: list[dict] | None = None,
    ) -> None:
        settings = get_settings()
        if not settings.line_channel_access_token:
            logger.info("LINE reply placeholder: %s", text)
            return
        message = {"type": "text", "text": text[:5000]}
        if quick_reply_items:
            message["quickReply"] = {"items": quick_reply_items}
        self._post(
            "https://api.line.me/v2/bot/message/reply",
            {
                "replyToken": reply_token,
                "messages": [message],
            },
            settings.line_channel_access_token,
        )

    def reply_language_choices(self, reply_token: str, text: str) -> None:
        self.reply_text(reply_token, text, quick_reply_items=self._language_quick_reply_items())

    def reply_flex(
        self,
        reply_token: str,
        *,
        alt_text: str,
        contents: dict,
        quick_reply_items: list[dict] | None = None,
    ) -> None:
        settings = get_settings()
        if not settings.line_channel_access_token:
            logger.info("LINE flex reply placeholder: %s", alt_text)
            return
        message = {
            "type": "flex",
            "altText": alt_text[:400],
            "contents": contents,
        }
        if quick_reply_items:
            message["quickReply"] = {"items": quick_reply_items}
        self._post(
            "https://api.line.me/v2/bot/message/reply",
            {
                "replyToken": reply_token,
                "messages": [message],
            },
            settings.line_channel_access_token,
        )

    def reply_menu_card(self, reply_token: str, *, command: str, language: SupportedLanguage) -> None:
        card = _menu_card(command, language)
        self.reply_flex(
            reply_token,
            alt_text=card["alt_text"],
            contents=_flex_bubble(card["title"], card["body"], card["buttons"]),
            quick_reply_items=self.message_quick_reply_items(card["quick_replies"]),
        )

    def push_text(self, line_user_id: str, text: str) -> None:
        settings = get_settings()
        if not settings.line_channel_access_token:
            logger.info("LINE push placeholder to %s: %s", line_user_id, text)
            return
        self._post(
            "https://api.line.me/v2/bot/message/push",
            {
                "to": line_user_id,
                "messages": [{"type": "text", "text": text[:5000]}],
            },
            settings.line_channel_access_token,
        )

    def link_rich_menu_for_language(
        self,
        line_user_id: str,
        language: SupportedLanguage,
    ) -> None:
        settings = get_settings()
        rich_menu_id = {
            "th": settings.line_rich_menu_id_th,
            "ms": settings.line_rich_menu_id_ms,
            "en": settings.line_rich_menu_id_en,
        }.get(language)
        if not settings.line_channel_access_token or not rich_menu_id:
            logger.info("LINE rich menu link placeholder for %s: %s", line_user_id, language)
            return
        try:
            self._post(
                f"https://api.line.me/v2/bot/user/{line_user_id}/richmenu/{rich_menu_id}",
                {},
                settings.line_channel_access_token,
            )
        except httpx.HTTPStatusError:
            logger.exception("Failed to link LINE rich menu for %s: %s", line_user_id, language)

    def _language_quick_reply_items(self) -> list[dict]:
        return self.message_quick_reply_items(
            [(label, label) for label in LANGUAGE_QUICK_REPLY_LABELS.values()]
        )

    def message_quick_reply_items(self, items: list[tuple[str, str]]) -> list[dict]:
        return [
            {
                "type": "action",
                "action": {
                    "type": "message",
                    "label": label[:20],
                    "text": text,
                },
            }
            for label, text in items
        ]

    def _post(self, url: str, payload: dict, access_token: str) -> None:
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json",
        }
        for attempt in range(len(LINE_RETRY_DELAYS_SECONDS) + 1):
            try:
                with httpx.Client(timeout=10) as client:
                    response = client.post(url, json=payload, headers=headers)
                status_code = getattr(response, "status_code", None)
                if (
                    status_code in LINE_RETRYABLE_STATUS_CODES
                    and attempt < len(LINE_RETRY_DELAYS_SECONDS)
                ):
                    delay = LINE_RETRY_DELAYS_SECONDS[attempt]
                    logger.warning(
                        "LINE request returned %s on attempt %s/%s; retrying in %.1fs: %s",
                        status_code,
                        attempt + 1,
                        len(LINE_RETRY_DELAYS_SECONDS) + 1,
                        delay,
                        url,
                    )
                    time.sleep(delay)
                    continue
                response.raise_for_status()
                return
            except httpx.TransportError as exc:
                if attempt >= len(LINE_RETRY_DELAYS_SECONDS):
                    logger.exception("LINE request failed after retries: %s", url)
                    return
                delay = LINE_RETRY_DELAYS_SECONDS[attempt]
                logger.warning(
                    "LINE request transport error on attempt %s/%s; retrying in %.1fs: %s",
                    attempt + 1,
                    len(LINE_RETRY_DELAYS_SECONDS) + 1,
                    delay,
                    exc,
                )
                time.sleep(delay)
            except httpx.HTTPStatusError:
                logger.exception("LINE request rejected: %s", url)
                return


MENU_CARD_COPY = {
    "lesson": {
        "th": {
            "title": "สร้างแผนสอน",
            "body": "เลือกตัวอย่างด้านล่าง หรือพิมพ์ชั้นเรียน วิชา และหัวข้อเอง",
            "buttons": [
                ("เลือกชั้นเรียน", "/lesson_choose_grade"),
                ("เปลี่ยนภาษา", "/change language"),
                ("ช่วยเหลือ", "/menu_help"),
            ],
            "quick_replies": [],
        },
        "ms": {
            "title": "Jana Pelajaran",
            "body": "Pilih contoh di bawah atau taip darjah, subjek, dan topik sendiri.",
            "buttons": [
                ("Pilih darjah", "/lesson_choose_grade"),
                ("Tukar bahasa", "/change language"),
                ("Bantuan", "/menu_help"),
            ],
            "quick_replies": [],
        },
        "en": {
            "title": "Generate Lesson",
            "body": "Choose a sample below, or type your own grade, subject, and topic.",
            "buttons": [
                ("Choose grade", "/lesson_choose_grade"),
                ("Language", "/change language"),
                ("Help", "/menu_help"),
            ],
            "quick_replies": [],
        },
    },
    "submit_text": {
        "th": {
            "title": "ส่งข้อความ",
            "body": "ส่งความรู้ท้องถิ่นด้วยรูปแบบ submit: ตามด้วยเนื้อหา",
            "buttons": [
                ("ดูรูปแบบ", "/submission_format"),
                ("ตัวอย่าง", "/submission_example"),
                ("เริ่มส่ง", "/submission_start"),
            ],
            "quick_replies": [("สร้างแผนสอน", "/menu_lesson"), ("ประวัติ", "/menu_history")],
        },
        "ms": {
            "title": "Hantar Teks",
            "body": "Hantar ilmu tempatan dengan format submit: diikuti kandungan.",
            "buttons": [
                ("Format", "/submission_format"),
                ("Contoh", "/submission_example"),
                ("Mula", "/submission_start"),
            ],
            "quick_replies": [("Jana pelajaran", "/menu_lesson"), ("Sejarah", "/menu_history")],
        },
        "en": {
            "title": "Text Submission",
            "body": "Submit local knowledge with submit: followed by the content.",
            "buttons": [
                ("Format", "/submission_format"),
                ("Example", "/submission_example"),
                ("Start", "/submission_start"),
            ],
            "quick_replies": [("Lesson", "/menu_lesson"), ("History", "/menu_history")],
        },
    },
    "submit_image": {
        "th": {
            "title": "ส่งรูปภาพ",
            "body": "รูปภาพและ OCR ยังอยู่ระหว่างพัฒนา ตอนนี้ใช้การส่งข้อความก่อน",
            "buttons": [("ส่งข้อความ", "/menu_submit_text"), ("ช่วยเหลือ", "/menu_help")],
            "quick_replies": [("สร้างแผนสอน", "/menu_lesson"), ("ประวัติ", "/menu_history")],
        },
        "ms": {
            "title": "Hantar Imej",
            "body": "Imej dan OCR masih dibina. Buat masa ini, gunakan hantaran teks.",
            "buttons": [("Hantar teks", "/menu_submit_text"), ("Bantuan", "/menu_help")],
            "quick_replies": [("Jana pelajaran", "/menu_lesson"), ("Sejarah", "/menu_history")],
        },
        "en": {
            "title": "Image Submission",
            "body": "Image and OCR submission is still in development. Use text submission for now.",
            "buttons": [("Text Submission", "/menu_submit_text"), ("Help", "/menu_help")],
            "quick_replies": [("Lesson", "/menu_lesson"), ("History", "/menu_history")],
        },
    },
    "ai_experience": {
        "th": {
            "title": "ประสบการณ์ AI",
            "body": "กิจกรรม AI ในห้องเรียนยังอยู่ระหว่างพัฒนา",
            "buttons": [("สร้างแผนสอน", "/menu_lesson"), ("ช่วยเหลือ", "/menu_help")],
            "quick_replies": [("ส่งข้อความ", "/menu_submit_text"), ("ประวัติ", "/menu_history")],
        },
        "ms": {
            "title": "Pengalaman AI",
            "body": "Aktiviti AI dalam bilik darjah masih dalam pembangunan.",
            "buttons": [("Jana pelajaran", "/menu_lesson"), ("Bantuan", "/menu_help")],
            "quick_replies": [("Hantar teks", "/menu_submit_text"), ("Sejarah", "/menu_history")],
        },
        "en": {
            "title": "AI Experience",
            "body": "AI classroom activities are still in development.",
            "buttons": [("Generate Lesson", "/menu_lesson"), ("Help", "/menu_help")],
            "quick_replies": [("Submit text", "/menu_submit_text"), ("History", "/menu_history")],
        },
    },
    "help": {
        "th": {
            "title": "ช่วยเหลือ",
            "body": "เลือกงานที่ต้องการ หรือเปลี่ยนภาษาได้จากปุ่มด้านล่าง",
            "buttons": [
                ("สร้างแผนสอน", "/menu_lesson"),
                ("ส่งข้อความ", "/menu_submit_text"),
                ("เปลี่ยนภาษา", "/change language"),
            ],
            "quick_replies": [("ประวัติ", "/menu_history"), ("รูปภาพ", "/menu_submit_image")],
        },
        "ms": {
            "title": "Bantuan",
            "body": "Pilih tugas yang diperlukan, atau tukar bahasa dengan butang di bawah.",
            "buttons": [
                ("Jana pelajaran", "/menu_lesson"),
                ("Hantar teks", "/menu_submit_text"),
                ("Tukar bahasa", "/change language"),
            ],
            "quick_replies": [("Sejarah", "/menu_history"), ("Imej", "/menu_submit_image")],
        },
        "en": {
            "title": "Help",
            "body": "Choose a task, or switch language from the buttons below.",
            "buttons": [
                ("Generate Lesson", "/menu_lesson"),
                ("Text Submission", "/menu_submit_text"),
                ("Language", "/change language"),
            ],
            "quick_replies": [("History", "/menu_history"), ("Image", "/menu_submit_image")],
        },
    },
}


def _menu_card(command: str, language: SupportedLanguage) -> dict:
    copy = MENU_CARD_COPY[command][language]
    return {
        "alt_text": copy["title"],
        "title": copy["title"],
        "body": copy["body"],
        "buttons": copy["buttons"],
        "quick_replies": copy["quick_replies"],
    }


def _flex_bubble(title: str, body: str, buttons: list[tuple[str, str]]) -> dict:
    return {
        "type": "bubble",
        "size": "mega",
        "body": {
            "type": "box",
            "layout": "vertical",
            "spacing": "md",
            "contents": [
                {
                    "type": "text",
                    "text": title,
                    "weight": "bold",
                    "size": "xl",
                    "wrap": True,
                    "color": "#0f172a",
                },
                {
                    "type": "text",
                    "text": body,
                    "size": "sm",
                    "wrap": True,
                    "color": "#475569",
                },
            ],
        },
        "footer": {
            "type": "box",
            "layout": "vertical",
            "spacing": "sm",
            "contents": [
                {
                    "type": "button",
                    "style": "primary" if index == 0 else "secondary",
                    "height": "sm",
                    "action": {
                        "type": "message",
                        "label": label,
                        "text": text,
                    },
                }
                for index, (label, text) in enumerate(buttons)
            ],
            "flex": 0,
        },
    }
