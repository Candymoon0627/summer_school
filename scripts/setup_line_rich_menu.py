import argparse
import sys
from pathlib import Path

import httpx

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.config import get_settings

RICH_MENU_SIZE = {"width": 2500, "height": 1686}
MENU_COMMANDS = [
    "/menu_lesson",
    "/menu_submit_text",
    "/menu_submit_image",
    "/menu_ai_experience",
    "/menu_history",
    "/menu_help",
]
CHAT_BAR_TEXT = {
    "th": "เมนู",
    "ms": "Menu",
    "en": "Menu",
}


def main() -> None:
    parser = argparse.ArgumentParser(description="Create three language-specific LINE Rich Menus.")
    parser.add_argument("--th-image", required=True, type=Path)
    parser.add_argument("--ms-image", required=True, type=Path)
    parser.add_argument("--en-image", required=True, type=Path)
    parser.add_argument(
        "--set-default",
        choices=["th", "ms", "en"],
        help="Optionally set one created menu as the default rich menu for all users.",
    )
    args = parser.parse_args()

    settings = get_settings()
    if not settings.line_channel_access_token:
        raise SystemExit("LINE_CHANNEL_ACCESS_TOKEN is required.")

    created: dict[str, str] = {}
    for language, image_path in {
        "th": args.th_image,
        "ms": args.ms_image,
        "en": args.en_image,
    }.items():
        rich_menu_id = create_rich_menu(settings.line_channel_access_token, language)
        upload_rich_menu_image(settings.line_channel_access_token, rich_menu_id, image_path)
        created[language] = rich_menu_id
        print(f"Created {language}: {rich_menu_id}")

    if args.set_default:
        set_default_rich_menu(settings.line_channel_access_token, created[args.set_default])
        print(f"Set default rich menu: {args.set_default}")

    print("\nAdd these to .env:")
    print(f"LINE_RICH_MENU_ID_TH={created['th']}")
    print(f"LINE_RICH_MENU_ID_MS={created['ms']}")
    print(f"LINE_RICH_MENU_ID_EN={created['en']}")


def create_rich_menu(access_token: str, language: str) -> str:
    payload = {
        "size": RICH_MENU_SIZE,
        "selected": True,
        "name": f"edu-ai-main-{language}",
        "chatBarText": CHAT_BAR_TEXT[language],
        "areas": _six_button_areas(),
    }
    with httpx.Client(timeout=20) as client:
        response = client.post(
            "https://api.line.me/v2/bot/richmenu",
            json=payload,
            headers=_json_headers(access_token),
        )
        response.raise_for_status()
        return response.json()["richMenuId"]


def upload_rich_menu_image(access_token: str, rich_menu_id: str, image_path: Path) -> None:
    if not image_path.exists():
        raise FileNotFoundError(image_path)
    content_type = _image_content_type(image_path)
    with httpx.Client(timeout=30) as client:
        response = client.post(
            f"https://api-data.line.me/v2/bot/richmenu/{rich_menu_id}/content",
            content=image_path.read_bytes(),
            headers={
                "Authorization": f"Bearer {access_token}",
                "Content-Type": content_type,
            },
        )
        response.raise_for_status()


def set_default_rich_menu(access_token: str, rich_menu_id: str) -> None:
    with httpx.Client(timeout=20) as client:
        response = client.post(
            f"https://api.line.me/v2/bot/user/all/richmenu/{rich_menu_id}",
            headers=_json_headers(access_token),
        )
        response.raise_for_status()


def _six_button_areas() -> list[dict]:
    width = RICH_MENU_SIZE["width"] // 2
    height = RICH_MENU_SIZE["height"] // 3
    areas = []
    for index, command in enumerate(MENU_COMMANDS):
        col = index % 2
        row = index // 2
        areas.append(
            {
                "bounds": {
                    "x": col * width,
                    "y": row * height,
                    "width": width,
                    "height": height,
                },
                "action": {
                    "type": "message",
                    "text": command,
                },
            }
        )
    return areas


def _json_headers(access_token: str) -> dict[str, str]:
    return {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }


def _image_content_type(image_path: Path) -> str:
    suffix = image_path.suffix.lower()
    if suffix in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if suffix == ".png":
        return "image/png"
    raise ValueError("Rich Menu image must be PNG or JPEG.")


if __name__ == "__main__":
    main()
