import os
import subprocess
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Awaitable, Callable

import jwt
import uvicorn
from fastapi import FastAPI, Request, Response
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from service.api import router
from service.core.constants import get_tenant_schema_name
from service.dependencies import with_settings
from service.kernel import HttpKernel
from service.law_core.background_work.background_dispatchers import (
    start_background_dispatchers,
)
from service.law_core.persistence.pharia_data_storage_backend import (
    pharia_data_storage_backend,
)
from service.law_core.persistence.storage_backend import StorageBackendType
from service.manifest import router as manifest_router
from service.metrics import user_endpoint_requests, user_last_seen, with_metrics

settings = with_settings()


def validate_environment() -> None:
    required_vars = [
        "SERVICE_AUTHENTICATION_TOKEN",
        "SERVICE_INFERENCE_API_URL",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[dict, None]:
    validate_environment()

    # Display schema information at startup
    schema_name = get_tenant_schema_name(settings.tenant_id)
    if settings.tenant_id:
        logger.info(
            f"🏢 New Tenant: Using schema '{schema_name}' for tenant '{settings.tenant_id}'"
        )
    else:
        logger.info(f"🏢 Default Tenant: Using default schema '{schema_name}'")

    run_db_migrations()

    if (
        settings.storage_type == StorageBackendType.PHARIA_DATA.value
        or settings.storage_type == StorageBackendType.PHARIA_DATA_SYNCED_SQLITE.value
    ):
        pharia_data_storage_backend.validate_connection()

    client = HttpKernel(str(settings.pharia_kernel_url))

    start_background_dispatchers()

    yield {"kernel": client}

    await client.shutdown()


def run_db_migrations() -> None:
    """Create tenant schema if needed and run Alembic migrations."""
    from service.core.database.database_manager import DatabaseManager

    logger.info("Checking database migrations...")

    # Ensure the schema exists for the tenant
    db_url = str(settings.database_url.get_secret_value())
    engine = DatabaseManager.create_engine_from_url(db_url)

    try:
        schema_name = DatabaseManager.ensure_schema_exists(
            engine=engine, tenant_id=settings.tenant_id
        )
    finally:
        engine.dispose()

    # Set the schema in an environment variable for Alembic to pick up
    env = os.environ.copy()
    env["TENANT_SCHEMA"] = schema_name

    logger.info("Running Alembic migrations...")
    try:
        # Use a list of arguments for better security and clarity
        subprocess.run(
            ["alembic", "upgrade", "head"],
            check=True,
            text=True,
            env=env,
            capture_output=True,  # Capture stdout/stderr
        )
        logger.info("Migrations complete.")
    except subprocess.CalledProcessError as exc:
        logger.error(
            f"Migrations failed:\nSTDOUT:\n{exc.stdout}\nSTDERR:\n{exc.stderr}"
        )
        raise RuntimeError("Database migration failed") from exc


app = FastAPI(lifespan=lifespan)

# Mount icons directory - must be before generic /ui mount
app.mount("/ui/icons", StaticFiles(directory="icons"), name="icons")
app.mount("/ui", StaticFiles(directory="ui-artifacts"), name="ui")


@app.middleware("http")
async def user_tracking_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    user_id = None
    auth = request.headers.get("Authorization", "")
    if auth.startswith("Bearer "):
        token = auth[len("Bearer ") :]
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            user_id = payload.get("sub")
        except jwt.PyJWTError:
            user_id = None

    if user_id:
        user_last_seen.labels(user_id=user_id).set(time.time())

        endpoint = request.url.path
        user_endpoint_requests.labels(user_id=user_id, endpoint=endpoint).inc()

    return await call_next(request)


if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,  # type: ignore
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE", "PUT"],
        allow_headers=["*"],
    )

app.include_router(manifest_router)
app.include_router(router)

with_metrics(app)


def main() -> None:
    uvicorn.run("service.main:app", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    main()
