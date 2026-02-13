import logging
import numpy as np
import asyncpg
from app.config import settings

logger = logging.getLogger(__name__)


async def load_all(pool: asyncpg.Pool) -> dict:
    index = {}

    rows = await pool.fetch("""
        SELECT p.id, p.category_id, p.name,
               pad.jina_v2_clip_name_embedding::text
        FROM product p
        JOIN product_ai_data pad ON pad.product_id = p.id
    """)

    categories = {}
    for row in rows:
        cat_id = str(row["category_id"])
        if cat_id not in categories:
            categories[cat_id] = {"ids": [], "embeddings": [], "names": []}
        categories[cat_id]["ids"].append(str(row["id"]))
        categories[cat_id]["embeddings"].append(
            np.array(eval(row["jina_v2_clip_name_embedding"]), dtype=np.float32)
        )
        categories[cat_id]["names"].append(row["name"].lower())

    for cat_id, data in categories.items():
        index[cat_id] = {
            "product_ids": data["ids"],
            "embeddings": np.array(data["embeddings"]),
            "names": data["names"],
            "filters": {},
            "dimensions": {},
        }

    logger.info(
        "Loaded embeddings: %d products in %d categories", len(rows), len(categories)
    )

    faucet_rows = await pool.fetch("""
        SELECT product_id,
               single_hole_spacing_compatible,
               four_inch_hole_spacing_compatible,
               eight_inch_hole_spacing_compatible
        FROM faucet
    """)
    faucet_cat = None
    for cat_id, data in index.items():
        for row in faucet_rows:
            pid = str(row["product_id"])
            if pid in data["product_ids"]:
                faucet_cat = cat_id
                break
        if faucet_cat:
            break

    if faucet_cat:
        for row in faucet_rows:
            pid = str(row["product_id"])
            index[faucet_cat]["filters"][pid] = {
                "single_hole": row["single_hole_spacing_compatible"] or False,
                "widespread": row["eight_inch_hole_spacing_compatible"] or False,
                "centerset": row["four_inch_hole_spacing_compatible"] or False,
            }
    logger.info("Loaded faucet filters: %d rows", len(faucet_rows))

    tile_rows = await pool.fetch("""
        SELECT product_id,
               available_for_wall,
               available_for_floor,
               available_for_shower_wall,
               available_for_shower_floor
        FROM tile
    """)
    tile_cat = None
    for cat_id, data in index.items():
        for row in tile_rows:
            if str(row["product_id"]) in data["product_ids"]:
                tile_cat = cat_id
                break
        if tile_cat:
            break

    if tile_cat:
        for row in tile_rows:
            pid = str(row["product_id"])
            index[tile_cat]["filters"][pid] = {
                "wall": row["available_for_wall"] or False,
                "floor": row["available_for_floor"] or False,
                "shower_wall": row["available_for_shower_wall"] or False,
                "shower_floor": row["available_for_shower_floor"] or False,
            }
    logger.info("Loaded tile filters: %d rows", len(tile_rows))

    shower_rows = await pool.fetch("""
        SELECT product_id, has_tub_spout
        FROM shower_system
    """)
    shower_cat = None
    for cat_id, data in index.items():
        for row in shower_rows:
            if str(row["product_id"]) in data["product_ids"]:
                shower_cat = cat_id
                break
        if shower_cat:
            break

    if shower_cat:
        for row in shower_rows:
            pid = str(row["product_id"])
            index[shower_cat]["filters"][pid] = {
                "has_tub_spout": row["has_tub_spout"] or False,
            }
    logger.info("Loaded shower system filters: %d rows", len(shower_rows))

    dimension_tables = ["vanity", "mirror", "lighting", "shower_glass", "tub_door"]
    total_dims = 0

    for table in dimension_tables:
        dim_rows = await pool.fetch(f"""
            SELECT t.product_id, rp.length, rp.width
            FROM {table} t
            JOIN renderable_product rp ON rp.id = t.render_id
        """)

        dim_cat = None
        for cat_id, data in index.items():
            for row in dim_rows:
                if str(row["product_id"]) in data["product_ids"]:
                    dim_cat = cat_id
                    break
            if dim_cat:
                break

        if dim_cat:
            for row in dim_rows:
                pid = str(row["product_id"])
                index[dim_cat]["dimensions"][pid] = {
                    "length": float(row["length"]) if row["length"] else None,
                    "width": float(row["width"]) if row["width"] else None,
                }
        total_dims += len(dim_rows)

    logger.info(
        "Loaded dimensions: %d rows from %d tables",
        total_dims,
        len(dimension_tables),
    )
    logger.info(
        "Total index size: %.1f MB embeddings",
        sum(d["embeddings"].nbytes for d in index.values()) / 1024 / 1024,
    )

    tiles_category_id = settings.tiles_category_id
    flooring_id = settings.flooring_category_id

    flooring_ids = []
    flooring_embs = []
    flooring_names = []

    if settings.lvps_category_id in index:
        lvp = index[settings.lvps_category_id]
        flooring_ids.extend(lvp["product_ids"])
        flooring_embs.append(lvp["embeddings"])
        flooring_names.extend(lvp["names"])

    if tiles_category_id in index:
        tile = index[tiles_category_id]
        for i, pid in enumerate(tile["product_ids"]):
            f = tile["filters"].get(pid, {})
            if f.get("floor"):
                flooring_ids.append(pid)
                flooring_embs.append(tile["embeddings"][i : i + 1])
                flooring_names.append(tile["names"][i])

    if flooring_ids:
        index[flooring_id] = {
            "product_ids": flooring_ids,
            "embeddings": np.concatenate(flooring_embs),
            "names": flooring_names,
            "filters": {},
            "dimensions": {},
        }
    logger.info("Loaded flooring (synthetic): %d products", len(flooring_ids))

    return index
