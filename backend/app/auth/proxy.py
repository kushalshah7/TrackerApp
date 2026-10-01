"""First-party transport for managed Neon Auth; never stores passwords."""
import json
import os
from urllib.parse import urlsplit

import httpx
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import Response

from .neon_auth import AccessSettings

router = APIRouter()
ENDPOINTS = {
    "get-session": "GET", "token": "GET",
    "sign-in/email": "POST", "sign-up/email": "POST", "sign-out": "POST",
    "email-otp/send-verification-otp": "POST", "email-otp/verify-email": "POST",
    "forget-password/email-otp": "POST", "email-otp/request-password-reset": "POST",
    "email-otp/reset-password": "POST",
}


def first_party_cookie(value: str) -> str | None:
    parts = value.split(";")
    if not parts[0].strip().startswith("__Secure-neon-auth."):
        return None
    retained = [part.strip() for part in parts[1:] if part.strip().split("=", 1)[0].lower()
                not in {"domain", "path", "samesite", "partitioned", "secure", "httponly"}]
    return "; ".join([parts[0].strip(), *retained, "Path=/", "HttpOnly", "Secure", "SameSite=Lax"])


@router.api_route("/api/auth/neon/{path:path}", methods=["GET", "POST"])
async def auth_proxy(path: str, request: Request):
    if ENDPOINTS.get(path) != request.method:
        raise HTTPException(404, "Unknown sign-in endpoint")
    origin = os.getenv("FRONTEND_ORIGIN", "https://tracker-app-two-swart.vercel.app").rstrip("/")
    if request.headers.get("origin") not in {None, origin} or (
        request.method == "POST" and request.headers.get("origin") != origin
    ) or request.headers.get("sec-fetch-site") == "cross-site":
        raise HTTPException(403, "Invalid origin")
    upstream = os.getenv("NEON_AUTH_BASE_URL", "").rstrip("/")
    parsed = urlsplit(upstream)
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.query or parsed.fragment:
        raise HTTPException(503, "Tracker sign-in is not configured")
    body = await request.body()
    if len(body) > 16384:
        raise HTTPException(413, "Sign-in request is too large")
    if request.method == "POST" and path != "sign-out":
        try:
            payload = json.loads(body)
            if not isinstance(payload, dict) or not isinstance(payload.get("email"), str):
                raise ValueError
            name, _ = AccessSettings.from_env().identity(payload["email"])
        except (ValueError, TypeError):
            raise HTTPException(422, "Enter a valid work email") from None
        except RuntimeError:
            raise HTTPException(503, "Tracker sign-in is not configured") from None
        if path == "sign-up/email":
            payload["name"] = name
            body = json.dumps(payload).encode()
    headers = {"Content-Type": "application/json", "Origin": origin,
               "x-neon-auth-middleware": "true"}
    cookies = [part.strip() for part in request.headers.get("cookie", "").split(";")
               if part.strip().split("=", 1)[0].startswith("__Secure-neon-auth.")]
    if cookies:
        headers["Cookie"] = "; ".join(cookies)
    try:
        async with httpx.AsyncClient(timeout=20, follow_redirects=False) as client:
            result = await client.request(request.method, upstream + "/" + path,
                                          params=request.query_params, headers=headers, content=body)
    except httpx.HTTPError:
        raise HTTPException(502, "Sign-in service unavailable. Please try again.") from None
    response = Response(result.content, status_code=result.status_code,
                        headers={"Cache-Control": "no-store", "Content-Type": result.headers.get(
                            "content-type", "application/json")})
    for header in ("set-auth-jwt", "set-auth-token"):
        if header in result.headers:
            response.headers[header] = result.headers[header]
    for value in result.headers.get_list("set-cookie"):
        cookie = first_party_cookie(value)
        if cookie:
            response.headers.append("set-cookie", cookie)
    return response
