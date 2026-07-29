from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

WIDTH = 2500
HEIGHT = 1686
COLS = 2
ROWS = 3
CELL_W = WIDTH // COLS
CELL_H = HEIGHT // ROWS


FONT_CANDIDATES = {
    "common": {
        "regular": [
            Path("C:/Windows/Fonts/segoeui.ttf"),
            Path("C:/Windows/Fonts/tahoma.ttf"),
            Path("C:/Windows/Fonts/arial.ttf"),
        ],
        "bold": [
            Path("C:/Windows/Fonts/segoeuib.ttf"),
            Path("C:/Windows/Fonts/tahomabd.ttf"),
            Path("C:/Windows/Fonts/arialbd.ttf"),
        ],
    },
    "thai": {
        "regular": [
            Path("C:/Windows/Fonts/LeelawUI.ttf"),
            Path("C:/Windows/Fonts/tahoma.ttf"),
            Path("C:/Windows/Fonts/segoeui.ttf"),
        ],
        "bold": [
            Path("C:/Windows/Fonts/LeelaUIb.ttf"),
            Path("C:/Windows/Fonts/tahomabd.ttf"),
            Path("C:/Windows/Fonts/segoeuib.ttf"),
        ],
    },
}


PALETTE = [
    ((238, 247, 245), (0, 128, 112)),
    ((255, 247, 237), (198, 92, 0)),
    ((239, 246, 255), (37, 99, 235)),
    ((249, 245, 255), (124, 58, 237)),
    ((241, 245, 249), (71, 85, 105)),
    ((240, 253, 244), (22, 163, 74)),
]


MENUS = {
    "en": {
        "title": "Edu AI Assistant",
        "font": "common",
        "items": [
            ("lesson", "Generate Lesson", "Create a lesson plan"),
            ("text", "Text Submission", "Share local knowledge"),
            ("image", "Image Submission", "OCR under development"),
            ("ai", "AI Experience", "Classroom activities"),
            ("history", "My History", "Recent lesson requests"),
            ("help", "Help", "Commands and support"),
        ],
    },
    "ms": {
        "title": "Edu AI Assistant",
        "font": "common",
        "items": [
            ("lesson", "Jana Pelajaran", "Bina rancangan mengajar"),
            ("text", "Hantar Teks", "Kongsi ilmu tempatan"),
            ("image", "Hantar Imej", "OCR sedang dibina"),
            ("ai", "Pengalaman AI", "Aktiviti bilik darjah"),
            ("history", "Sejarah Saya", "Permintaan terkini"),
            ("help", "Bantuan", "Arahan dan sokongan"),
        ],
    },
    "th": {
        "title": "ผู้ช่วย Edu AI",
        "font": "thai",
        "items": [
            ("lesson", "สร้างแผนสอน", "สร้างแผนการเรียนรู้"),
            ("text", "ส่งข้อความ", "แบ่งปันความรู้ท้องถิ่น"),
            ("image", "ส่งรูปภาพ", "OCR กำลังพัฒนา"),
            ("ai", "ประสบการณ์ AI", "กิจกรรมในห้องเรียน"),
            ("history", "ประวัติของฉัน", "คำขอล่าสุด"),
            ("help", "ช่วยเหลือ", "คำสั่งและการสนับสนุน"),
        ],
    },
}


def load_font(group: str, size: int, *, bold: bool = False) -> ImageFont.FreeTypeFont:
    weight = "bold" if bold else "regular"
    candidates = FONT_CANDIDATES[group][weight]
    for path in candidates:
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default(size=size)


