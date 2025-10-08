from urllib.parse import urljoin

import requests
from fastapi import status
from requests import Response

from service.core.services.auth_service import AuthService, UserProfile


class UnexpectedStatusCodeOnAuthCheck(RuntimeError):
    def __init__(self, status_code: int) -> None:
        super().__init__(f"Unexpected status code when checking auth: {status_code}")


class AlephAlphaApiAuthService(AuthService):  # pylint: disable=too-few-public-methods
    # the path is zitadel specific and may need to be adjusted
    # for other providers
    USER_INFO_PATH = "oidc/v1/userinfo"

    def __init__(self, authorization_service_url: str, iam_issuer_url: str) -> None:
        self._authorization_service_url = authorization_service_url
        self._iam_issuer_url = iam_issuer_url

    def is_valid_token(
        self, token: str | None, expected_permissions: tuple[str, ...]
    ) -> bool:
        if not token:
            return False

        formatted_sufficient_permissions = [
            {"permission": f"{permission}"} for permission in expected_permissions
        ]
        url = urljoin(self._authorization_service_url, "check_privileges")
        headers = self._build_headers(token)
        response = requests.post(
            url, json=formatted_sufficient_permissions, headers=headers
        )
        self._raise_on_unexpected_status(response)
        return response.status_code == status.HTTP_200_OK and (
            len(formatted_sufficient_permissions) == 0
            or any(el in formatted_sufficient_permissions for el in (response.json()))
        )

    def get_profile(self, token: str) -> UserProfile:
        url = urljoin(self._iam_issuer_url, self.USER_INFO_PATH)
        headers = self._build_headers(token)
        response = requests.post(url, headers=headers)
        response.raise_for_status()

        data = response.json()
        return UserProfile(
            email=data["email"],
            family_name=data["family_name"],
            given_name=data["given_name"],
            name=data["name"],
            preferred_username=data["preferred_username"],
            sub=data["sub"],
        )

    def _raise_on_unexpected_status(self, response: Response) -> None:
        if response.status_code not in {
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
        }:
            raise UnexpectedStatusCodeOnAuthCheck(response.status_code)

    def _build_headers(self, token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}
