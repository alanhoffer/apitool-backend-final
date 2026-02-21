from pydantic import BaseModel
from typing import Optional


class AudioResponse(BaseModel):
    """Respuesta del endpoint POST /api/audio según IAPORVOZ.md."""
    text: str
    audio_url: Optional[str] = None
    chatId: Optional[str] = None
