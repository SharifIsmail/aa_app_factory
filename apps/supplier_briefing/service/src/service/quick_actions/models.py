from enum import Enum
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field

from service.quick_actions.summarize_business_partner.models import (
    PartnerData,
    SummarizeBusinessPartnerParams,
)


class QuickAction(str, Enum):
    """Supported quick actions."""

    SUMMARIZE_BUSINESS_PARTNER = "summarize_business_partner"


class SummarizeBusinessPartnerRequest(BaseModel):
    flow_name: Literal["summarize_business_partner"]
    filter_params: SummarizeBusinessPartnerParams


QuickActionFilterRequest = Annotated[
    Union[SummarizeBusinessPartnerRequest],
    Field(discriminator="flow_name"),
]


QuickActionData = Union[PartnerData]


class QuickActionFilterResponse(BaseModel):
    success: bool
    data: List[QuickActionData]
    error: Optional[str] = None
