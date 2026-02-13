# app/api/schemas.py
from pydantic import BaseModel
from typing import Optional, List


class SearchRequest(BaseModel):
    query: str


class FaucetSearchRequest(SearchRequest):
    holeSpacingCompatibility: Optional[str] = None


class TileSearchRequest(SearchRequest):
    locations: Optional[List[str]] = None


class ShowerSystemSearchRequest(SearchRequest):
    hasTubSpout: Optional[bool] = None


class LengthFilterRequest(SearchRequest):
    lengthMax: Optional[float] = None


class WidthFilterRequest(SearchRequest):
    widthMax: Optional[float] = None
