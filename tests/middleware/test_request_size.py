from fastapi import FastAPI, Request
from fastapi.testclient import TestClient

from app.middleware.request_size import PATH_PREFIX_LIMITS, RequestSizeMiddleware


def create_app(max_size: int = 5) -> FastAPI:
    app = FastAPI()
    app.add_middleware(RequestSizeMiddleware, max_size=max_size)

    @app.post("/echo")
    async def echo(request: Request):
        body = await request.body()
        return {"size": len(body)}

    return app


def test_request_size_rejects_large_stream_without_content_length():
    client = TestClient(create_app(max_size=5))

    response = client.post("/echo", content=iter([b"abc", b"def"]))

    assert response.status_code == 413
    assert "Request body too large" in response.json()["detail"]


def test_request_size_accepts_small_stream_without_content_length():
    client = TestClient(create_app(max_size=8))

    response = client.post("/echo", content=iter([b"abc", b"de"]))

    assert response.status_code == 200
    assert response.json() == {"size": 5}


def test_request_size_uses_apiary_prefix_limit_for_multipart_overhead():
    middleware = RequestSizeMiddleware(app=lambda scope, receive, send: None, max_size=5)

    assert middleware._get_max_size("/apiarys") == PATH_PREFIX_LIMITS["/apiarys"]
    assert middleware._get_max_size("/apiarys/123") == PATH_PREFIX_LIMITS["/apiarys"]
    assert middleware._get_max_size("/echo") == 5
