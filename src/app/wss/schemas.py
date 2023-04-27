
"""Schemas for the chat app."""
from pydantic import BaseModel, validator


class ChatResponse(BaseModel):
    """Chat response schema."""

    sender: str
    message: str
    type: str

    @validator("sender")
    def sender_must_be_assistant_or_human(cls, v):
        if v not in ["Assistant", "Human"]:
            raise ValueError("sender must be Assistant or Human")
        return v

    @validator("type")
    def validate_message_type(cls, v):
        if v not in ["start", "stream", "end", "error", "info"]:
            raise ValueError("type must be start, stream or end")
        return v
