from typing import Literal

SupportedLanguage = Literal["th", "ms", "en"]

DEFAULT_LANGUAGE: SupportedLanguage = "th"
SUPPORTED_LANGUAGES: tuple[SupportedLanguage, ...] = ("th", "ms", "en")

LANGUAGE_LABELS: dict[SupportedLanguage, str] = {
    "th": "ไทย",
    "ms": "Bahasa Melayu",
    "en": "English",
}

LANGUAGE_QUICK_REPLY_LABELS: dict[SupportedLanguage, str] = {
    "th": "ไทย",
    "ms": "Bahasa Melayu",
    "en": "English",
}

_LANGUAGE_ALIASES: dict[str, SupportedLanguage] = {
    "th": "th",
    "thai": "th",
    "ไทย": "th",
    "ภาษาไทย": "th",
    "เปลี่ยนเป็นไทย": "th",
    "ms": "ms",
    "my": "ms",
    "malay": "ms",
    "melayu": "ms",
    "bahasa melayu": "ms",
    "bahasa malaysia": "ms",
    "ภาษามลายู": "ms",
    "มลายู": "ms",
    "มาเลย์": "ms",
    "en": "en",
    "eng": "en",
    "english": "en",
    "อังกฤษ": "en",
    "ภาษาอังกฤษ": "en",
}

TEXT: dict[str, dict[SupportedLanguage, str]] = {
    "choose_language": {
        "th": "เลือกภาษาที่ต้องการใช้ใน LINE และเอกสาร DOCX",
        "ms": "Pilih bahasa untuk mesej LINE dan dokumen DOCX.",
        "en": "Choose the language for LINE replies and DOCX documents.",
    },
    "language_changed": {
        "th": "เปลี่ยนภาษาเป็นไทยแล้ว",
        "ms": "Bahasa telah ditukar kepada Bahasa Melayu.",
        "en": "Language changed to English.",
    },
    "invalid_school_code": {
        "th": "กรุณาใส่รหัสเชิญโรงเรียนที่ถูกต้องก่อนใช้ผู้ช่วยนี้",
        "ms": "Sila masukkan kod jemputan sekolah yang sah sebelum menggunakan pembantu ini.",
        "en": "Please enter a valid school invitation code before using the assistant.",
    },
    "bound_to_school": {
        "th": "เชื่อมต่อกับโรงเรียนแล้ว: {school_name}. ขั้นตอนความยินยอมถูกเตรียมไว้แล้ว",
        "ms": "Telah dipautkan ke sekolah: {school_name}. Aliran persetujuan telah disediakan.",
        "en": "Bound to school: {school_name}. Consent flow is scaffolded.",
    },
    "image_under_development": {
        "th": "การส่งรูปภาพ/ไฟล์กำลังพัฒนาอยู่ ตอนนี้กรุณาใช้การส่งข้อความก่อน",
        "ms": "Penghantaran imej/fail masih dalam pembangunan. Buat masa ini, sila gunakan teks.",
        "en": "Image/file submission is under development. Please use text submission for now.",
    },
    "unsupported_message_type": {
        "th": "ยังไม่รองรับข้อความประเภทนี้",
        "ms": "Jenis mesej ini belum disokong.",
        "en": "This message type is not supported yet.",
    },
    "missing_submission_body": {
        "th": "กรุณาใส่เนื้อหาหลังคำว่า submit: หรือ 投稿:",
        "ms": "Sila tambah kandungan selepas submit: atau 投稿:.",
        "en": "Please add submission content after submit: or 投稿:.",
    },
    "submission_received": {
        "th": "ได้รับข้อมูลแล้ว ID: {submission_id}. กำลังรอผู้ดูแลตรวจสอบ",
        "ms": "Sumbangan diterima. ID: {submission_id}. Menunggu semakan admin.",
        "en": "Submission received. ID: {submission_id}. It is waiting for admin review.",
    },
    "menu_lesson": {
        "th": "ส่งระดับชั้น วิชา และหัวข้อ เช่น: ป.4 คณิตศาสตร์ เศษส่วน",
        "ms": "Hantar darjah, subjek, dan topik. Contoh: Tahun 4 matematik pecahan",
        "en": "Send the grade, subject, and topic. Example: Grade 4 math fractions",
    },
    "menu_submit_text": {
        "th": "ส่งความรู้ท้องถิ่นโดยขึ้นต้นข้อความด้วย submit: แล้วตามด้วยเนื้อหา",
        "ms": "Hantar pengetahuan tempatan dengan memulakan mesej menggunakan submit: diikuti kandungan.",
        "en": "Send local knowledge by starting the message with submit: followed by the content.",
    },
    "menu_submit_image": {
        "th": "การส่งรูปภาพ/OCR กำลังพัฒนาอยู่",
        "ms": "Penghantaran imej/OCR masih dalam pembangunan.",
        "en": "Image/OCR submission is in development.",
    },
    "menu_ai_experience": {
        "th": "ประสบการณ์ AI ในห้องเรียนกำลังพัฒนาอยู่",
        "ms": "Pengalaman AI dalam bilik darjah masih dalam pembangunan.",
        "en": "AI classroom experience is in development.",
    },
    "menu_help": {
        "th": "ส่งหัวข้อบทเรียนเพื่อสร้างแผนการสอน ใช้ /change language เพื่อเปลี่ยนภาษา หากยังไม่ได้เชื่อมโรงเรียน ให้ส่งรหัสเชิญโรงเรียนก่อน",
        "ms": "Hantar topik pelajaran untuk menjana rancangan mengajar. Gunakan /change language untuk menukar bahasa. Jika belum dipautkan, hantar kod jemputan sekolah dahulu.",
        "en": "Send a lesson topic to generate a lesson plan. Use /change language to switch language. If you are not bound yet, send your school invitation code first.",
    },
    "history_empty": {
        "th": "ยังไม่มีประวัติการขอแผนการสอน",
        "ms": "Belum ada sejarah permintaan rancangan mengajar.",
        "en": "No lesson request history yet.",
    },
    "history_header": {
        "th": "ประวัติแผนการสอนล่าสุด:",
        "ms": "Sejarah rancangan mengajar terkini:",
        "en": "Recent lesson requests:",
    },
    "needs_binding": {
        "th": "กรุณาใส่รหัสเชิญโรงเรียนก่อนใช้ผู้ช่วยนี้",
        "ms": "Sila masukkan kod jemputan sekolah sebelum menggunakan pembantu ini.",
        "en": "Please enter your school invitation code before using the assistant.",
    },
    "account_disabled": {
        "th": "บัญชีของคุณถูกปิดใช้งานอยู่ในขณะนี้",
        "ms": "Akaun anda sedang dinyahaktifkan.",
        "en": "Your account is currently disabled.",
    },
    "missing_lesson_fields": {
        "th": "กรุณาระบุวิชา ระดับชั้น และหัวข้อ",
        "ms": "Sila berikan subjek, darjah, dan topik.",
        "en": "Please provide subject, grade, and topic.",
    },
    "queue_failed": {
        "th": "บันทึกคำขอแล้ว แต่คิวประมวลผลยังไม่พร้อมใช้งาน",
        "ms": "Permintaan telah disimpan, tetapi baris gilir pekerja tidak tersedia.",
        "en": "The request was saved, but the worker queue is not available.",
    },
    "lesson_started": {
        "th": "เริ่มสร้างแผนการสอนแล้ว",
        "ms": "Penjanaan rancangan mengajar telah bermula.",
        "en": "Lesson generation has started.",
    },
    "lesson_ready": {
        "th": "แผนการสอนพร้อมแล้ว:",
        "ms": "Rancangan mengajar sudah siap:",
        "en": "Lesson plan ready:",
    },
    "download_docx": {
        "th": "ดาวน์โหลด DOCX:",
        "ms": "Muat turun DOCX:",
        "en": "Download DOCX:",
    },
    "lesson_failed": {
        "th": "ขออภัย การสร้างแผนการสอนล้มเหลว กรุณาลองใหม่หรือส่งวิชา ระดับชั้น และหัวข้อให้ง่ายขึ้น",
        "ms": "Maaf, penjanaan rancangan mengajar gagal. Sila cuba lagi atau hantar subjek, darjah, dan topik yang lebih ringkas.",
        "en": "Sorry, lesson generation failed. Please try again or send a simpler subject, grade, and topic.",
    },
}

