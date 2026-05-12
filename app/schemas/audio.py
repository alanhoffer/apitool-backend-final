from pydantic import BaseModel
from typing import Optional


class ChatRequest(BaseModel):
    message: str
    chatId: Optional[str] = None


class ChatResponse(BaseModel):
    text: str
    chatId: Optional[str] = None


class AudioResponse(BaseModel):
    """Respuesta del endpoint POST /api/audio segun IAPORVOZ.md."""
    text: str
    audio_url: Optional[str] = None
    chatId: Optional[str] = None
    transcript: Optional[str] = None
