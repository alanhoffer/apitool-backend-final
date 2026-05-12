"""
Endpoint de audio para el chat con IA (IAPORVOZ).
POST /api/audio: recibe audio y devuelve respuesta del agente (texto y opcionalmente audio).
"""
import logging
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, status, UploadFile
from sqlalchemy.orm import Session

from app.database import get_db
from app.dependencies import get_current_user_payload
from app.schemas.audio import AudioResponse, ChatRequest, ChatResponse
from app.services.audio_ai_service import process_audio, process_text
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["audio"])

MAX_AUDIO_SIZE_MB = 25


@router.post("/audio", response_model=AudioResponse)
async def post_audio(
    audio: UploadFile = File(..., description="Archivo de audio (m4a, 3gp, webm, etc.)"),
    chatId: Optional[str] = Form(None, description="ID de conversación para mantener contexto"),
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
):
    """
    Recibe un audio de voz y devuelve la respuesta del asistente de IA.
    Requiere autenticación (Bearer token).
    """
    user_id = int(payload.get("sub"))
    if not SubscriptionService(db).can_use_ai(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu plan no incluye acceso a la IA. Actualizá tu suscripción."
        )

    raw_type = (audio.content_type or "").split(";")[0].strip().lower()
    if raw_type and not raw_type.startswith("audio/"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Tipo de archivo no válido. Se espera audio (m4a, 3gp, webm, mp3).",
        )

    max_bytes = MAX_AUDIO_SIZE_MB * 1024 * 1024
    body = await audio.read()
    if len(body) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"El archivo de audio supera el tamaño máximo de {MAX_AUDIO_SIZE_MB} MB.",
        )
    if len(body) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El archivo de audio está vacío.",
        )

    content_type = (audio.content_type or "audio/m4a").split(";")[0].strip()

    try:
        result = await process_audio(
            audio_bytes=body,
            content_type=content_type,
            chat_id=chatId,
        )
        return AudioResponse(**result)
    except Exception as e:
        logger.exception("Error processing audio: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo procesar el audio.",
        )


@router.post("/ai/chat", response_model=ChatResponse)
async def post_chat(
    request: ChatRequest,
    payload: dict = Depends(get_current_user_payload),
    db: Session = Depends(get_db),
):
    user_id = int(payload.get("sub"))
    if not SubscriptionService(db).can_use_ai(user_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Tu plan no incluye acceso a la IA. Actualizá tu suscripción."
        )

    message = (request.message or "").strip()
    if not message:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="El mensaje no puede estar vacio.",
        )

    try:
        result = await process_text(
            user_text=message,
            chat_id=request.chatId,
        )
        return ChatResponse(**result)
    except Exception as e:
        logger.exception("Error processing chat: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="No se pudo procesar el chat.",
        )
