import traceback
from datetime import date, datetime
from enum import Enum
from functools import lru_cache
from typing import Annotated, Callable, Iterator, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from fastapi_pagination.cursor import CursorParams
from loguru import logger
from pydantic import BaseModel, Field

from service.api.dependencies import get_law_data_service
from service.core.dependencies.authorization import access_permission
from service.law_data_service import LawDataService
from service.models import (
    Category,
    LawData,
    LawDataWithCursorPagination,
    LawDataWithPagination,
    Pagination,
)

laws_router = APIRouter(dependencies=[Depends(access_permission)])


def _handle_simple_search(
    search_query: str,
    search_method: Callable[[str], list[LawData]],
    search_type_name: str,
) -> list[LawData]:
    """
    Generic handler for simple search endpoints to reduce code duplication.

    Args:
        search_query: The search query string
        search_method: The service method to call
        search_type_name: Name of search type for logging and error messages

    Returns:
        List of matching laws

    Raises:
        HTTPException: If there's an error during the search
    """
    try:
        laws = search_method(search_query)

        logger.info(
            f"{search_type_name.title()} search '{search_query}' found {len(laws)} laws"
        )
        return laws

    except Exception as e:
        logger.error(
            f"Error searching laws by {search_type_name} '{search_query}': {e}"
        )
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error searching laws by {search_type_name}"
        )


class LawDataUpdateRequest(BaseModel):
    """Request model for updating law data fields."""

    category: Optional[Category] = Field(
        default=None, description="User's categorization of the law"
    )


class EurovocSearchRequest(BaseModel):
    """Request model for searching laws by Eurovoc descriptors."""

    eurovoc_descriptors: list[str] = Field(
        description="List of Eurovoc descriptors to search for",
        min_length=1,
        examples=[["environment", "climate change", "sustainable development"]],
    )


# Cache at service level
@lru_cache(maxsize=1)
def _get_cached_available_dates(
    law_data_service: LawDataService, cache_key: str
) -> list[str]:
    datetime_dates = law_data_service.get_available_law_dates()
    return [date.strftime("%Y-%m-%d") for date in datetime_dates]


@laws_router.get("/laws/dates")
async def get_available_dates(
    law_data_service: Annotated[LawDataService, Depends(get_law_data_service)],
) -> list[str]:
    """
    Get all dates that have discovered laws from the storage backend.
    Cached for 15 minutes.

    Returns:
        Array of ISO date strings representing dates with available laws
    """
    # Use current time rounded to 15-minute intervals as cache key
    cache_key = str(int(datetime.now().timestamp() // 900))
    return _get_cached_available_dates(law_data_service, cache_key)


@laws_router.get("/laws")
async def get_laws(
    law_data_service: Annotated[LawDataService, Depends(get_law_data_service)],
    start_date: Optional[date] = Query(
        None, description="Start date in YYYY-MM-DD format (optional)"
    ),
    end_date: Optional[date] = Query(
        None, description="End date in YYYY-MM-DD format (optional)"
    ),
) -> LawDataWithPagination:
    """
    Get all processed laws, optionally filtered by date range.

    Args:
        start_date: Optional start date in YYYY-MM-DD format (inclusive)
        end_date: Optional end date in YYYY-MM-DD format (inclusive)

    Returns:
        Array of processed law objects
    """
    try:
        # Convert dates to datetime objects if provided
        start_datetime = None
        end_datetime = None

        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())

        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())

        laws = law_data_service.get_laws_by_date_range(start_datetime, end_datetime)
        number_of_total_laws = law_data_service.get_total_laws()

        laws_with_pagination = LawDataWithPagination(
            law_data=laws, pagination=Pagination(total_items=number_of_total_laws)
        )

        logger.info(
            f"Retrieved {len(laws)} laws (start_date={start_date}, end_date={end_date})"
        )
        return laws_with_pagination

    except Exception as e:
        logger.error(f"Error retrieving laws for date range: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail="Error retrieving laws for date range"
        )


@laws_router.get("/v2/laws")
async def get_laws_cursor(
    law_data_service: Annotated[LawDataService, Depends(get_law_data_service)],
    cursor: Optional[str] = Query(None, description="Pagination with cursor"),
    size: int = Query(50, ge=1, le=500, description="Items per page"),
    start_date: Optional[date] = Query(
        None, description="Start date in YYYY-MM-DD format (optional)"
    ),
    end_date: Optional[date] = Query(
        None, description="End date in YYYY-MM-DD format (optional)"
    ),
) -> LawDataWithCursorPagination:
    try:
        start_datetime = None
        end_datetime = None
        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())
        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())

        cursor_params = CursorParams(size=size, cursor=cursor)
        return law_data_service.get_laws_cursor_paginated(
            cursor_params=cursor_params,
            start_date=start_datetime,
            end_date=end_datetime,
        )

    except Exception as e:
        logger.error(f"Error retrieving laws (cursor) for date range: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Error retrieving cursor page")


