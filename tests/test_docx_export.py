from zipfile import ZipFile

from app.core.config import get_settings
from app.schemas.lesson import (
    LessonFlowStep,
    LessonTerm,
    StructuredLesson,
    TrilingualText,
)
from app.services.docx_export import DocxExportService


def test_docx_export_writes_one_selected_language_and_sets_font(monkeypatch, tmp_path) -> None:
    monkeypatch.setenv("LOCAL_STORAGE_DIR", str(tmp_path))
    get_settings.cache_clear()
    lesson = _lesson()

    thai_path = DocxExportService().export_lesson(lesson, language="th")
    english_path = DocxExportService().export_lesson(lesson, language="en")
    malay_path = DocxExportService().export_lesson(lesson, language="ms")

    thai_xml = ZipFile(thai_path).read("word/document.xml").decode("utf-8")
    english_xml = ZipFile(english_path).read("word/document.xml").decode("utf-8")
    malay_xml = ZipFile(malay_path).read("word/document.xml").decode("utf-8")
    styles_xml = ZipFile(thai_path).read("word/styles.xml").decode("utf-8")

    assert "บทเรียนเรื่องวัฏจักรน้ำ" in thai_xml
    assert "Students learn about evaporation" not in thai_xml
    assert "Lesson about the water cycle" in english_xml
    assert "บทเรียนเรื่องวัฏจักรน้ำ" not in english_xml
    assert "Pelajaran tentang kitaran air" in malay_xml
    assert 'w:eastAsia="Tahoma"' in styles_xml
    assert 'w:cs="Tahoma"' in styles_xml


def _lesson() -> StructuredLesson:
    return StructuredLesson(
        title="Water cycle lesson",
        title_trilingual=TrilingualText(
            th="บทเรียนเรื่องวัฏจักรน้ำ",
            ms="Pelajaran tentang kitaran air",
            en="Lesson about the water cycle",
        ),
        summary="Students learn about evaporation and condensation.",
        summary_trilingual=TrilingualText(
            th="นักเรียนเรียนรู้เรื่องการระเหยและการควบแน่น",
            ms="Murid belajar tentang penyejatan dan pemeluwapan",
            en="Students learn about evaporation and condensation.",
        ),
        teaching_objectives=["Explain the water cycle."],
        teaching_objectives_trilingual=[
            TrilingualText(
                th="อธิบายวัฏจักรน้ำได้",
                ms="Menerangkan kitaran air",
                en="Explain the water cycle.",
            )
        ],
        materials=["Paper"],
        materials_trilingual=[
            TrilingualText(th="กระดาษ", ms="Kertas", en="Paper"),
        ],
        lesson_flow=[
            LessonFlowStep(
                phase="Warm-up",
                minutes=5,
                teacher_action="Ask a question.",
                student_action="Answer.",
            )
        ],
        local_examples=["Drying clothes"],
        key_terms_trilingual=[
            LessonTerm(term_th="การระเหย", helper_ms="Penyejatan", helper_en="Evaporation")
        ],
        student_activity="Draw a diagram.",
        practice_questions=["Where does water go?"],
        board_plan="Draw the water cycle.",
        low_resource_plan="Use paper and pencil.",
    )
