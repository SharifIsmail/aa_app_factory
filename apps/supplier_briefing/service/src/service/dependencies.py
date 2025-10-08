from functools import lru_cache

from dotenv import load_dotenv
from fastapi import Header, HTTPException
from loguru import logger

from service.settings import Settings


@lru_cache
def with_settings() -> Settings:
    load_dotenv(verbose=True)

    # mypy complains about missing named arguments (required attributes without a default)
    loaded_settings = Settings()  # type: ignore
    logger.info(f"Loaded settings: {loaded_settings}")
    return loaded_settings


def get_token(authorization: str = Header(...)) -> str:
    # this enables to run the service locally during development
    if authorization.startswith("Bearer "):
        return authorization[len("Bearer ") :]
    raise HTTPException(status_code=400, detail="Invalid authorization header")
