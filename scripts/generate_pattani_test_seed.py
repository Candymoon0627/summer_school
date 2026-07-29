from __future__ import annotations

from pathlib import Path

import yaml

BATCH_ID = "pattani-test-v1-80"
OUTPUT_PATH = Path("data/seed_knowledge/pattani_test_80.yaml")

TOPICS = [
    ("math", "fractions", "Fractions as equal parts", "เศษส่วนคือส่วนที่เท่ากันของทั้งหมด"),
    ("math", "equivalent fractions", "Equivalent fractions", "เศษส่วนที่เท่ากันแทนปริมาณเดียวกัน"),
    ("math", "perimeter", "Perimeter of rectangles", "เส้นรอบรูปคือผลรวมความยาวรอบรูป"),
    ("math", "area", "Area with unit squares", "พื้นที่คือจำนวนช่องหน่วยที่ปกคลุมรูป"),
    ("math", "data representation", "Reading pictographs", "แผนภูมิรูปภาพใช้สัญลักษณ์แสดงข้อมูล"),
    ("math", "multiplication", "Multiplication as groups", "การคูณคือกลุ่มที่มีจำนวนเท่ากัน"),
    ("math", "division", "Division as sharing", "การหารคือการแบ่งอย่างเท่าเทียม"),
    ("math", "decimals", "Decimals and tenths", "ทศนิยมแสดงส่วนของสิบหรือร้อย"),
    ("math", "measurement", "Measuring length", "การวัดความยาวต้องใช้หน่วยเดียวกัน"),
    ("math", "time", "Elapsed time", "เวลาที่ผ่านไปหาได้จากเวลาเริ่มและเวลาสิ้นสุด"),
    ("science", "water cycle", "Water cycle", "วัฏจักรน้ำมีการระเหย ควบแน่น และฝนตก"),
    ("science", "evaporation", "Evaporation", "การระเหยคือน้ำเปลี่ยนเป็นไอน้ำ"),
    ("science", "plant parts", "Plant parts", "ราก ลำต้น และใบมีหน้าที่ต่างกัน"),
    ("science", "material properties", "Material properties", "วัสดุมีสมบัติเช่นแข็ง ยืดหยุ่น หรือดูดซับน้ำ"),
    ("science", "forces", "Push and pull forces", "แรงผลักและแรงดึงเปลี่ยนการเคลื่อนที่"),
    ("science", "habitats", "Habitats", "ถิ่นที่อยู่ให้สิ่งมีชีวิตมีอาหาร น้ำ และที่หลบภัย"),
    ("science", "states of matter", "States of matter", "ของแข็ง ของเหลว และแก๊สมีสมบัติต่างกัน"),
    ("science", "light", "Light and shadows", "เงาเกิดเมื่อวัตถุกั้นทางเดินของแสง"),
    ("science", "sound", "Sound vibrations", "เสียงเกิดจากการสั่นสะเทือน"),
    ("science", "weather", "Weather observation", "สภาพอากาศสังเกตได้จากฝน ลม เมฆ และอุณหภูมิ"),
]

CONTEXTS = [
    "Use examples from a Pattani classroom, local market, garden, canal, or coastal community.",
    "Connect the idea to familiar low-cost materials such as paper, string, bottle caps, fruit, or notebooks.",
    "Use bilingual discussion in Thai with optional local Malay helper phrases for peer explanation.",
    "Prefer examples that work in low-resource classrooms and do not require internet or lab equipment.",
]

ACTIVITIES = [
    "Students first predict, then test with a small drawing, measurement, sorting task, or discussion.",
    "Pairs explain their reasoning, compare answers, and revise one sentence after teacher feedback.",
    "Groups make a quick table or diagram, then share one observation with the class.",
    "The teacher checks understanding with one exit question connected to a local example.",
]

SAFETY = [
    "Use clean, safe classroom materials and avoid sharp, hot, glass, or unknown objects.",
    "Avoid examples that reveal sensitive family, income, religion, or ethnicity information.",
    "Keep movement organized and make sure water or floor activities do not create slipping risk.",
    "Supervise cutting, measuring, and outdoor observation activities.",
]


def build_items() -> list[dict]:
    items = []
    for index in range(80):
        subject, topic, title, thai_concept = TOPICS[index % len(TOPICS)]
        grade = 3 + (index % 3)
        context = CONTEXTS[index % len(CONTEXTS)]
        activity = ACTIVITIES[index % len(ACTIVITIES)]
        safety = SAFETY[index % len(SAFETY)]
        variant = index // len(TOPICS) + 1
        knowledge_type = ["term_explanation", "teaching_activity", "local_example", "term_explanation"][
            index % 4
        ]
        items.append(
            {
                "knowledge_type": knowledge_type,
                "title": f"{title} - test item {variant}",
                "region_code": "pattani",
                "visibility_scope": "shared_region",
                "subject": subject,
                "topic": topic,
                "target_grade": grade,
                "grade_min": max(1, grade - 1),
                "grade_max": min(6, grade + 1),
                "content_en": (
                    f"{title} is a core grade {grade} concept for MVP retrieval testing. "
                    f"The teacher should define the idea, show one concrete example, and ask "
                    f"students to explain the reasoning in their own words."
                ),
                "content_th": (
                    f"{thai_concept} สำหรับชั้นประถมศึกษาปีที่ {grade} "
                    f"ครูควรเริ่มจากตัวอย่างที่จับต้องได้ ให้ผู้เรียนสังเกต อธิบายเหตุผล "
                    f"และเชื่อมโยงกับสถานการณ์ใกล้ตัว"
                ),
                "content_ms": (
                    f"Konsep ini sesuai untuk Tahun {grade}. Guru boleh menggunakan contoh "
                    f"harian, meminta murid memerhati, berbincang dan menerangkan idea dengan "
                    f"perkataan sendiri."
                ),
                "local_context": context,
                "classroom_use": activity,
                "safety_notes": safety,
                "quality_score": 3,
                "source_type": "oer_synthetic_test",
                "source_confidence": "medium",
                "source_note": (
                    f"batch={BATCH_ID}; self-authored synthetic MVP test item inspired by "
                    "general elementary OER-style concepts; not final curriculum-approved content."
                ),
                "verified": True,
            }
        )
    return items


def main() -> None:
    OUTPUT_PATH.write_text(
        yaml.safe_dump(build_items(), allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    print(f"Wrote {OUTPUT_PATH} with 80 items for batch {BATCH_ID}.")


if __name__ == "__main__":
    main()
