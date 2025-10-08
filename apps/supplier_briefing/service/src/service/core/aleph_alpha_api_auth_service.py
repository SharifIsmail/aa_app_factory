from urllib.parse import urljoin

import requests
from fastapi import status
from requests import Response

from service.core.services.auth_service import AuthService


class UnexpectedStatusCodeOnAuthCheck(RuntimeError):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"Unexpected status code when checking auth: {status_code}")


class AlephAlphaApiAuthService(AuthService):  # pylint: disable=too-few-public-methods
    def __init__(self, authorization_service_url: str):
        self._authorization_service_url = authorization_service_url

    def is_valid_token(
        self, token: str | None, expected_permissions: tuple[str, ...]
    ) -> bool:
        formatted_sufficient_permissions = [
            {"permission": f"{permission}"} for permission in expected_permissions
        ]
        url = urljoin(self._authorization_service_url, "check_privileges")
        headers = {"Authorization": f"Bearer {token}"}
        response = requests.post(
            url, json=formatted_sufficient_permissions, headers=headers
        )
        self._raise_on_unexpected_status(response)
        return response.status_code == status.HTTP_200_OK and (
            len(formatted_sufficient_permissions) == 0
            or any(el in formatted_sufficient_permissions for el in (response.json()))
        )

    def _raise_on_unexpected_status(self, response: Response) -> None:
        if response.status_code not in {
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
        }:
            raise UnexpectedStatusCodeOnAuthCheck(response.status_code)
