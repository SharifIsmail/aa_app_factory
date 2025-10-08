from abc import ABC, abstractmethod

from pydantic import BaseModel


class UserProfile(BaseModel):
    email: str
    family_name: str
    given_name: str
    name: str
    preferred_username: str
    sub: str


class AuthService(ABC):
    @abstractmethod
    def is_valid_token(
        self, token: str | None, expected_permissions: tuple[str, ...]
    ) -> bool: ...

    @abstractmethod
    def get_profile(self, token: str) -> UserProfile: ...
