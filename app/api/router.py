"""HTTP endpoints for semantic product search."""

from typing import Any

from fastapi import APIRouter, Request

from app.api.schemas import (
    FaucetSearchRequest,
    LengthFilterRequest,
    SearchRequest,
    ShowerSystemSearchRequest,
    TileSearchRequest,
    WidthFilterRequest,
)
from app.data.categories import ENDPOINTS

router = APIRouter()
SEARCH_TAGS = ["Search"]
PAGE_SIZE = 10


def _paginate(items: list[str], page: int) -> list[str]:
    """Return a single page of IDs with fixed page size."""
    start = (page - 1) * PAGE_SIZE
    end = start + PAGE_SIZE
    return items[start:end]


async def _search(
    request: Request,
    endpoint: str,
    query: str,
    page: int,
    filters: dict[str, Any] | None = None,
) -> list[str]:
    """Run search for a specific endpoint category and optional filters."""
    engine = request.app.state.engine
    category_id = ENDPOINTS[endpoint]["category_id"]
    results = await engine.search(category_id, query, filters)
    return _paginate(results, page)


@router.post(
    "/faucets",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search faucets",
    description="Semantic faucet search with optional hole spacing compatibility filter.",
    response_description="Ordered list of matching product IDs.",
)
async def search_faucets(body: FaucetSearchRequest, request: Request) -> list[str]:
    """Search faucet products."""
    return await _search(
        request,
        "faucets",
        body.query,
        body.page,
        {
            "holeSpacingCompatibility": body.holeSpacingCompatibility,
        },
    )


@router.post(
    "/tiles",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search tiles",
    description="Semantic tile search with optional location filters.",
    response_description="Ordered list of matching product IDs.",
)
async def search_tiles(body: TileSearchRequest, request: Request) -> list[str]:
    """Search tile products."""
    return await _search(
        request,
        "tiles",
        body.query,
        body.page,
        {
            "locations": body.locations,
        },
    )


@router.post(
    "/shower-systems",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search shower systems",
    description="Semantic shower system search with optional tub spout filter.",
    response_description="Ordered list of matching product IDs.",
)
async def search_shower_systems(
    body: ShowerSystemSearchRequest, request: Request
) -> list[str]:
    """Search shower system products."""
    return await _search(
        request,
        "shower-systems",
        body.query,
        body.page,
        {
            "hasTubSpout": body.hasTubSpout,
        },
    )


@router.post(
    "/vanities",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search vanities",
    description="Semantic vanity search with optional maximum length filter.",
    response_description="Ordered list of matching product IDs.",
)
async def search_vanities(body: LengthFilterRequest, request: Request) -> list[str]:
    """Search vanity products."""
    return await _search(
        request,
        "vanities",
        body.query,
        body.page,
        {
            "lengthMax": body.lengthMax,
        },
    )


@router.post(
    "/lightings",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search lightings",
    description="Semantic lighting search with optional maximum length filter.",
    response_description="Ordered list of matching product IDs.",
)
async def search_lightings(body: LengthFilterRequest, request: Request) -> list[str]:
    """Search lighting products."""
    return await _search(
        request,
        "lightings",
        body.query,
        body.page,
        {
            "lengthMax": body.lengthMax,
        },
    )


@router.post(
    "/shower-glasses",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search shower glasses",
    description="Semantic shower glass search with optional maximum length filter.",
    response_description="Ordered list of matching product IDs.",
)
async def search_shower_glasses(
    body: LengthFilterRequest, request: Request
) -> list[str]:
    """Search shower glass products."""
    return await _search(
        request,
        "shower-glasses",
        body.query,
        body.page,
        {
            "lengthMax": body.lengthMax,
        },
    )


@router.post(
    "/tub-doors",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search tub doors",
    description="Semantic tub door search with optional maximum length filter.",
    response_description="Ordered list of matching product IDs.",
)
async def search_tub_doors(body: LengthFilterRequest, request: Request) -> list[str]:
    """Search tub door products."""
    return await _search(
        request,
        "tub-doors",
        body.query,
        body.page,
        {
            "lengthMax": body.lengthMax,
        },
    )


