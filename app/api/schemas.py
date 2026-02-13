"""Request models for search endpoints exposed in Swagger/OpenAPI."""

from typing import List, Optional

from pydantic import BaseModel, Field


class SearchRequest(BaseModel):
    """Base request model for text search endpoints."""

    query: str = Field(
        ...,
        description="Free-text semantic query.",
        examples=["matte black faucet"],
    )
    page: int = Field(
        default=1,
        ge=1,
        description="Pagination page number (1-based). Each page contains 10 product IDs.",
        examples=[1],
    )


class FaucetSearchRequest(SearchRequest):
    """Faucet search request with optional hole spacing filter."""

    holeSpacingCompatibility: Optional[str] = Field(
        default=None,
        description="Optional faucet hole spacing compatibility: Single Hole, Widespread, or Centerset.",
        examples=["Single Hole"],
    )


class TileSearchRequest(SearchRequest):
    """Tile search request with optional placement/location filters."""

    locations: Optional[List[str]] = Field(
        default=None,
        description="Optional tile locations. Supported values: wall, floor, shower_wall, shower_floor.",
        examples=[["floor", "shower_wall"]],
    )


class ShowerSystemSearchRequest(SearchRequest):
    """Shower system search request with optional tub spout filter."""

    hasTubSpout: Optional[bool] = Field(
        default=None,
        description="If true/false, returns only shower systems matching the tub spout flag.",
        examples=[True],
    )


class LengthFilterRequest(SearchRequest):
    """Search request with optional maximum product length filter."""

    lengthMax: Optional[float] = Field(
        default=None,
        description="Optional maximum length value used by length-aware categories.",
        examples=[60.0],
    )


class WidthFilterRequest(SearchRequest):
    """Search request with optional maximum product width filter."""

    widthMax: Optional[float] = Field(
        default=None,
        description="Optional maximum width value used by width-aware categories.",
        examples=[36.0],
    )
