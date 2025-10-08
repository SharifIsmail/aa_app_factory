import os
import re
import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, Optional

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Request,
    Response,
)
from fastapi.responses import FileResponse, HTMLResponse

from service.core.dependencies.authorization import access_permission
from service.dependencies import with_kernel
from service.kernel import Json, Kernel
from service.lksg_core.agent_extract_company_data.data_agent_main import (
    create_work_log as create_company_data_work_log,
)
from service.lksg_core.agent_extract_company_data.data_agent_main import (
    extract_company_data,
)
from service.lksg_core.agent_extract_company_risks.risks_agent_main import (
    create_work_log as create_risks_work_log,
)
from service.lksg_core.agent_extract_company_risks.risks_agent_main import (
    extract_company_risks,
)
from service.lksg_core.models import TaskStatus, WorkLog
from service.lksg_core.persistence_service import persistence_service
from service.models import HealthResponse

router: APIRouter = APIRouter()


class SearchStatus(str, Enum):
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


# Simple container for storing work logs
class WorkLogManager:
    def __init__(self) -> None:
        # Simple dictionary storage - no locks
        self._work_logs: Dict[str, WorkLog] = {}

    def get(self, execution_id: str) -> Optional[WorkLog]:
        return self._work_logs.get(execution_id)

    def set(self, execution_id: str, work_log: WorkLog) -> None:
        self._work_logs[execution_id] = work_log

    def contains(self, execution_id: str) -> bool:
        return execution_id in self._work_logs

    def update_status(self, execution_id: str, status: TaskStatus) -> bool:
        if execution_id in self._work_logs:
            self._work_logs[execution_id].status = status
            return True
        return False


# Create a single instance of WorkLogManager for the application
work_log_manager = WorkLogManager()


# Dependency to get the WorkLogManager instance
def get_work_log_manager() -> WorkLogManager:
    return work_log_manager


@router.get("/health")
async def health() -> HealthResponse:
    return HealthResponse(status="ok")


@router.post("/quote")
async def quote(
    request: Request,
    #    token: str = Depends(get_token),
    kernel: Kernel = Depends(with_kernel),
) -> Json:
    # skill = Skill(namespace="app", name="quote")
    # response = await kernel.run(skill, token, await request.json())
    response = "some hardcoded response--aaasdasdas" + datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )
    return response


@router.post("/company-data-search", dependencies=[Depends(access_permission)])
async def company_data_search(
    request: Request,
    background_tasks: BackgroundTasks,
    work_log_manager: WorkLogManager = Depends(get_work_log_manager),
) -> Json:
    data = await request.json()
    if "company_name" not in data or "country_id" not in data:
        raise HTTPException(
            status_code=400,
            detail="Missing required fields: company_name and country_id",
        )

    # Get the research type from the request data, default to comprehensive if not provided
    research_type = data.get("research_type", "comprehensive")

    execution_id = str(uuid.uuid4())

    # Create work log and store it in the manager
    work_log = create_company_data_work_log(
        research_type=research_type, work_log_id=execution_id
    )
    work_log.status = TaskStatus.IN_PROGRESS
    work_log_manager.set(execution_id, work_log)

    background_tasks.add_task(
        extract_company_data,
        data["company_name"],
        execution_id,
        work_log,
        research_type,
    )
    return {
        "status": "OK",
        "id": execution_id,
    }


@router.get(
    "/company-data-search-status/{uuid}", dependencies=[Depends(access_permission)]
)
async def company_data_search_status(
    uuid: str, work_log_manager: WorkLogManager = Depends(get_work_log_manager)
) -> Json:
    if not work_log_manager.contains(uuid):
        raise HTTPException(
            status_code=404, detail=f"Search job with ID {uuid} not found"
        )

    work_log = work_log_manager.get(uuid)
    if work_log is None:
        raise HTTPException(
            status_code=404, detail=f"Search job with ID {uuid} not found"
        )

    return {
        "status": work_log.status.value if work_log.status else "UNKNOWN",
        "uuid": uuid,
        "tasks": work_log.tasks if work_log.tasks else [],
        "tool_logs": work_log.tool_logs if work_log.tool_logs else [],
        "extracted_data": work_log.extracted_data if work_log.extracted_data else {},
    }


@router.delete("/company-data-search/{uuid}", dependencies=[Depends(access_permission)])
async def stop_company_data_search(
    uuid: str, work_log_manager: WorkLogManager = Depends(get_work_log_manager)
) -> Json:
    try:
        if not work_log_manager.contains(uuid):
            raise HTTPException(status_code=404, detail="Search job not found")

        # TODO: Implement logic to stop the search task
        # task = active_tasks.get(uuid)
        # if task:
        #     task.cancel()
        #     try:
        #         await task  # Await to handle cancellation
        #     except asyncio.CancelledError:
        #         pass  # Task was cancelled
        #     del active_tasks[uuid]

        # Mark the task as stopped/failed
        work_log_manager.update_status(uuid, TaskStatus.FAILED)

        return {"status": "STOPPED", "uuid": uuid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/company-data-search/{uuid}/report/{report_type}",
    dependencies=[Depends(access_permission)],
)
async def get_company_report(
    uuid: str,
    report_type: str,
    download: bool = False,
) -> Response:
    company_data = persistence_service.get_company_data_by_uuid(uuid)

    if company_data is None:
        raise HTTPException(
            status_code=404, detail=f"Company data not found for UUID: {uuid}"
        )

    if report_type == "data":
        if not company_data["company_data_report_path"]:
            raise HTTPException(status_code=404, detail="Company data report not found")
        report_path = company_data["company_data_report_path"]
        filename = (
            re.sub(r"\W+", "_", company_data["name"]).lower() + "_company_data.html"
        )
    elif report_type == "risks":
        if not company_data["risks_report_path"]:
            raise HTTPException(status_code=404, detail="Risks report not found")
        report_path = company_data["risks_report_path"]
        filename = re.sub(r"\W+", "_", company_data["name"]).lower() + "_risks.html"
    else:
        raise HTTPException(
            status_code=400, detail="Invalid report type. Use 'data' or 'risks'"
        )

    if download:
        return FileResponse(path=report_path, filename=filename, media_type="text/html")
    else:
        return HTMLResponse(content=open(report_path, "r", encoding="utf-8").read())