@router.post(
    "/mirrors",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search mirrors",
    description="Semantic mirror search with optional maximum width filter.",
    response_description="Ordered list of matching product IDs.",
)
async def search_mirrors(body: WidthFilterRequest, request: Request) -> list[str]:
    """Search mirror products."""
    return await _search(
        request,
        "mirrors",
        body.query,
        body.page,
        {
            "widthMax": body.widthMax,
        },
    )


@router.post(
    "/tubs",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search tubs",
    description="Semantic tub search.",
    response_description="Ordered list of matching product IDs.",
)
async def search_tubs(body: SearchRequest, request: Request) -> list[str]:
    """Search tub products."""
    return await _search(request, "tubs", body.query, body.page)


@router.post(
    "/toilets",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search toilets",
    description="Semantic toilet search.",
    response_description="Ordered list of matching product IDs.",
)
async def search_toilets(body: SearchRequest, request: Request) -> list[str]:
    """Search toilet products."""
    return await _search(request, "toilets", body.query, body.page)


@router.post(
    "/paints",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search paints",
    description="Semantic paint search.",
    response_description="Ordered list of matching product IDs.",
)
async def search_paints(body: SearchRequest, request: Request) -> list[str]:
    """Search paint products."""
    return await _search(request, "paints", body.query, body.page)


@router.post(
    "/lvps",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search LVPs",
    description="Semantic LVP flooring search.",
    response_description="Ordered list of matching product IDs.",
)
async def search_lvps(body: SearchRequest, request: Request) -> list[str]:
    """Search LVP products."""
    return await _search(request, "lvps", body.query, body.page)


@router.post(
    "/tub-fillers",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search tub fillers",
    description="Semantic tub filler search.",
    response_description="Ordered list of matching product IDs.",
)
async def search_tub_fillers(body: SearchRequest, request: Request) -> list[str]:
    """Search tub filler products."""
    return await _search(request, "tub-fillers", body.query, body.page)


@router.post(
    "/towel-bars",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search towel bars",
    description="Semantic towel bar search.",
    response_description="Ordered list of matching product IDs.",
)
async def search_towel_bars(body: SearchRequest, request: Request) -> list[str]:
    """Search towel bar products."""
    return await _search(request, "towel-bars", body.query, body.page)


@router.post(
    "/wallpapers",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search wallpapers",
    description="Semantic wallpaper search.",
    response_description="Ordered list of matching product IDs.",
)
async def search_wallpapers(body: SearchRequest, request: Request) -> list[str]:
    """Search wallpaper products."""
    return await _search(request, "wallpapers", body.query, body.page)


@router.post(
    "/toilet-paper-holders",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search toilet paper holders",
    description="Semantic toilet paper holder search.",
    response_description="Ordered list of matching product IDs.",
)
async def search_toilet_paper_holders(
    body: SearchRequest, request: Request
) -> list[str]:
    """Search toilet paper holder products."""
    return await _search(request, "toilet-paper-holders", body.query, body.page)


@router.post(
    "/robe-hooks",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search robe hooks",
    description="Semantic robe hook search.",
    response_description="Ordered list of matching product IDs.",
)
async def search_robe_hooks(body: SearchRequest, request: Request) -> list[str]:
    """Search robe hook products."""
    return await _search(request, "robe-hooks", body.query, body.page)


@router.post(
    "/towel-rings",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search towel rings",
    description="Semantic towel ring search.",
    response_description="Ordered list of matching product IDs.",
)
async def search_towel_rings(body: SearchRequest, request: Request) -> list[str]:
    """Search towel ring products."""
    return await _search(request, "towel-rings", body.query, body.page)


@router.post(
    "/shelves",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search shelves",
    description="Semantic shelf search.",
    response_description="Ordered list of matching product IDs.",
)
async def search_shelves(body: SearchRequest, request: Request) -> list[str]:
    """Search shelf products."""
    return await _search(request, "shelves", body.query, body.page)


@router.post(
    "/flooring",
    tags=SEARCH_TAGS,
    response_model=list[str],
    summary="Search flooring",
    description="Semantic flooring search across configured flooring category.",
    response_description="Ordered list of matching product IDs.",
)
async def search_flooring(body: SearchRequest, request: Request) -> list[str]:
    """Search flooring products."""
    return await _search(request, "flooring", body.query, body.page)
