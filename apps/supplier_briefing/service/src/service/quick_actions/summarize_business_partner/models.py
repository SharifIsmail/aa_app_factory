"""Data models for summarize business partner quick action."""

from pydantic import BaseModel, Field


class PartnerData(BaseModel):
    id: str
    name: str


class SummarizeBusinessPartnerParams(BaseModel):
    query: str = Field(default="", description="Search query for name and ID")
    limit: int = Field(default=100000, description="Maximum number of results")
