from __future__ import annotations

import json
import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Annotated

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
class AuthSettings:
    tenant_id: str
    api_audience: str
    api_scope: str
    spa_client_id: str
    admin_emails: frozenset[str]
    presales_by_email: dict[str, str]

    @classmethod
    def from_env(cls) -> AuthSettings:
        keys = ("ENTRA_TENANT_ID", "ENTRA_API_AUDIENCE", "ENTRA_API_SCOPE",
                "ENTRA_SPA_CLIENT_ID", "TRACKER_ADMIN_EMAILS", "TRACKER_PRESALES_EMAIL_MAP")
        missing = [key for key in keys if not os.getenv(key)]
        if missing:
            raise RuntimeError(f"Microsoft sign-in is not configured: {', '.join(missing)}")
        try:
            mapping = json.loads(os.environ["TRACKER_PRESALES_EMAIL_MAP"])
        except (ValueError, TypeError) as exc:
            raise RuntimeError("TRACKER_PRESALES_EMAIL_MAP must be a JSON object") from exc
        if not isinstance(mapping, dict) or not mapping:
            raise RuntimeError("TRACKER_PRESALES_EMAIL_MAP must map work emails to Presales names")
        roster = {name.casefold(): name for name in PRESALES_NAMES}
        try:
            normalized = {email.strip().casefold(): roster[name.strip().casefold()]
                          for email, name in mapping.items()}
        except (AttributeError, KeyError) as exc:
            raise RuntimeError("Presales email mapping contains an unknown team name") from exc
        if len(normalized) != len(PRESALES_NAMES) or set(normalized.values()) != set(PRESALES_NAMES):
            raise RuntimeError("Presales email mapping must contain each of the eight team members once")
        admins = frozenset(email.strip().casefold() for email in
                           os.environ["TRACKER_ADMIN_EMAILS"].split(",") if email.strip())
        if not admins or admins.intersection(normalized):
            raise RuntimeError("Administrator emails must be present and distinct from Presales emails")
        return cls(os.environ["ENTRA_TENANT_ID"], os.environ["ENTRA_API_AUDIENCE"],
                   os.environ["ENTRA_API_SCOPE"].rsplit("/", 1)[-1],
                   os.environ["ENTRA_SPA_CLIENT_ID"], admins, normalized)

class TokenValidator:
    def __init__(self, settings: AuthSettings):
        self.settings = settings
        self.jwks = PyJWKClient(f"https://login.microsoftonline.com/{settings.tenant_id}/discovery/v2.0/keys")
        self.issuer = f"https://login.microsoftonline.com/{settings.tenant_id}/v2.0"

    def validate(self, token: str) -> AuthenticatedUser:
        try:
            key = self.jwks.get_signing_key_from_jwt(token)
            claims = jwt.decode(token, key.key, algorithms=["RS256"],
                                audience=self.settings.api_audience, issuer=self.issuer,
                                options={"require": ["exp", "iat", "iss", "aud", "tid", "oid", "scp"]})
        except jwt.PyJWTError as exc:
            raise HTTPException(401, "Invalid or expired API access token") from exc
        if (claims["tid"] != self.settings.tenant_id or claims.get("ver") != "2.0"
                or claims.get("azp") != self.settings.spa_client_id
                or self.settings.api_scope not in claims["scp"].split()):
            raise HTTPException(403, "This account is not authorized for the tracker API")
        email = str(claims.get("preferred_username") or "").strip().casefold()
        if email in self.settings.admin_emails:
            presales = None
        else:
            presales = self.settings.presales_by_email.get(email)
            if presales is None:
                raise HTTPException(403, "This work account is not on the tracker access list")
        return AuthenticatedUser(claims["oid"], email, claims.get("name") or email, presales)


@lru_cache
def configured_validator() -> TokenValidator:
    return TokenValidator(AuthSettings.from_env())


def current_user(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AuthenticatedUser:
    if credentials is None or credentials.scheme.casefold() != "bearer":
        raise HTTPException(401, "Microsoft work account sign-in required")
    try:
        validator = configured_validator()
    except RuntimeError as exc:
        raise HTTPException(503, str(exc)) from exc
    return validator.validate(credentials.credentials)
