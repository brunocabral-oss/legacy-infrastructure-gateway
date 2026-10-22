"""Authorization and Role-Based Access Control (RBAC) helpers."""

from collections.abc import Callable

from fastapi import HTTPException, status

from lig.security.authentication import AuthenticatedUser


def require_role(*allowed_roles: str) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    """Dependency factory restricting endpoints to callers with specific roles."""

    def role_checker(user: AuthenticatedUser) -> AuthenticatedUser:
        if user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=(
                    f"Access denied: role '{user.role}' is not authorized. "
                    f"Required: {allowed_roles}"
                ),
            )
        return user

    return role_checker
