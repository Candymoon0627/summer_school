import hashlib
import random

from app.schemas.lesson import (
    LessonFlowStep,
    LessonGenerationResult,
    LessonTerm,
    StructuredLesson,
    TrilingualLessonFlowStep,
    TrilingualText,
)
from app.services.model_providers.base import EmbeddingProvider, ModelProvider


class MockModelProvider(ModelProvider):
    provider_name = "mock"
    model_name = "mock-lesson-v1"

    def generate_lesson(self, prompt: str) -> LessonGenerationResult:
        lesson = StructuredLesson(
            title="Grade 4 Math: Fractions with Local Market Examples",
            title_trilingual=TrilingualText(
                th="คณิตศาสตร์ ป.4: เศษส่วนจากตัวอย่างตลาดท้องถิ่น",
                ms="Matematik Tahun 4: Pecahan melalui contoh pasar tempatan",
                en="Grade 4 Math: Fractions with Local Market Examples",
            ),
            summary="A low-resource lesson plan using local market sharing examples.",
            summary_trilingual=TrilingualText(
                th="แผนการสอนแบบใช้ทรัพยากรน้อย โดยใช้ตัวอย่างการแบ่งของในตลาดท้องถิ่น",
                ms="Rancangan pengajaran rendah sumber menggunakan contoh perkongsian di pasar.",
                en="A low-resource lesson plan using local market sharing examples.",
            ),
            teaching_objectives=[
                "Students explain simple fractions using familiar objects.",
                "Students compare 1/2, 1/4, and 3/4 using a local example.",
            ],
            teaching_objectives_trilingual=[
                TrilingualText(
                    th="นักเรียนอธิบายเศษส่วนอย่างง่ายโดยใช้สิ่งของที่คุ้นเคยได้",
                    ms="Murid menerangkan pecahan mudah menggunakan objek harian.",
                    en="Students explain simple fractions using familiar objects.",
                ),
                TrilingualText(
                    th="นักเรียนเปรียบเทียบ 1/2, 1/4 และ 3/4 ด้วยตัวอย่างท้องถิ่นได้",
                    ms="Murid membandingkan 1/2, 1/4 dan 3/4 dengan contoh tempatan.",
                    en="Students compare 1/2, 1/4, and 3/4 using a local example.",
                ),
            ],
            materials=["Paper strips", "Bottle caps", "Board and chalk"],
            materials_trilingual=[
                TrilingualText(th="แถบกระดาษ", ms="Jalur kertas", en="Paper strips"),
                TrilingualText(th="ฝาขวด", ms="Penutup botol", en="Bottle caps"),
                TrilingualText(th="กระดานและชอล์ก", ms="Papan dan kapur", en="Board and chalk"),
            ],
            lesson_flow=[
                LessonFlowStep(
                    phase="Warm-up",
                    minutes=5,
                    teacher_action="Ask students how families share food at a market.",
                    student_action="Share examples from daily life.",
                ),
                LessonFlowStep(
                    phase="Activity",
                    minutes=25,
                    teacher_action="Use bottle caps to model halves and quarters.",
                    student_action="Work in groups to divide objects equally.",
                ),
            ],
            lesson_flow_trilingual=[
                TrilingualLessonFlowStep(
                    phase=TrilingualText(th="ขั้นนำ", ms="Set induksi", en="Warm-up"),
                    minutes=5,
                    teacher_action=TrilingualText(
                        th="ถามนักเรียนว่าครอบครัวแบ่งอาหารกันอย่างไร",
                        ms="Tanya murid bagaimana keluarga berkongsi makanan.",
                        en="Ask students how families share food.",
                    ),
                    student_action=TrilingualText(
                        th="เล่าตัวอย่างจากชีวิตประจำวัน",
                        ms="Kongsi contoh daripada kehidupan harian.",
                        en="Share examples from daily life.",
                    ),
                ),
                TrilingualLessonFlowStep(
                    phase=TrilingualText(th="กิจกรรม", ms="Aktiviti", en="Activity"),
                    minutes=25,
                    teacher_action=TrilingualText(
                        th="ใช้ฝาขวดจำลองครึ่งหนึ่งและหนึ่งในสี่",
                        ms="Gunakan penutup botol untuk model separuh dan suku.",
                        en="Use bottle caps to model halves and quarters.",
                    ),
                    student_action=TrilingualText(
                        th="ทำงานเป็นกลุ่มเพื่อแบ่งสิ่งของให้เท่ากัน",
                        ms="Bekerja dalam kumpulan untuk membahagi objek sama rata.",
                        en="Work in groups to divide objects equally.",
                    ),
                ),
            ],
            local_examples=["Sharing fish from a Pattani market into equal parts."],
            local_examples_trilingual=[
                TrilingualText(
                    th="การแบ่งปลาในตลาดปัตตานีเป็นส่วนเท่า ๆ กัน",
                    ms="Membahagi ikan di pasar Pattani kepada bahagian sama.",
                    en="Sharing fish from a Pattani market into equal parts.",
                )
            ],
            key_terms_trilingual=[
                LessonTerm(
                    term_th="เศษส่วน",
                    helper_ms="bahagian daripada satu benda",
                    helper_en="fraction",
                    teacher_note="Use concrete objects before symbols.",
                )
            ],
            student_activity="Students divide paper strips and bottle caps into equal parts.",
            student_activity_trilingual=TrilingualText(
                th="นักเรียนแบ่งแถบกระดาษและฝาขวดเป็นส่วนเท่า ๆ กัน",
                ms="Murid membahagi jalur kertas dan penutup botol kepada bahagian sama.",
                en="Students divide paper strips and bottle caps into equal parts.",
            ),
            practice_questions=[
                "Which is larger: 1/2 or 1/4?",
                "If 8 fish are shared equally by 4 families, how many fish does each get?",
            ],
            practice_questions_trilingual=[
                TrilingualText(
                    th="ข้อใดมากกว่า: 1/2 หรือ 1/4?",
                    ms="Yang manakah lebih besar: 1/2 atau 1/4?",
                    en="Which is larger: 1/2 or 1/4?",
                )
            ],
            board_plan="Draw one whole, then divide it into 2 and 4 equal parts.",
            board_plan_trilingual=TrilingualText(
                th="วาดหนึ่งหน่วยเต็ม แล้วแบ่งเป็น 2 และ 4 ส่วนเท่า ๆ กัน",
                ms="Lukis satu keseluruhan, kemudian bahagi kepada 2 dan 4 bahagian sama.",
                en="Draw one whole, then divide it into 2 and 4 equal parts.",
            ),
            low_resource_plan="Use chalk drawings or found objects if paper is unavailable.",
            low_resource_plan_trilingual=TrilingualText(
                th="ถ้าไม่มีกระดาษ ให้ใช้ภาพวาดด้วยชอล์กหรือสิ่งของที่หาได้",
                ms="Jika tiada kertas, gunakan lukisan kapur atau objek yang ada.",
                en="Use chalk drawings or found objects if paper is unavailable.",
            ),
            safety_notes="Avoid using real student or family names.",
            safety_notes_trilingual=TrilingualText(
                th="หลีกเลี่ยงการใช้ชื่อนักเรียนหรือครอบครัวจริง",
                ms="Elakkan menggunakan nama sebenar murid atau keluarga.",
                en="Avoid using real student or family names.",
            ),
            local_knowledge_used=["Local market sharing example"],
        )
        markdown = render_lesson_markdown(lesson)
        return LessonGenerationResult(
            structured_content=lesson,
            rendered_markdown=markdown,
            token_input=len(prompt.split()),
            token_output=len(markdown.split()),
        )

    def classify_json(self, prompt: str) -> dict:
        if "copyright" in prompt.lower():
            return {
                "copyright_status": "likely_original",
                "risk_level": "low",
                "tags": [],
                "notes": "Mock copyright classifier result.",
            }
        return {"risk_level": "low", "tags": [], "notes": "Mock classifier result."}


