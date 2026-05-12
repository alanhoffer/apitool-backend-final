import io
from datetime import datetime, timedelta

from app.models.subscription import Subscription


def test_ai_chat_requires_ai_access(client, auth_headers):
    response = client.post(
        '/api/ai/chat',
        json={'message': 'hola'},
        headers=auth_headers,
    )
    assert response.status_code == 403


def test_ai_chat_empty_message_returns_400(client, ai_auth_headers):
    response = client.post(
        '/api/ai/chat',
        json={'message': ''},
        headers=ai_auth_headers,
    )
    assert response.status_code == 400


def test_ai_chat_ok(client, ai_auth_headers, monkeypatch):
    import app.routers.audio as audio_router

    async def fake_process_text(user_text: str, chat_id=None):
        return {'text': 'hola', 'chatId': 'chat123'}

    monkeypatch.setattr(audio_router, 'process_text', fake_process_text)

    response = client.post(
        '/api/ai/chat',
        json={'message': 'hola'},
        headers=ai_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data['text'] == 'hola'
    assert data['chatId'] == 'chat123'


def test_audio_ok_returns_transcript(client, ai_auth_headers, monkeypatch):
    import app.routers.audio as audio_router

    async def fake_process_audio(audio_bytes: bytes, content_type: str, chat_id=None):
        return {
            'text': 'respuesta',
            'chatId': 'chat456',
            'audio_url': None,
            'transcript': 'hola mundo',
        }

    monkeypatch.setattr(audio_router, 'process_audio', fake_process_audio)

    files = {
        'audio': ('test.m4a', io.BytesIO(b'abc'), 'audio/m4a')
    }

    response = client.post(
        '/api/audio',
        files=files,
        headers=ai_auth_headers,
    )

    assert response.status_code == 200
    data = response.json()
    assert data['text'] == 'respuesta'
    assert data['chatId'] == 'chat456'
    assert data['transcript'] == 'hola mundo'


def test_ai_chat_rejects_expired_premium_subscription(client, db, test_user, auth_headers):
    db.add(
        Subscription(
            userId=test_user.id,
            tier='apicultor',
            status='active',
            expiresAt=datetime.utcnow() - timedelta(days=1),
        )
    )
    db.commit()

    response = client.post(
        '/api/ai/chat',
        json={'message': 'hola'},
        headers=auth_headers,
    )

    assert response.status_code == 403
