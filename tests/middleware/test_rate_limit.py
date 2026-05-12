from starlette.requests import Request

from app.middleware.rate_limit import RateLimitMiddleware
import app.middleware.rate_limit as rate_limit_module


async def _dummy_app(scope, receive, send):
    return None


def _build_request(headers: dict[str, str], client_host: str) -> Request:
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/auth/login",
        "raw_path": b"/auth/login",
        "query_string": b"",
        "headers": [(key.lower().encode("latin-1"), value.encode("latin-1")) for key, value in headers.items()],
        "client": (client_host, 12345),
        "server": ("testserver", 80),
    }
    return Request(scope)


def test_rate_limit_ignores_forwarded_headers_by_default(monkeypatch):
    middleware = RateLimitMiddleware(_dummy_app)
    monkeypatch.setattr(rate_limit_module.settings, "rate_limit_trust_proxy_headers", False)
    monkeypatch.setattr(rate_limit_module.settings, "rate_limit_trusted_proxies", "")

    request = _build_request({"x-forwarded-for": "203.0.113.10"}, client_host="198.51.100.20")

    assert middleware._get_client_ip(request) == "198.51.100.20"


def test_rate_limit_uses_forwarded_headers_for_trusted_proxy(monkeypatch):
    middleware = RateLimitMiddleware(_dummy_app)
    monkeypatch.setattr(rate_limit_module.settings, "rate_limit_trust_proxy_headers", True)
    monkeypatch.setattr(rate_limit_module.settings, "rate_limit_trusted_proxies", "10.0.0.0/8")

    request = _build_request({"x-forwarded-for": "203.0.113.10"}, client_host="10.1.2.3")

    assert middleware._get_client_ip(request) == "203.0.113.10"


def test_rate_limit_rejects_spoofed_forwarded_headers_from_untrusted_peer(monkeypatch):
    middleware = RateLimitMiddleware(_dummy_app)
    monkeypatch.setattr(rate_limit_module.settings, "rate_limit_trust_proxy_headers", True)
    monkeypatch.setattr(rate_limit_module.settings, "rate_limit_trusted_proxies", "10.0.0.0/8")

    request = _build_request({"x-forwarded-for": "203.0.113.10"}, client_host="198.51.100.20")

    assert middleware._get_client_ip(request) == "198.51.100.20"


def test_account_deletion_uses_login_grade_rate_limit():
    middleware = RateLimitMiddleware(_dummy_app)

    assert middleware._get_limit("/users/account-deletion") == middleware._get_limit("/auth/login")
