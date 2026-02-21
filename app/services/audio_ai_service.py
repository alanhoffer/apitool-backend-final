"""
Servicio de audio para el chat por voz (IAPORVOZ).
- Recibe audio, opcionalmente transcribe con Whisper y obtiene respuesta del agente (OpenAI).
- Si OPENAI_API_KEY no está definida, devuelve mensaje informativo.
"""
from __future__ import annotations

import io
import logging
from typing import Optional

from app.config import settings

logger = logging.getLogger(__name__)

# Historial de conversación en memoria por chat_id (mensajes para el contexto).
# En producción podría persistirse en Redis/DB.
_chat_history: dict[str, list[dict]] = {}
_MAX_HISTORY_MESSAGES = 20

SYSTEM_PROMPT = (
    "Eres un asistente experto en apicultura para la app ApiTool. "
    "Respondes de forma breve y útil sobre colmenas, cosecha de miel, tratamientos, "
    "y tareas del día a día del apicultor. Responde siempre en el mismo idioma que el usuario."
)


def _get_client():
    """Cliente OpenAI solo si la API key está configurada."""
    if not settings.openai_api_key:
        return None
    try:
        from openai import OpenAI
        return OpenAI(api_key=settings.openai_api_key)
    except Exception as e:
        logger.warning("OpenAI client not available: %s", e)
        return None


def _transcribe(client, audio_bytes: bytes, content_type: str) -> Optional[str]:
    """Transcribe audio con Whisper. content_type ej: audio/m4a, audio/webm."""
    try:
        # Whisper acepta m4a, mp3, webm, etc.
        ext = "m4a"
        if "webm" in content_type:
            ext = "webm"
        elif "3gpp" in content_type or "3gp" in content_type:
            ext = "3gp"
        file_like = io.BytesIO(audio_bytes)
        file_like.name = f"audio.{ext}"
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=file_like,
        )
        return (transcript.text or "").strip() or None
    except Exception as e:
        logger.exception("Whisper transcription failed: %s", e)
        return None


def _chat_completion(client, user_text: str, chat_id: Optional[str] = None) -> Optional[str]:
    """Obtiene respuesta del modelo de chat, opcionalmente con historial."""
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if chat_id and chat_id in _chat_history:
        for msg in _chat_history[chat_id][-_MAX_HISTORY_MESSAGES:]:
            messages.append(msg)

    messages.append({"role": "user", "content": user_text})

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            max_tokens=500,
        )
        choice = response.choices[0] if response.choices else None
        if not choice or not choice.message:
            return None
        assistant_content = (choice.message.content or "").strip()

        # Guardar en historial para siguiente turno
        if chat_id:
            if chat_id not in _chat_history:
                _chat_history[chat_id] = []
            _chat_history[chat_id].append({"role": "user", "content": user_text})
            _chat_history[chat_id].append({"role": "assistant", "content": assistant_content})
            if len(_chat_history[chat_id]) > _MAX_HISTORY_MESSAGES:
                _chat_history[chat_id] = _chat_history[chat_id][-_MAX_HISTORY_MESSAGES:]

        return assistant_content
    except Exception as e:
        logger.exception("Chat completion failed: %s", e)
        return None


async def process_audio(
    audio_bytes: bytes,
    content_type: str = "audio/m4a",
    chat_id: Optional[str] = None,
) -> dict:
    """
    Procesa el audio: transcribe y obtiene respuesta del agente.
    Retorna dict con keys: text, audio_url (opcional), chatId (opcional).
    """
    client = _get_client()
    if not client:
        return {
            "text": "La funcionalidad de voz no está configurada. Añade OPENAI_API_KEY en el servidor para activarla.",
            "audio_url": None,
            "chatId": chat_id,
        }

    text_in = _transcribe(client, audio_bytes, content_type)
    if not text_in:
        return {
            "text": "No pude entender el audio. Prueba a hablar más claro o en un lugar tranquilo.",
            "audio_url": None,
            "chatId": chat_id,
        }

    text_out = _chat_completion(client, text_in, chat_id)
    if not text_out:
        return {
            "text": "No pude generar una respuesta. Inténtalo de nuevo.",
            "audio_url": None,
            "chatId": chat_id,
        }

    return {
        "text": text_out,
        "audio_url": None,  # Opcional: integrar TTS (ej. OpenAI TTS) si se desea
        "chatId": chat_id,
    }