@router.get("/companies", dependencies=[Depends(access_permission)])
async def get_companies_list() -> Json:
    """
    Get a list of all previously processed companies.

    Returns:
        List of company data including UUID, name, and report availability
    """
    try:
        companies = persistence_service.list_cached_companies()

        response_data = []
        for company in companies:
            response_data.append(
                {
                    "uuid": company["uuid"],
                    "name": company["name"],
                    "hasCompanyDataReport": company["company_data_report_path"]
                    is not None,
                    "hasRisksReport": company["risks_report_path"] is not None,
                    "processingDate": os.path.getmtime(company["path"]),
                }
            )

        response_data.sort(key=lambda x: x["processingDate"], reverse=True)

        for item in response_data:
            item["processingDate"] = datetime.fromtimestamp(
                item["processingDate"]
            ).strftime("%Y-%m-%d %H:%M:%S")

        return response_data
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(
            status_code=500, detail=f"Error fetching company list: {str(e)}"
        )


@router.post("/company-risks-research", dependencies=[Depends(access_permission)])
async def company_risks_research(
    request: Request,
    background_tasks: BackgroundTasks,
    work_log_manager: WorkLogManager = Depends(get_work_log_manager),
) -> Json:
    """
    Endpoint for initiating company risks research.
    """
    try:
        data = await request.json()
        if "company_name" not in data:
            raise HTTPException(
                status_code=400, detail="Missing required field: company_name"
            )

        company_name = data["company_name"]

        # Get the research type from the request data, default to comprehensive if not provided
        research_type = data.get("research_type", "comprehensive")

        # Use the new fetch_cached_company_by_name method
        matching_company = persistence_service.fetch_cached_company_by_name(
            company_name
        )

        if not matching_company:
            raise HTTPException(
                status_code=404,
                detail=f"Company '{company_name}' not found in processed data",
            )

        execution_id = str(uuid.uuid4())

        # Create work log and store it in the manager
        num_iterations = 5 if research_type == "comprehensive" else 1
        work_log = create_risks_work_log(
            research_type=research_type,
            work_log_id=execution_id,
            num_iterations=num_iterations,
        )
        work_log.status = TaskStatus.IN_PROGRESS
        work_log_manager.set(execution_id, work_log)

        # Prepare company data in the format expected by extract_company_risks
        company_data = {
            "company_name": matching_company["name"],
            **matching_company["data"],  # Include all the parsed XML data
        }

        # Start the risk research in the background
        background_tasks.add_task(
            extract_company_risks, company_data, execution_id, work_log
        )

        return {
            "status": "success",
            "id": execution_id,
            "company_name": matching_company["name"],
            "message": "Company risks research initiated",
        }
    except Exception as e:
        import traceback

        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/company-risks-research-status/{uuid}", dependencies=[Depends(access_permission)]
)
async def company_risks_research_status(
    uuid: str, work_log_manager: WorkLogManager = Depends(get_work_log_manager)
) -> Json:
    if not work_log_manager.contains(uuid):
        raise HTTPException(
            status_code=404, detail=f"Risks research job with ID {uuid} not found"
        )

    work_log = work_log_manager.get(uuid)
    if work_log is None:
        raise HTTPException(
            status_code=404, detail=f"Work log with ID {uuid} not found"
        )

    return {
        "status": work_log.status.value,
        "uuid": uuid,
        "tasks": work_log.tasks,
        "tool_logs": work_log.tool_logs,
        "extracted_data": work_log.extracted_data,
    }


@router.delete(
    "/company-risks-research/{uuid}", dependencies=[Depends(access_permission)]
)
async def stop_company_risks_research(
    uuid: str, work_log_manager: WorkLogManager = Depends(get_work_log_manager)
) -> Json:
    try:
        if not work_log_manager.contains(uuid):
            raise HTTPException(status_code=404, detail="Risks research job not found")

        # Mark the task as stopped/failed
        work_log_manager.update_status(uuid, TaskStatus.FAILED)

        return {"status": "STOPPED", "uuid": uuid}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/company-risks-research/{uuid}/report", dependencies=[Depends(access_permission)]
)
async def get_risk_report(
    uuid: str,
    download: bool = False,
) -> Response:
    risk_data = persistence_service.get_risk_data_by_uuid(uuid)

    if risk_data is None:
        raise HTTPException(
            status_code=404, detail=f"Risk data not found for UUID: {uuid}"
        )

    if not risk_data["risks_report_path"]:
        raise HTTPException(status_code=404, detail="Risks report not found")

    report_path = risk_data["risks_report_path"]
    filename = f"{uuid}_risks.html"

    if download:
        return FileResponse(path=report_path, filename=filename, media_type="text/html")
    else:
        return HTMLResponse(content=open(report_path, "r", encoding="utf-8").read())
