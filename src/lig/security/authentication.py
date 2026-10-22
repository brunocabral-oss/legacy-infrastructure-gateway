"""Authentication and API Key / Bearer token security module."""

import os
from dataclasses import dataclass

from fastapi import HTTPException, Request, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)
http_bearer = HTTPBearer(auto_error=False)


@dataclass
class AuthenticatedUser:
    """Identity and authorization claims of the authenticated caller."""

    actor: str
    role: str  # "reader", "operator", "admin"
    token: str


class TokenAuthenticator:
    """Manages API token verification and role mapping."""

    def __init__(self) -> None:
        # Load authorized tokens from environment or safe defaults for development
        self._tokens: dict[str, AuthenticatedUser] = {}
        self._load_tokens()

    def _load_tokens(self) -> None:
        # Default tokens for development/lab
        default_tokens = {
            "lig_reader_dev_token": AuthenticatedUser(
                actor="engineer_lab", role="reader", token="lig_reader_dev_token"
            ),
            "lig_operator_dev_token": AuthenticatedUser(
                actor="noc_operator", role="operator", token="lig_operator_dev_token"
            ),
            "lig_admin_dev_token": AuthenticatedUser(
                actor="admin_user", role="admin", token="lig_admin_dev_token"
            ),
        }
        self._tokens.update(default_tokens)

        # Allow adding tokens from environment (e.g. LIG_API_TOKEN_READER=...)
        custom_reader = os.environ.get("LIG_API_TOKEN_READER")
        if custom_reader:
            self._tokens[custom_reader] = AuthenticatedUser(
                actor="custom_reader", role="reader", token=custom_reader
            )
        custom_admin = os.environ.get("LIG_API_TOKEN_ADMIN")
        if custom_admin:
            self._tokens[custom_admin] = AuthenticatedUser(
                actor="custom_admin", role="admin", token=custom_admin
            )

    def verify_token(self, token: str) -> AuthenticatedUser | None:
        return self._tokens.get(token)


authenticator = TokenAuthenticator()


async def get_current_user(
    request: Request,
    api_key: str | None = Security(api_key_header),
    bearer: HTTPAuthorizationCredentials | None = Security(http_bearer),
) -> AuthenticatedUser:
    """FastAPI dependency verifying API key or Bearer token."""
    token = api_key or (bearer.credentials if bearer else None)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=(
                "Authentication credentials were not provided. "
                "Pass 'X-API-Key' or 'Authorization: Bearer <token>' header."
            ),
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = authenticator.verify_token(token)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired authentication credentials.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    request.state.actor = user.actor
    request.state.user_role = user.role
    return user
