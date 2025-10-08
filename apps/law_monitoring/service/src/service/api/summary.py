import base64
import re
import traceback
from enum import Enum
from typing import Union

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, Response
from loguru import logger

from service.core.dependencies.authorization import access_permission
from service.core.utils.utils import generate_url_hash
from service.kernel import Json
from service.law_core.background_work.workers_constants import REPORTS_FOLDER
from service.law_core.law_report_service import LawReportService
from service.law_core.models import TaskStatus, WorkLog
from service.law_core.persistence.storage_factory import get_configured_storage_backend
from service.law_core.summary.model_tools_manager import REPO_EXTRACTED_DATA
from service.law_core.summary.summary_work_log_manager import (
    create_work_log as summary_create_work_log,
)
from service.law_core.tools.fetch_webpage_div_content import FetchWebpageDivContentTool
from service.task_execution import task_execution_manager
from service.work_log import work_log_manager

summary_router = APIRouter(dependencies=[Depends(access_permission)])

# Create storage backend instance once at module level (singleton pattern)
storage_backend = get_configured_storage_backend()


class SearchStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


def run_summary_in_thread(
    law_url: str, execution_id: str, work_log: WorkLog, fetched_content: str
) -> str:
    try:
        if (
            work_log.status == TaskStatus.FAILED
            or work_log.status == TaskStatus.CANCELLED
        ):
            logger.info(f"Task {execution_id} was cancelled before execution began")
            return ""

        # For now, use the same URL for both expression and PDF since only one URL is provided
        # No metadata available in this legacy flow
        law_report_service = LawReportService(act_id=execution_id, work_log=work_log)
        return law_report_service.analyze_law_and_generate_report(
            expression_url=law_url,
            pdf_url=law_url,
            law_text=fetched_content,
            metadata=None,
        )
    except Exception as e:
        logger.error(f"Error in summary thread: {str(e)}")
        logger.error(traceback.format_exc())
        work_log.status = TaskStatus.FAILED
        return ""


@summary_router.post("/summary-start")
async def summary_start(
    request: Request,
) -> Json:
    data = await request.json()

    law_url = data["law_url"]
    execution_id = generate_url_hash(law_url)
    logger.info("Starting summary analysis with ID: {}", execution_id)

    work_log = summary_create_work_log(work_log_id=execution_id)
    work_log.status = TaskStatus.IN_PROGRESS
    work_log_manager.set(execution_id, work_log)

    fetch_tool = FetchWebpageDivContentTool(
        execution_id=execution_id,
        work_log=work_log,
        repo_key=None,
        data_storage=None,
    )
    success, result = fetch_tool.forward(law_url, div_id="eli-container")

    if not success:
        work_log.status = TaskStatus.FAILED
        work_log_manager.update_status(execution_id, TaskStatus.FAILED)
        logger.warning("URL validation failed for {}: {}", law_url, result)
        return {"status": "ERROR", "error_code": "INVALID_URL", "message": result}

    task_execution_manager.execute_task(
        execution_id,
        run_summary_in_thread,
        law_url,
        execution_id,
        work_log,
        result,
    )

    return {"status": "OK", "id": execution_id}


@summary_router.get("/summary-status/{uuid}")
async def summary_status(uuid: str) -> Json:
    if not work_log_manager.contains(uuid):
        logger.warning("Summary job with ID {} not found", uuid)
        raise HTTPException(
            status_code=404, detail=f"Summary job with ID {uuid} not found"
        )

    work_log = work_log_manager.get(uuid)

    if work_log:
        return {
            "status": work_log.status.value,
            "uuid": uuid,
            "tasks": work_log.tasks,
            "tool_logs": work_log.tool_logs,
            "extracted_data": work_log.data_storage.retrieve_all_from_repo(
                REPO_EXTRACTED_DATA
            ),
        }

    logger.error("Error fetching work_log for task {}", uuid)
    return {}


