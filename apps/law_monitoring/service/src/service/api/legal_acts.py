from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from loguru import logger

from service.core.dependencies.authorization import access_permission
from service.law_core.eur_lex_service import EurLexServiceError, eur_lex_service
from service.models import LegalActsRequest, LegalActsResponse

legal_acts_router = APIRouter(dependencies=[Depends(access_permission)])


@legal_acts_router.post("/legal-acts/search")
async def search_legal_acts(
    request: LegalActsRequest,
) -> LegalActsResponse:
    """
    Search for legal acts published within a specified date range.

    Args:
        request: Request containing start_date, end_date, and optional limit

    Returns:
        LegalActsResponse containing the list of legal acts and metadata

    Raises:
        HTTPException: If there's an error with the request or EUR-Lex service
    """
    try:
        logger.info(
            f"Received legal acts search request: {request.start_date.date()} to {request.end_date.date()}, limit: {request.limit}"
        )

        result = eur_lex_service.get_legal_acts_by_date_range(
            start_date=request.start_date,
            end_date=request.end_date,
            limit=request.limit,
        )

        logger.info(f"Successfully retrieved {result.total_count} legal acts")
        return result

    except EurLexServiceError as e:
        logger.error(f"EUR-Lex service error: {str(e)}")
        raise HTTPException(status_code=503, detail=f"EUR-Lex service error: {str(e)}")
    except ValueError as e:
        logger.error(f"Invalid request parameters: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Invalid parameters: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error in legal acts search: {str(e)}")
        raise HTTPException(
            status_code=500, detail="Internal server error during legal acts search"
        )


@legal_acts_router.get("/legal-acts/search")
async def search_legal_acts_get(
    start_date: datetime = Query(
        ..., description="Start date for the search (YYYY-MM-DD)"
    ),
    end_date: datetime = Query(..., description="End date for the search (YYYY-MM-DD)"),
    limit: int = Query(
        1000, ge=1, le=10000, description="Maximum number of results per day"
    ),
) -> LegalActsResponse:
    """
    Search for legal acts via GET request (alternative to POST).

    Args:
        start_date: Start date for the search
        end_date: End date for the search
        limit: Maximum number of results per day

    Returns:
        LegalActsResponse containing the list of legal acts and metadata
    """
    # Convert to LegalActsRequest and delegate to the POST endpoint logic
    request = LegalActsRequest(start_date=start_date, end_date=end_date, limit=limit)
    return await search_legal_acts(request)
