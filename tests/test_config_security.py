from app.config import Settings


def test_default_cors_origins_are_local_only_in_testing(monkeypatch):
    monkeypatch.setenv("TESTING", "1")
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    test_settings = Settings(_env_file=None)

    assert "*" not in test_settings.cors_origins_list
    assert "http://localhost:3000" in test_settings.cors_origins_list
    assert "http://testserver" in test_settings.cors_origins_list


def test_default_cors_origins_are_closed_in_production(monkeypatch):
    monkeypatch.delenv("TESTING", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("CORS_ORIGINS", raising=False)

    test_settings = Settings(_env_file=None)

    assert test_settings.cors_origins_list == []


def test_wildcard_cors_is_ignored_in_production(monkeypatch):
    monkeypatch.delenv("TESTING", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("CORS_ORIGINS", "*")

    test_settings = Settings(_env_file=None)

    assert test_settings.cors_origins_list == []


def test_rate_limit_proxy_headers_are_disabled_by_default(monkeypatch):
    monkeypatch.delenv("TESTING", raising=False)
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.delenv("RATE_LIMIT_TRUST_PROXY_HEADERS", raising=False)

    test_settings = Settings(_env_file=None)

    assert test_settings.rate_limit_trust_proxy_headers is False
