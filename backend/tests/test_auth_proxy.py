import os
from types import SimpleNamespace

import httpx
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://unused")
from app.auth import proxy

ORIGIN = "https://tracker-app-two-swart.vercel.app"


@pytest.fixture
def setup(monkeypatch):
    monkeypatch.setenv("NEON_AUTH_BASE_URL", "https://auth.example/auth")
    monkeypatch.setenv("FRONTEND_ORIGIN", ORIGIN)
    monkeypatch.setattr(proxy.AccessSettings, "from_env", lambda: SimpleNamespace(
        identity=lambda email: ("Kushal Shah", None)))
    calls = []

    class Upstream:
        def __init__(self, **kwargs):
            pass

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            pass

        async def request(self, method, url, **kwargs):
            calls.append((method, url, kwargs))
            if url.endswith("sign-in/email"):
                return httpx.Response(200, json={"user": {"emailVerified": True}}, headers=[
                    ("set-cookie", "__Secure-neon-auth.session_token=test-session; Domain=auth.example; Path=/auth; Max-Age=604800; Secure; HttpOnly; SameSite=None; Partitioned"),
                    ("set-cookie", "__Secure-neon-auth.session_data=test-data; Path=/; Secure; SameSite=None; Partitioned"),
                    ("set-auth-jwt", "test-jwt"),
                    ("set-cookie", "unrelated=value; Path=/"),
                ])
            return httpx.Response(200, json={"token": "test-jwt"})

    monkeypatch.setattr(proxy.httpx, "AsyncClient", Upstream)
    app = FastAPI()
    app.include_router(proxy.router)
    with TestClient(app, base_url=ORIGIN) as client:
        yield client, calls


def test_sign_in_session_round_trip(setup):
    client, calls = setup
    response = client.post("/api/auth/neon/sign-in/email", headers={"Origin": ORIGIN},
                           json={"email": "kushal.shah@invecto.com", "password": "test-only"})
    assert response.status_code == 200
    assert response.headers["set-auth-jwt"] == "test-jwt"
    cookies = response.headers.get_list("set-cookie")
    assert len(cookies) == 2
    assert all("SameSite=Lax" in c and "HttpOnly" in c and "Secure" in c for c in cookies)
    assert all("Partitioned" not in c and "Domain=" not in c and "Path=/;" in c for c in cookies)
    assert response.headers["cache-control"] == "no-store"
    client.cookies.set("vercel-token", "must-not-forward")
    assert client.get("/api/auth/neon/token?disableCookieCache=true").json()["token"] == "test-jwt"
    headers = calls[-1][2]["headers"]
    assert "test-session" in headers["Cookie"]
    assert "vercel-token" not in headers["Cookie"]
    assert headers["Origin"] == ORIGIN
    assert headers["x-neon-auth-middleware"] == "true"
    assert calls[-1][2]["params"]["disableCookieCache"] == "true"


@pytest.mark.parametrize("origin", [None, "https://evil.example", "null"])
def test_mutations_require_exact_origin(setup, origin):
    client, calls = setup
    headers = {"Origin": origin} if origin else {}
    assert client.post("/api/auth/neon/sign-out", json={}, headers=headers).status_code == 403
    assert not calls


def test_unknown_paths_and_cross_site_are_blocked(setup):
    client, calls = setup
    assert client.get("/api/auth/neon/admin/list-users").status_code == 404
    assert client.get("/api/auth/neon/token", headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
    assert not calls


def test_signup_uses_approved_name(setup):
    client, calls = setup
    assert client.post("/api/auth/neon/sign-up/email", headers={"Origin": ORIGIN},
                       json={"email": "kushal.shah@invecto.com", "name": "Fake Admin",
                             "password": "test-only"}).status_code == 200
    assert b'"name": "Kushal Shah"' in calls[0][2]["content"]


def test_invalid_body_and_configuration(setup, monkeypatch):
    client, calls = setup
    assert client.post("/api/auth/neon/sign-in/email", headers={"Origin": ORIGIN}, json=[]).status_code == 422
    monkeypatch.setenv("NEON_AUTH_BASE_URL", "http://insecure.example")
    assert client.get("/api/auth/neon/token").status_code == 503
    assert not calls


def test_cookie_expiry_is_preserved():
    cookie = proxy.first_party_cookie("__Secure-neon-auth.session_token=; Max-Age=0; Expires=Thu, 01 Jan 1970 00:00:00 GMT; Partitioned; SameSite=None")
    assert "Max-Age=0" in cookie and "Expires=Thu, 01 Jan 1970" in cookie
    assert "Partitioned" not in cookie


def test_upstream_failure_is_safe(setup, monkeypatch):
    client, _ = setup

    async def failed_request(*args, **kwargs):
        raise httpx.ConnectError("internal details must not escape")

    monkeypatch.setattr(proxy.httpx.AsyncClient, "request", failed_request)
    result = client.get("/api/auth/neon/token")
    assert result.status_code == 502
    assert "internal details" not in result.text


def test_unapproved_email_cannot_sign_up(setup, monkeypatch):
    from fastapi import HTTPException
    client, calls = setup

    def denied(email):
        raise HTTPException(403, "Email is not approved")

    monkeypatch.setattr(proxy.AccessSettings, "from_env", lambda: SimpleNamespace(identity=denied))
    response = client.post("/api/auth/neon/sign-up/email", headers={"Origin": ORIGIN},
                           json={"email": "outsider@example.com", "password": "test-only"})
    assert response.status_code == 403
    assert response.json()["message"] == "Email is not approved"
    assert not calls
