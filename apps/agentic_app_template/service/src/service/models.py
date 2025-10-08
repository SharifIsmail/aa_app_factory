from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]


class QuoteResponse(BaseModel):
    quote: str
