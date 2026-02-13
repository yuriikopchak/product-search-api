from app.config import settings

ENDPOINTS = {
    "faucets": {
        "category_id": settings.faucets_category_id,
        "filters": ["holeSpacingCompatibility"],
    },
    "vanities": {
        "category_id": settings.vanities_category_id,
        "filters": ["lengthMax"],
    },
    "lightings": {
        "category_id": settings.lightings_category_id,
        "filters": ["lengthMax"],
    },
    "tiles": {
        "category_id": settings.tiles_category_id,
        "filters": ["locations"],
    },
    "shower-systems": {
        "category_id": settings.shower_systems_category_id,
        "filters": ["hasTubSpout"],
    },
    "tubs": {
        "category_id": settings.tubs_category_id,
        "filters": [],
    },
    "shower-glasses": {
        "category_id": settings.shower_glasses_category_id,
        "filters": ["lengthMax"],
    },
    "mirrors": {
        "category_id": settings.mirrors_category_id,
        "filters": ["widthMax"],
    },
    "toilets": {
        "category_id": settings.toilets_category_id,
        "filters": [],
    },
    "paints": {
        "category_id": settings.paints_category_id,
        "filters": [],
    },
    "lvps": {
        "category_id": settings.lvps_category_id,
        "filters": [],
    },
    "tub-fillers": {
        "category_id": settings.tub_fillers_category_id,
        "filters": [],
    },
    "towel-bars": {
        "category_id": settings.towel_bars_category_id,
        "filters": [],
    },
    "wallpapers": {
        "category_id": settings.wallpapers_category_id,
        "filters": [],
    },
    "toilet-paper-holders": {
        "category_id": settings.toilet_paper_holders_category_id,
        "filters": [],
    },
    "robe-hooks": {
        "category_id": settings.robe_hooks_category_id,
        "filters": [],
    },
    "towel-rings": {
        "category_id": settings.towel_rings_category_id,
        "filters": [],
    },
    "tub-doors": {
        "category_id": settings.tub_doors_category_id,
        "filters": ["lengthMax"],
    },
    "shelves": {
        "category_id": settings.shelves_category_id,
        "filters": [],
    },
    "flooring": {
        "category_id": settings.flooring_category_id,
        "filters": [],
    },
}