@laws_router.get("/laws/title-search")
async def get_laws_by_title_search(
    law_data_service: Annotated[LawDataService, Depends(get_law_data_service)],
    title: str = Query(..., min_length=1, description="Case-insensitive title search"),
) -> list[LawData]:
    """
    Search for laws by title using case-insensitive regex matching.

    Args:
        title: Search query for law titles (minimum 2 characters)

    Returns:
        Array of law objects matching the title search

    Raises:
        HTTPException: If there's an error during the search
    """
    return _handle_simple_search(title, law_data_service.search_laws_by_title, "title")


@laws_router.post("/laws/eurovoc-search")
async def get_laws_by_eurovoc(
    law_data_service: Annotated[LawDataService, Depends(get_law_data_service)],
    request: EurovocSearchRequest,
) -> list[LawData]:
    """
    Search for laws by Eurovoc descriptors using case-insensitive matching.
    Returns laws that have at least one matching Eurovoc descriptor.

    Args:
        request: EurovocSearchRequest containing the list of Eurovoc descriptors

    Returns:
        Array of law objects that match at least one Eurovoc descriptor

    Raises:
        HTTPException: If there's an error during the search or validation fails
    """
    try:
        # Extract eurovoc descriptors from request
        eurovoc_descriptors = request.eurovoc_descriptors

        # Validate input
        if not eurovoc_descriptors:
            raise HTTPException(
                status_code=400,
                detail="At least one Eurovoc descriptor must be provided",
            )

        # Filter out empty/whitespace-only descriptors
        valid_descriptors = [
            desc.strip() for desc in eurovoc_descriptors if desc.strip()
        ]

        if not valid_descriptors:
            raise HTTPException(
                status_code=400,
                detail="At least one non-empty Eurovoc descriptor must be provided",
            )

        laws = law_data_service.search_laws_by_eurovoc(valid_descriptors)

        logger.info(
            f"Eurovoc search with {len(valid_descriptors)} descriptors found {len(laws)} laws"
        )
        return laws

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            f"Error searching laws by Eurovoc descriptors {request.eurovoc_descriptors}: {e}"
        )
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail="Error searching laws by Eurovoc descriptors"
        )


@laws_router.get("/laws/document-type-search")
async def get_laws_by_document_type_search(
    law_data_service: Annotated[LawDataService, Depends(get_law_data_service)],
    document_type: str = Query(
        ..., min_length=1, description="Document type to search for"
    ),
) -> list[LawData]:
    """
    Search for laws by document type.

    Args:
        document_type: Document type to search for (e.g., 'Directive', 'Regulation')

    Returns:
        Array of law objects matching the document type

    Raises:
        HTTPException: If there's an error during the search
    """
    return _handle_simple_search(
        document_type, law_data_service.search_laws_by_document_type, "document type"
    )


@laws_router.get("/laws/journal-series-search")
async def get_laws_by_journal_series_search(
    law_data_service: Annotated[LawDataService, Depends(get_law_data_service)],
    journal_series: str = Query(
        ..., min_length=1, description="Journal series to search for"
    ),
) -> list[LawData]:
    """
    Search for laws by official journal series.

    Args:
        journal_series: Journal series to search for (e.g., 'L-Series', 'C-Series')

    Returns:
        Array of law objects matching the journal series

    Raises:
        HTTPException: If there's an error during the search
    """
    return _handle_simple_search(
        journal_series, law_data_service.search_laws_by_journal_series, "journal series"
    )


@laws_router.get("/laws/department-search")
async def get_laws_by_department_search(
    law_data_service: Annotated[LawDataService, Depends(get_law_data_service)],
    department: str = Query(
        ..., min_length=1, description="Department name to search for"
    ),
) -> list[LawData]:
    """
    Search for laws that are relevant to teams in a specific department.

    Args:
        department: Department name to search for (case-insensitive)

    Returns:
        Array of law objects that are relevant to teams in the specified department

    Raises:
        HTTPException: If there's an error during the search
    """
    return _handle_simple_search(
        department, law_data_service.search_laws_by_department, "department"
    )