def draw_icon(draw: ImageDraw.ImageDraw, kind: str, cx: int, cy: int, color: tuple[int, int, int]) -> None:
    line = 18
    thin = 12
    if kind == "lesson":
        draw.rounded_rectangle((cx - 90, cy - 75, cx + 90, cy + 70), radius=10, outline=color, width=line)
        draw.line((cx - 45, cy - 75, cx - 45, cy + 70), fill=color, width=thin)
        for offset, length in [(-35, 80), (5, 80), (45, 65)]:
            draw.line((cx - 20, cy + offset, cx - 20 + length, cy + offset), fill=color, width=thin)
    elif kind == "text":
        draw.rounded_rectangle((cx - 82, cy - 88, cx + 82, cy + 88), radius=10, outline=color, width=line)
        for offset, length in [(-38, 93), (2, 93), (42, 70)]:
            draw.line((cx - 45, cy + offset, cx - 45 + length, cy + offset), fill=color, width=thin)
    elif kind == "image":
        draw.rounded_rectangle((cx - 92, cy - 72, cx + 92, cy + 72), radius=10, outline=color, width=line)
        draw.ellipse((cx + 32, cy - 42, cx + 60, cy - 14), fill=color)
        points = [(cx - 74, cy + 52), (cx - 22, cy), (cx + 14, cy + 38), (cx + 44, cy + 10), (cx + 76, cy + 52)]
        draw.line(points, fill=color, width=thin, joint="curve")
    elif kind == "ai":
        draw.ellipse((cx - 78, cy - 78, cx + 78, cy + 78), outline=color, width=line)
        draw.line((cx - 40, cy - 6, cx + 40, cy - 6), fill=color, width=thin)
        draw.line((cx - 20, cy + 34, cx + 20, cy + 34), fill=color, width=thin)
        draw.ellipse((cx - 44, cy - 38, cx - 20, cy - 14), fill=color)
        draw.ellipse((cx + 20, cy - 38, cx + 44, cy - 14), fill=color)
        draw.line((cx - 82, cy - 102, cx - 58, cy - 70), fill=color, width=thin)
        draw.line((cx + 82, cy - 102, cx + 58, cy - 70), fill=color, width=thin)
    elif kind == "history":
        draw.arc((cx - 82, cy - 82, cx + 82, cy + 82), 25, 325, fill=color, width=line)
        draw.line((cx - 84, cy - 78, cx - 88, cy - 22), fill=color, width=line)
        draw.line((cx, cy, cx, cy - 52), fill=color, width=thin)
        draw.line((cx, cy, cx + 44, cy + 24), fill=color, width=thin)
    elif kind == "help":
        draw.ellipse((cx - 82, cy - 82, cx + 82, cy + 82), outline=color, width=line)
        draw.arc((cx - 36, cy - 42, cx + 36, cy + 24), 195, 425, fill=color, width=thin)
        draw.line((cx, cy + 26, cx, cy + 38), fill=color, width=thin)
        draw.ellipse((cx - 10, cy + 60, cx + 10, cy + 80), fill=color)


def draw_centered_text(
    draw: ImageDraw.ImageDraw,
    rect: tuple[int, int, int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
) -> None:
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = rect[0] + ((rect[2] - rect[0]) - text_w) / 2
    y = rect[1] + ((rect[3] - rect[1]) - text_h) / 2 - bbox[1]
    draw.text((x, y), text, font=font, fill=fill)


def draw_left_text(
    draw: ImageDraw.ImageDraw,
    xy: tuple[int, int],
    text: str,
    font: ImageFont.FreeTypeFont,
    fill: tuple[int, int, int],
) -> None:
    draw.text(xy, text, font=font, fill=fill)


def make_menu(language: str, output_dir: Path) -> Path:
    config = MENUS[language]
    image = Image.new("RGB", (WIDTH, HEIGHT), (248, 250, 252))
    draw = ImageDraw.Draw(image)

    label_font = load_font(config["font"], 64, bold=True)
    sub_font = load_font(config["font"], 34)

    for index, (icon, label, sub) in enumerate(config["items"]):
        col = index % COLS
        row = index // COLS
        x = col * CELL_W
        y = row * CELL_H
        content_y = y
        available_h = CELL_H
        bg, accent = PALETTE[index]

        draw.rectangle((x, content_y, x + CELL_W, content_y + available_h), fill=bg)
        draw.rectangle((x, content_y, x + 18, content_y + available_h), fill=accent)
        draw_icon(draw, icon, x + 190, content_y + available_h // 2 - 24, accent)

        text_x = x + 360
        center_y = content_y + available_h // 2
        draw_left_text(draw, (text_x, center_y - 104), label, label_font, (15, 23, 42))
        draw_left_text(draw, (text_x, center_y + 4), sub, sub_font, (71, 85, 105))

    for col in range(1, COLS):
        x = col * CELL_W
        draw.line((x, 0, x, HEIGHT), fill=(226, 232, 240), width=3)
    for row in range(1, ROWS):
        y = row * CELL_H
        draw.line((0, y, WIDTH, y), fill=(226, 232, 240), width=3)
    draw.rectangle((2, 2, WIDTH - 3, HEIGHT - 3), outline=(203, 213, 225), width=4)

    output_path = output_dir / f"rich_menu_{language}.png"
    image.save(output_path, optimize=True)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate LINE Rich Menu PNG assets.")
    parser.add_argument("--output-dir", type=Path, default=Path("data/line"))
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)
    for language in ("th", "ms", "en"):
        output_path = make_menu(language, args.output_dir)
        size_kb = output_path.stat().st_size / 1024
        print(f"{output_path} ({size_kb:.1f} KB)")


if __name__ == "__main__":
    main()