@summary_router.delete("/summary-stop/{uuid}")
async def stop_summary(
    uuid: str,
) -> Json:
    if not work_log_manager.contains(uuid):
        logger.warning("Attempted to stop non-existent summary job: {}", uuid)
        raise HTTPException(status_code=404, detail="Summary job not found")

    cancelled = task_execution_manager.cancel_task(uuid)
    work_log_manager.update_status(uuid, TaskStatus.CANCELLED)

    return {"uuid": uuid, "task_cancelled": cancelled}


@summary_router.get("/reports/{uuid}", response_model=None)
async def get_summary_report(
    uuid: str,
    report_type: str = Query(
        "html",
        regex="^(html|json|docx|pdf)$",
        description="Report type: html, json, docx, or pdf",
    ),
    download: bool = False,
    format: str = Query(
        "binary",
        regex="^(binary|base64)$",
        description="Response format: binary or base64",
    ),
) -> Union[HTMLResponse, JSONResponse, Response]:
    """
    Get the HTML, JSON, Word, or PDF report for a completed summary analysis.

    Args:
        uuid: The execution ID of the completed summary analysis
        report_type: Type of report to retrieve ('html', 'json', 'docx', or 'pdf')
        download: Whether to return as download attachment
        format: Response format ('binary' for direct download, 'base64' for encoded string)

    Returns:
        HTMLResponse, JSONResponse, or Response: The content of the requested report

    Raises:
        HTTPException: If UUID format is invalid or report not found
    """
    # Validate that uuid is a 32-character hexadecimal string (MD5-like format)
    try:
        if not re.match(r"^[a-f0-9]{32}$", uuid):
            raise ValueError("Invalid hash format")
    except ValueError:
        logger.warning("Invalid hash format provided: {}", uuid)
        raise HTTPException(status_code=400, detail=f"Invalid hash format: {uuid}")

    # Set filename based on report type
    filename = ""
    if report_type == "html":
        filename = f"act_{uuid}.html"
    elif report_type == "json":
        filename = f"act_{uuid}.json"
    elif report_type == "docx":
        filename = f"act_{uuid}.docx"
    elif report_type == "pdf":
        filename = f"act_{uuid}.pdf"

    content = storage_backend.load_file(REPORTS_FOLDER, filename)

    if content is None:
        logger.warning(
            "{} summary report not found for UUID: {}", report_type.upper(), uuid
        )
        raise HTTPException(
            status_code=404,
            detail=f"{report_type.upper()} summary report not found for UUID: {uuid}",
        )

    # Prepare response data based on report type
    content_type = ""
    response_class: type[Union[HTMLResponse, JSONResponse, Response]]
    response_content = None
    if report_type == "html":
        response_content = content
        content_type = "text/html; charset=utf-8"
        response_class = HTMLResponse
    elif report_type == "json":
        response_content = content
        content_type = "application/json; charset=utf-8"
        response_class = JSONResponse
    elif report_type in ["docx", "pdf"]:
        if format == "base64":
            # Return base64-encoded content for frontend binary handling
            if isinstance(content, bytes):
                response_content = base64.b64encode(content).decode("utf-8")
            else:
                response_content = base64.b64encode(content.encode("utf-8")).decode(
                    "utf-8"
                )
            content_type = "text/plain; charset=utf-8"
            response_class = Response
        else:
            # Return binary content as before
            response_content = content
            if report_type == "docx":
                content_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            else:  # pdf
                content_type = "application/pdf"
            response_class = Response

    # Handle download vs display
    headers = {"Content-Type": content_type}
    if download:
        headers["Content-Disposition"] = (
            f"attachment; filename=law_report_{uuid}.{report_type}"
        )

    logger.info(
        "Serving {} summary report for UUID: {} (download={}) (content-type={})",
        report_type.upper(),
        uuid,
        download,
        content_type,
    )
    return response_class(content=response_content, headers=headers)
