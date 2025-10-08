import os
import time
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import jwt
import uvicorn
from fastapi import FastAPI, Request
from starlette.middleware.cors import CORSMiddleware
from starlette.staticfiles import StaticFiles

from service.dependencies import with_settings
from service.kernel import HttpKernel
from service.lksg_core.persistence_service import persistence_service
from service.metrics import user_endpoint_requests, user_last_seen, with_metrics
from service.routes import router

settings = with_settings()


def validate_environment() -> None:
    required_vars = [
        "SERVICE_AUTHENTICATION_TOKEN",
        "SERVICE_INFERENCE_API_URL",
        "SERVICE_COMPLETION_MODEL_NAME",
        "SERPER_API_KEY",
        "ABSTRACT_API_KEY",
    ]

    missing_vars = [var for var in required_vars if not os.getenv(var)]
    if missing_vars:
        raise ValueError(
            f"Missing required environment variables: {', '.join(missing_vars)}"
        )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[dict, None]:
    validate_environment()

    # Copy preprocessed artifacts
    preprocessed_dir = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "preprocessed_artifacts",
    )

    if os.path.exists(preprocessed_dir):
        for filename in os.listdir(preprocessed_dir):
            if filename.endswith(".html"):
                persistence_service.load_and_store_html_report(
                    source_folder=preprocessed_dir,
                    source_filename=filename,
                    target_filename=os.path.splitext(filename)[0],
                )
            elif filename.endswith(".xml"):
                persistence_service.load_and_store_xml_report(
                    source_folder=preprocessed_dir,
                    source_filename=filename,
                    target_filename=os.path.splitext(filename)[0],
                )

    client = HttpKernel(str(settings.pharia_kernel_url))
    yield {"kernel": client}
    await client.shutdown()


app = FastAPI(lifespan=lifespan)


@app.middleware("http")
async def user_tracking_middleware(request: Request, call_next):
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
        allow_methods=["GET", "POST", "DELETE"],
        allow_headers=["*"],
    )

app.include_router(router)

app.mount("/ui", StaticFiles(directory="ui-artifacts"), name="ui")

with_metrics(app)


def main() -> None:
    uvicorn.run("service.main:app", host="0.0.0.0", port=8080, reload=True)


if __name__ == "__main__":
    main()
