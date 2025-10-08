"""FastAPI server that serves BaFin legal act metadata and HTML content."""

from __future__ import annotations

import os
from textwrap import dedent
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from external_sources.python_module.my_provider import (
    DEFAULT_ENDPOINT_BASE_URL,
    ENDPOINT_ENV_VAR,
    SOURCE_ID,
)
from external_sources.shared.dataset import (
    build_expression_url,
    ensure_dataset,
    iter_cached_records,
)

app = FastAPI(
    title="BaFin Legal Act Provider",
    description="Reference implementation for serving BaFin legal act content.",
)


def _base_url(request: Request) -> str:
    """Return the base URL to use for expression links."""
    configured = os.environ.get(ENDPOINT_ENV_VAR)
    if configured:
        return configured.rstrip("/")
    return str(request.base_url).rstrip("/")


def _should_force_refresh(request: Request) -> bool:
    """Check whether the caller requested a dataset refresh."""
    flag = request.query_params.get("refresh", "")
    return flag.lower() in {"1", "true", "yes"}


def _record_to_payload(record, expression_url: str) -> dict[str, Any]:
    """Convert a cached record to a JSON serialisable payload."""
    return {
        "source_id": SOURCE_ID,
        "identifier": record.identifier,
        "title": record.title,
        "expression_url": expression_url,
        "pdf_url": record.pdf_url,
        "publication_date": record.publication_date,
        "document_type": record.document_type,
        "document_type_label": record.document_type.title(),
        "eurovoc_labels": list(record.eurovoc_labels),
        "summary": record.summary,
        "source_url": record.source_url,
    }


@app.get("/", response_class=JSONResponse)
async def healthcheck() -> dict[str, str]:
    """Simple health endpoint."""
    return {"status": "ok", "default_expression_base": DEFAULT_ENDPOINT_BASE_URL}


@app.get("/legal-acts", response_class=JSONResponse)
async def list_legal_acts(request: Request) -> list[dict[str, Any]]:
    """Enumerate the available legal acts as JSON metadata."""
    base_url = _base_url(request)
    try:
        dataset = ensure_dataset(force_refresh=_should_force_refresh(request))
    except Exception as exc:  # pragma: no cover - delegated to provider env
        raise HTTPException(status_code=503, detail=f"Dataset unavailable: {exc}") from exc
    payload: list[dict[str, Any]] = []
    for record in iter_cached_records(dataset):
        expression_url = build_expression_url(base_url, record.identifier)
        payload.append(_record_to_payload(record, expression_url))
    return payload


@app.get("/legal-acts/{identifier}", response_class=HTMLResponse)
async def render_legal_act(identifier: str, request: Request) -> HTMLResponse:
    """Render the HTML article that corresponds to a legal act."""
    base_url = _base_url(request)
    try:
        dataset = ensure_dataset(force_refresh=_should_force_refresh(request))
    except Exception as exc:  # pragma: no cover
        raise HTTPException(status_code=503, detail=f"Dataset unavailable: {exc}") from exc
    for record in iter_cached_records(dataset):
        if record.identifier != identifier:
            continue
        expression_url = build_expression_url(base_url, record.identifier)
        html = dedent(
            f"""
            <!doctype html>
            <html lang="en">
              <head>
                <meta charset="utf-8" />
                <title>{record.title}</title>
              </head>
              <body>
                <article
                  data-law-monitoring="legal-act"
                  data-expression-url="{expression_url}"
                  data-source-id="{SOURCE_ID}"
                >
                  {record.html_body}
                </article>
              </body>
            </html>
            """
        ).strip()
        return HTMLResponse(content=html, status_code=200)

    raise HTTPException(status_code=404, detail=f"Unknown legal act: {identifier}")
