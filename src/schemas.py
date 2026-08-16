"""
Pydantic schemas for normalized book records and error records.
Provides strict schema validation and runtime type coercion.
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, HttpUrl, field_validator


class BookRecord(BaseModel):
    """
    Normalized, schema-validated book record.
    Matches the required schema with type safety and sanity constraints.
    """
    title: str = Field(..., min_length=1, description="Book title")
    product_url: HttpUrl = Field(..., description="Canonical absolute URL of the book")
    price_text: str = Field(..., description="Raw price text with currency symbol, e.g. '£51.77'")
    price_gbp: float = Field(..., gt=0.0, description="Normalized price in GBP as a positive float")
    availability_text: str = Field(..., description="Raw availability text, e.g. 'In stock (22 available)'")
    stock_count: int = Field(..., ge=0, description="Parsed number of available units in stock")
    rating_text: str = Field(..., description="Raw star rating text, e.g. 'Three'")
    rating: int = Field(..., ge=1, le=5, description="Normalized numeric star rating (1 to 5)")
    description: Optional[str] = Field(None, description="Product description if available, else None")
    source_page: HttpUrl = Field(..., description="Provenance: catalogue URL where book link was found")
    fetched_at: datetime = Field(..., description="Provenance: ISO 8601 UTC timestamp of fetch")

    @field_validator("title")
    @classmethod
    def validate_title_not_blank(cls, v: str) -> str:
        trimmed = v.strip()
        if not trimmed:
            raise ValueError("Title must not be empty or whitespace only")
        return trimmed

    model_config = {
        "json_encoders": {
            HttpUrl: str,
            datetime: lambda v: v.isoformat(),
        }
    }


class ErrorRecord(BaseModel):
    """
    Represents a rejected/invalid record that failed validation.
    Saved to output/errors.json with reasoning.
    """
    raw_record: dict
    reasons: list[str]
    rejected_at: str
