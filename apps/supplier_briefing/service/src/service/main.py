import asyncio
import time
import traceback
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Awaitable, Callable

import jwt
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse
from loguru import logger
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from service.agent_core.data_management.data_documentation import (
    DataDocumentation,
)
from service.agent_core.persistence.agent_instance_store import agent_instance_store
from service.data_loading import get_schema_for_path
from service.data_preparation_state import (
    with_data_preperation_state,
)
from service.dependencies import with_settings
from service.download_and_preprocess_data import download_and_preprocess_raw_data
from service.manifest import router as manifest_router
from service.metrics import user_endpoint_requests, user_last_seen, with_metrics
from service.routes import router
from service.tracing import initialize_tracing
from service.work_log_manager import WorkLogManager


async def run_data_download_and_preprocessing() -> None:
    settings = with_settings()
    data_preparation_state = with_data_preperation_state()

    if not settings.enable_data_preparation:
        logger.info(
            "Data preparation is disabled (SERVICE_ENABLE_DATA_PREPARATION=false)"
        )
        data_preparation_state.set_completed()
        return

    try:
        data_preparation_state.set_in_progress()
        logger.info("Starting background data download and preprocessing...")

        await asyncio.to_thread(download_and_preprocess_raw_data)

        data_preparation_state.set_completed()
        logger.info("Background data download and preprocessing completed")
    except Exception as e:
        data_preparation_state.set_failed(str(e))
        logger.error(f"Background data download and preprocessing failed: {e}")


async def pre_generate_data_descriptions_and_schemas() -> None:
    data_files = DataDocumentation.get_all_data_files_with_descriptions()
    for data_file in data_files:
        get_schema_for_path(data_file.file_path)


@asynccontextmanager
async def lifespan(
    _: FastAPI,
) -> AsyncGenerator[None, None]:
    asyncio.create_task(run_data_download_and_preprocessing())
    asyncio.create_task(pre_generate_data_descriptions_and_schemas())

    stop_event: asyncio.Event = asyncio.Event()

    async def purge_loop() -> None:
        manager = WorkLogManager.get_instance()
        while not stop_event.is_set():
            try:
                removed_agents = agent_instance_store.purge_expired()
                removed_worklogs = manager.purge_expired()
                if removed_agents > 0 or removed_worklogs > 0:
                    logger.info(
                        f"Background purge removed agents={removed_agents}, work_logs={removed_worklogs}"
                    )
            except Exception as e:
                logger.warning(f"Background purge error: {e}")
            # Wait up to 10 minutes, but wake up immediately when stopping
            try:
                await asyncio.wait_for(stop_event.wait(), timeout=600)
            except asyncio.TimeoutError:
                pass

    task = asyncio.create_task(purge_loop())
    try:
        yield
    finally:
        stop_event.set()
        await task


initialize_tracing()
app = FastAPI(debug=True, lifespan=lifespan)

# Mount icons directory - must be before generic /ui mount
app.mount("/ui/icons", StaticFiles(directory="icons"), name="icons")
app.mount("/ui", StaticFiles(directory="ui-artifacts"), name="ui")

settings = with_settings()


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        f"🚨 GLOBAL ERROR HANDLER - Unhandled exception on {request.method} {request.url}"
    )
    logger.error(f"🚨 Exception type: {type(exc).__name__}")
    logger.error(f"🚨 Exception message: {str(exc)}")
    logger.error(f"🚨 Full traceback:")
    logger.error(traceback.format_exc())

    return JSONResponse(
        status_code=500,
        content={
            "detail": f"Internal server error: {str(exc)}",
            "type": type(exc).__name__,
            "path": str(request.url.path),
        },
    )


@app.middleware("http")
async def user_tracking_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    # User tracking logic
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

    # Process request
    response = await call_next(request)
    return response


if settings.enable_cors:
    app.add_middleware(
        CORSMiddleware,  # type: ignore
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

app.include_router(manifest_router)
app.include_router(router)

with_metrics(app)


def main() -> None:
    uvicorn.run("service.main:app", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    main()
