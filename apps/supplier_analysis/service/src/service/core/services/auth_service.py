from abc import ABC, abstractmethod


class AuthService(ABC):
    @abstractmethod
    def is_valid_token(
        self, token: str | None, expected_permissions: tuple[str, ...]
    ) -> bool: ...