@laws_router.get("/laws/eurovoc-descriptors")
async def get_all_eurovoc_descriptors(
    law_data_service: Annotated[LawDataService, Depends(get_law_data_service)],
) -> list[str]:
    """
    Get all unique Eurovoc descriptors available in the system.

    Returns:
        Array of unique Eurovoc descriptors sorted alphabetically
    """
    try:
        descriptors = law_data_service.get_all_eurovoc_descriptors()

        logger.info(f"Retrieved {len(descriptors)} unique Eurovoc descriptors")
        return descriptors

    except Exception as e:
        logger.error(f"Error retrieving Eurovoc descriptors: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail="Error retrieving Eurovoc descriptors"
        )


@laws_router.put("/law/update/{law_id}")
async def update_law_data(
    law_id: str,
    update_request: LawDataUpdateRequest,
    law_data_service: Annotated[LawDataService, Depends(get_law_data_service)],
) -> LawData:
    """
    Update specific fields of a law data record.
    Only allows updating category field via API for security.

    Args:
        law_id: The ID of the law to update
        update_request: Pydantic model containing the fields to update

    Returns:
        Updated LawData object on success

    Raises:
        HTTPException: If the update operation fails or request body is invalid
    """
    try:
        # Convert Pydantic model to dict, excluding None values
        update_fields = update_request.model_dump(exclude_none=True)

        if not update_fields:
            raise HTTPException(
                status_code=400, detail="Category field must be provided"
            )

        success, updated_law = law_data_service.update_law_data(law_id, update_fields)

        if success and updated_law:
            logger.info(
                f"Successfully updated law {law_id} with fields: {list(update_fields.keys())}"
            )
            return updated_law
        else:
            logger.error(f"Failed to update law {law_id}")
            raise HTTPException(
                status_code=500,
                detail=f"Failed to update law {law_id}",
            )
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(f"Error updating law {law_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Error updating law {law_id}: {str(e)}",
        )


class ExportScope(str, Enum):
    ALL_HITS = "all_hits"
    ALL_EVALUATED = "all_evaluated"


@laws_router.get("/laws/export-csv", response_model=None)
async def export_laws_csv(
    law_data_service: Annotated[LawDataService, Depends(get_law_data_service)],
    category: Category = Query(
        Category.RELEVANT, description="Filter by category (defaults to RELEVANT)"
    ),
    start_date: Optional[date] = Query(
        None, description="Start date in YYYY-MM-DD format (optional)"
    ),
    end_date: Optional[date] = Query(
        None, description="End date in YYYY-MM-DD format (optional)"
    ),
    export_scope: ExportScope = Query(
        ExportScope.ALL_HITS,
        description="Export scope: 'all_hits' (default, only RELEVANT) or 'all_evaluated' (Category not OPEN)",
    ),
) -> StreamingResponse:
    """
    Export laws as CSV filtered by category and optional date range.

    Args:
        category: Category to filter by (defaults to RELEVANT)
        start_date: Optional start date in YYYY-MM-DD format (inclusive)
        end_date: Optional end date in YYYY-MM-DD format (inclusive)

    Returns:
        StreamingResponse: CSV file download

    Raises:
        HTTPException: If there's an error during CSV generation
    """
    try:
        # Convert dates to datetime objects if provided
        start_datetime = None
        end_datetime = None

        if start_date:
            start_datetime = datetime.combine(start_date, datetime.min.time())

        if end_date:
            end_datetime = datetime.combine(end_date, datetime.max.time())

        # Generate CSV based on export scope
        if export_scope == ExportScope.ALL_EVALUATED:
            csv_buffer = law_data_service.generate_evaluated_laws_csv(
                start_date=start_datetime, end_date=end_datetime
            )
        else:
            csv_buffer = law_data_service.generate_laws_csv(
                category=category, start_date=start_datetime, end_date=end_datetime
            )

        # Create filename with current date and category
        today = date.today().strftime("%Y-%m-%d")
        filename = (
            f"evaluated_legal_acts_{today}.csv"
            if export_scope == ExportScope.ALL_EVALUATED
            else f"{category.value.lower()}_legal_acts_{today}.csv"
        )

        # Create streaming response
        def generate() -> Iterator[str]:
            csv_buffer.seek(0)
            while True:
                chunk = csv_buffer.read(8192)  # Read in 8KB chunks
                if not chunk:
                    break
                yield chunk

        logger.info(
            f"Exporting CSV (scope={export_scope.value}) for category {category.value} "
            f"(start_date={start_date}, end_date={end_date})"
        )

        return StreamingResponse(
            generate(),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        logger.error(f"Error exporting CSV for category {category.value}: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(
            status_code=500, detail=f"Error exporting CSV for category {category.value}"
        )