MENU_COMMANDS = {
    "lesson": {
        "/menu_lesson",
        "menu lesson",
        "generate lesson",
        "lesson",
        "สร้างแผนการสอน",
        "แผนการสอน",
        "jana rancangan",
        "rancangan mengajar",
    },
    "submit_text": {
        "/menu_submit_text",
        "menu submit text",
        "text submission",
        "submit text",
        "ส่งข้อความ",
        "ส่งเนื้อหา",
        "hantar teks",
        "sumbangan teks",
    },
    "submit_image": {
        "/menu_submit_image",
        "menu submit image",
        "image submission",
        "submit image",
        "ส่งรูปภาพ",
        "ส่งไฟล์",
        "hantar imej",
    },
    "ai_experience": {
        "/menu_ai_experience",
        "menu ai experience",
        "ai experience",
        "ประสบการณ์ ai",
        "ai classroom",
        "pengalaman ai",
    },
    "history": {
        "/menu_history",
        "menu history",
        "my history",
        "history",
        "ประวัติ",
        "sejarah",
    },
    "help": {
        "/menu_help",
        "/help",
        "menu help",
        "help",
        "ช่วยเหลือ",
        "คู่มือ",
        "bantuan",
    },
}

CHANGE_LANGUAGE_ALIASES = {
    "/change language",
    "/change_language",
    "/language",
    "change language",
    "language",
    "เปลี่ยนภาษา",
    "ภาษา",
    "tukar bahasa",
    "bahasa",
}


def normalize_language(language: str | None) -> SupportedLanguage:
    if language in SUPPORTED_LANGUAGES:
        return language  # type: ignore[return-value]
    return DEFAULT_LANGUAGE


def text(key: str, language: str | None = None, **kwargs) -> str:
    language = normalize_language(language)
    template = TEXT[key][language]
    return template.format(**kwargs) if kwargs else template


def detect_language_selection(raw_text: str) -> SupportedLanguage | None:
    normalized = _normalize(raw_text)
    if normalized in _LANGUAGE_ALIASES:
        return _LANGUAGE_ALIASES[normalized]

    if normalized.startswith(("/language ", "/change language ", "/change_language ")):
        maybe_language = normalized.split(" ", maxsplit=1)[1]
        return _LANGUAGE_ALIASES.get(maybe_language)

    return None


def is_change_language_command(raw_text: str) -> bool:
    normalized = _normalize(raw_text)
    if normalized in CHANGE_LANGUAGE_ALIASES:
        return True
    return normalized.startswith(("/language ", "/change language ", "/change_language "))


def normalize_menu_command(raw_text: str) -> str | None:
    normalized = _normalize(raw_text)
    for command, aliases in MENU_COMMANDS.items():
        if normalized in {_normalize(alias) for alias in aliases}:
            return command
    return None


def _normalize(raw_text: str) -> str:
    return " ".join(raw_text.strip().casefold().replace("_", " ").split())
