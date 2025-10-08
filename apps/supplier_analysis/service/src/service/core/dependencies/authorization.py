from functools import lru_cache
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status
from fastapi.requests import Request

from service.core.aleph_alpha_api_auth_service import AlephAlphaApiAuthService
from service.core.services.auth_service import AuthService
from service.core.utils.auth_utils import (
    extract_bearer_token,
    extract_bearer_token_from_request,
)
from service.dependencies import with_settings
from service.settings import Settings


def with_authorization_service_url(
    settings: Annotated[Settings, Depends(with_settings)],
) -> str:
    return settings.pharia_auth_service_url


class NoAuthService(AuthService):
    def is_valid_token(
        self, token: str | None, expected_permissions: tuple[str, ...]
    ) -> bool:
        return True


@lru_cache(maxsize=1)
def with_auth_service(
    authorization_service_url: Annotated[str, Depends(with_authorization_service_url)],
) -> AuthService:
    auth_service = (
        NoAuthService()
        if authorization_service_url == "none"
        else AlephAlphaApiAuthService(authorization_service_url)
    )
    return auth_service


def with_user_token(
    authorization: Annotated[str | None, Header()] = None,
) -> str | None:
    token = extract_bearer_token(authorization)
    return token


class PermissionsChecker:  # pylint: disable=too-few-public-methods
    def __init__(self, permissions: tuple[str, ...]):
        self.permissions = permissions

    def __call__(
        self,
        request: Request,
        auth_service: Annotated[AuthService, Depends(with_auth_service)],
    ) -> None:
        token = extract_bearer_token_from_request(request)
        try:
            if not auth_service.is_valid_token(token, self.permissions):
                raise HTTPException(status.HTTP_401_UNAUTHORIZED)
        except RuntimeError:
            raise HTTPException(status.HTTP_500_INTERNAL_SERVER_ERROR)


access_permission = PermissionsChecker(("AccessAssistant",))
admin_permission = PermissionsChecker(("Admin",))
