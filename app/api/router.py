from fastapi import APIRouter, Request
from app.api.schemas import (
    SearchRequest,
    FaucetSearchRequest,
    TileSearchRequest,
    ShowerSystemSearchRequest,
    LengthFilterRequest,
    WidthFilterRequest,
)
from app.data.categories import ENDPOINTS

router = APIRouter()


async def _search(request: Request, endpoint: str, query: str, filters: dict = None):
    engine = request.app.state.engine
    category_id = ENDPOINTS[endpoint]["category_id"]
    return await engine.search(category_id, query, filters)


@router.post("/faucets")
async def search_faucets(body: FaucetSearchRequest, request: Request):
    return await _search(
        request,
        "faucets",
        body.query,
        {
            "holeSpacingCompatibility": body.holeSpacingCompatibility,
        },
    )


@router.post("/tiles")
async def search_tiles(body: TileSearchRequest, request: Request):
    return await _search(
        request,
        "tiles",
        body.query,
        {
            "locations": body.locations,
        },
    )


@router.post("/shower-systems")
async def search_shower_systems(body: ShowerSystemSearchRequest, request: Request):
    return await _search(
        request,
        "shower-systems",
        body.query,
        {
            "hasTubSpout": body.hasTubSpout,
        },
    )


@router.post("/vanities")
async def search_vanities(body: LengthFilterRequest, request: Request):
    return await _search(
        request,
        "vanities",
        body.query,
        {
            "lengthMax": body.lengthMax,
        },
    )


@router.post("/lightings")
async def search_lightings(body: LengthFilterRequest, request: Request):
    return await _search(
        request,
        "lightings",
        body.query,
        {
            "lengthMax": body.lengthMax,
        },
    )


@router.post("/shower-glasses")
async def search_shower_glasses(body: LengthFilterRequest, request: Request):
    return await _search(
        request,
        "shower-glasses",
        body.query,
        {
            "lengthMax": body.lengthMax,
        },
    )


@router.post("/tub-doors")
async def search_tub_doors(body: LengthFilterRequest, request: Request):
    return await _search(
        request,
        "tub-doors",
        body.query,
        {
            "lengthMax": body.lengthMax,
        },
    )


@router.post("/mirrors")
async def search_mirrors(body: WidthFilterRequest, request: Request):
    return await _search(
        request,
        "mirrors",
        body.query,
        {
            "widthMax": body.widthMax,
        },
    )


@router.post("/tubs")
async def search_tubs(body: SearchRequest, request: Request):
    return await _search(request, "tubs", body.query)


@router.post("/toilets")
async def search_toilets(body: SearchRequest, request: Request):
    return await _search(request, "toilets", body.query)


@router.post("/paints")
async def search_paints(body: SearchRequest, request: Request):
    return await _search(request, "paints", body.query)


@router.post("/lvps")
async def search_lvps(body: SearchRequest, request: Request):
    return await _search(request, "lvps", body.query)


@router.post("/tub-fillers")
async def search_tub_fillers(body: SearchRequest, request: Request):
    return await _search(request, "tub-fillers", body.query)


@router.post("/towel-bars")
async def search_towel_bars(body: SearchRequest, request: Request):
    return await _search(request, "towel-bars", body.query)


@router.post("/wallpapers")
async def search_wallpapers(body: SearchRequest, request: Request):
    return await _search(request, "wallpapers", body.query)


@router.post("/toilet-paper-holders")
async def search_toilet_paper_holders(body: SearchRequest, request: Request):
    return await _search(request, "toilet-paper-holders", body.query)


@router.post("/robe-hooks")
async def search_robe_hooks(body: SearchRequest, request: Request):
    return await _search(request, "robe-hooks", body.query)


@router.post("/towel-rings")
async def search_towel_rings(body: SearchRequest, request: Request):
    return await _search(request, "towel-rings", body.query)


@router.post("/shelves")
async def search_shelves(body: SearchRequest, request: Request):
    return await _search(request, "shelves", body.query)


@router.post("/flooring")
async def search_flooring(body: SearchRequest, request: Request):
    return await _search(request, "flooring", body.query)