class MockEmbeddingProvider(EmbeddingProvider):
    provider_name = "mock"
    model_name = "mock-embedding-v1"

    def __init__(self, dimensions: int = 8) -> None:
        self.dimensions = dimensions

    def embed(self, text: str) -> list[float]:
        digest = hashlib.sha256(text.encode("utf-8")).digest()
        seed = int.from_bytes(digest[:8], "big")
        rng = random.Random(seed)
        return [round(rng.uniform(-1, 1), 6) for _ in range(self.dimensions)]


def render_lesson_markdown(lesson: StructuredLesson) -> str:
    objectives = _render_trilingual_list(
        lesson.teaching_objectives_trilingual,
        lesson.teaching_objectives,
    )
    materials = _render_trilingual_list(lesson.materials_trilingual, lesson.materials)
    flow = _render_flow(lesson)
    examples = _render_trilingual_list(lesson.local_examples_trilingual, lesson.local_examples)
    terms = "\n".join(
        f"- Thai: {term.term_th} | Local Malay: {term.helper_ms} | English: {term.helper_en}"
        for term in lesson.key_terms_trilingual
    )
    questions = _render_trilingual_list(
        lesson.practice_questions_trilingual,
        lesson.practice_questions,
    )
    refs = "\n".join(f"- {item}" for item in lesson.local_knowledge_used)
    return f"""# {_trilingual_line(lesson.title_trilingual, lesson.title)}

## Summary
{_trilingual_line(lesson.summary_trilingual, lesson.summary)}

## Teaching Objectives
{objectives}

## Materials
{materials}

## Lesson Flow
{flow}

## Local Examples
{examples}

## Key Terms
{terms}

## Student Activity
{_trilingual_line(lesson.student_activity_trilingual, lesson.student_activity)}

## Practice Questions
{questions}

## Board Plan
{_trilingual_line(lesson.board_plan_trilingual, lesson.board_plan)}

## Low-resource Alternative
{_trilingual_line(lesson.low_resource_plan_trilingual, lesson.low_resource_plan)}

## Safety Notes
{_trilingual_line(lesson.safety_notes_trilingual, lesson.safety_notes or "")}

## Local Knowledge Used
{refs}
"""


def _trilingual_line(text, fallback: str) -> str:
    if text is None:
        return fallback
    return f"Thai: {text.th}\nLocal Malay: {text.ms}\nEnglish: {text.en}"


def _render_trilingual_list(items, fallback: list[str]) -> str:
    if not items:
        return "\n".join(f"- {item}" for item in fallback)
    return "\n".join(
        f"- Thai: {item.th}\n  Local Malay: {item.ms}\n  English: {item.en}" for item in items
    )


def _render_flow(lesson: StructuredLesson) -> str:
    if not lesson.lesson_flow_trilingual:
        return "\n".join(
            f"- {step.phase} ({step.minutes or '?'} min): {step.teacher_action}"
            for step in lesson.lesson_flow
        )
    lines = []
    for step in lesson.lesson_flow_trilingual:
        lines.append(
            f"- {step.phase.th} / {step.phase.ms} / {step.phase.en} "
            f"({step.minutes or '?'} min)\n"
            f"  Thai: {step.teacher_action.th}\n"
            f"  Local Malay: {step.teacher_action.ms}\n"
            f"  English: {step.teacher_action.en}"
        )
    return "\n".join(lines)
