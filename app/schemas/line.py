from pydantic import BaseModel


class LineTextEvent(BaseModel):
    event_key: str
    line_user_id: str
    message_id: str | None = None
    reply_token: str | None = None
    text: str

