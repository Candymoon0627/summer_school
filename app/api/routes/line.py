import hashlib
import hmac
import json

from fastapi import APIRouter, Header, HTTPException, Request

from app.core.config import get_settings
from app.db.session import SessionLocal
from app.services.line_webhook import LineWebhookService

router = APIRouter()


@router.post("/webhook")
async def line_webhook(
    request: Request,
    x_line_signature: str | None = Header(default=None),
) -> dict:
    body = await request.body()
    _verify_signature(body, x_line_signature)

    payload = json.loads(body.decode("utf-8") or "{}")
    with SessionLocal() as db:
        result = LineWebhookService(db).handle_payload(payload)
    return {"status": "received", **result}


def _verify_signature(body: bytes, signature: str | None) -> None:
    settings = get_settings()
    if not settings.line_channel_secret:
        return
    if not signature:
        raise HTTPException(status_code=401, detail="Missing LINE signature")
    digest = hmac.new(settings.line_channel_secret.encode("utf-8"), body, hashlib.sha256).digest()
    import base64

    expected = base64.b64encode(digest).decode("utf-8")
    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid LINE signature")
