from fastapi import APIRouter

from .application_config import application_config_router
from .company_config import company_config_router
from .dashboards import dashboards_router
from .laws import laws_router
from .legal_acts import legal_acts_router
from .public import public_router
from .summary import summary_router
from .user import user_router

router = APIRouter(tags=["API"])
router.include_router(public_router)
router.include_router(summary_router)
router.include_router(laws_router)
router.include_router(legal_acts_router)
router.include_router(company_config_router)
router.include_router(user_router)
router.include_router(application_config_router)
router.include_router(dashboards_router)

__all__ = ["router"]
