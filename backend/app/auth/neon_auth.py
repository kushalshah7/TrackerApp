from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated
from urllib.parse import urlparse

import jwt
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jwt import PyJWKClient

from ..tracker_store import PRESALES_NAMES


bearer = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class AuthenticatedUser:
    object_id: str
    email: str
    display_name: str
    presales: str | None

    @property
    def is_admin(self) -> bool:
        return self.presales is None


@dataclass(frozen=True)
class AccessSettings:
    auth_url: str
    admin_emails: frozenset[str]
    presales_by_email: dict[str, str]

    @classmethod
    def from_env(cls) -> AccessSettings:
        auth_url = os.getenv("NEON_AUTH_BASE_URL", "").rstrip("/")
        if not auth_url.startswith("https://"):
            raise RuntimeError("NEON_AUTH_BASE_URL is not configured")
        admins_raw = os.getenv("TRACKER_ADMIN_EMAILS", "")
        mapping_raw = os.getenv("TRACKER_PRESALES_EMAIL_MAP", "")
        if not admins_raw or not mapping_raw:
            raise RuntimeError("Tracker access list is not configured")
        try:
            mapping = json.loads(mapping_raw)
            roster = {name.casefold(): name for name in PRESALES_NAMES}
            presales = {email.strip().casefold(): roster[name.strip().casefold()]
                        for email, name in mapping.items()}
        except (ValueError, AttributeError, KeyError) as exc:
            raise RuntimeError("Tracker Presales access list is invalid") from exc
        admins = frozenset(email.strip().casefold() for email in admins_raw.split(",") if email.strip())
        if (len(presales) != len(PRESALES_NAMES) or set(presales.values()) != set(PRESALES_NAMES)
                or not admins or admins.intersection(presales)):
            raise RuntimeError("Tracker access list must contain each team member exactly once")
        return cls(auth_url, admins, presales)

    @property
    def issuer(self) -> str:
        parsed = urlparse(self.auth_url)
        return f"{parsed.scheme}://{parsed.netloc}"

    def identity(self, email: str) -> tuple[str, str | None]:
        email = email.strip().casefold()
        if email in self.admin_emails:
            return email.split("@", 1)[0].replace(".", " ").title(), None
        presales = self.presales_by_email.get(email)
        if presales is None:
            raise HTTPException(403, "This email is not approved for the tracker")
        return presales, presales


class TokenValidator:
    def __init__(self, settings: AccessSettings):
        self.settings = settings
        self.jwks = PyJWKClient(f"{settings.auth_url}/.well-known/jwks.json")

    def validate(self, token: str) -> AuthenticatedUser:
        try:
            key = self.jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(token, key.key, algorithms=["EdDSA"],
                                audience=self.settings.issuer, issuer=self.settings.issuer,
                                options={"require": ["exp", "iat", "iss", "aud", "sub", "email"]})
        except jwt.PyJWTError as exc:
            raise HTTPException(401, "Invalid or expired sign-in token") from exc
        if claims.get("banned"):
            raise HTTPException(403, "This account is disabled")
        email = str(claims["email"]).strip().casefold()
        display_name, presales = self.settings.identity(email)
        if claims.get("emailVerified") is not True:
            raise HTTPException(403, "Verify your work email before accessing the tracker")
        return AuthenticatedUser(str(claims["sub"]), email, display_name, presales)


@lru_cache
def configured_validator() -> TokenValidator:
    return TokenValidator(AccessSettings.from_env())


def verified_identity(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(401, "Sign in required")
    try:
        validator = configured_validator()
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    return validator.validate(credentials.credentials)


def current_user(user: Annotated[AuthenticatedUser, Depends(verified_identity)]) -> AuthenticatedUser:
    return user
