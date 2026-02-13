"""
Estimate RAM usage for the current runtime scenario:
- real in-memory index produced by app.data.loader.load_all
- model footprint (configurable, default 3.0 GB)
- projected total for N workers (each worker keeps its own model + index)
"""

import argparse
import asyncio
import os
import sys
from pathlib import Path
from typing import Iterable
from urllib.parse import quote_plus

import asyncpg
import numpy as np

# Allow running as: python3 scripts/measure_memory.py
ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.data.loader import load_all

BYTES_IN_GB = 1024**3


def parse_csv_ints(value: str) -> list[int]:
    return [int(v.strip()) for v in value.split(",") if v.strip()]


def build_db_url_from_env() -> str | None:
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_user = os.getenv("DB_USER")
    db_password = os.getenv("DB_PASSWORD")
    db_sslmode = os.getenv("DB_SSLMODE", "disable")

    required = [db_host, db_port, db_name, db_user, db_password]
    if not all(required):
        return None

    return (
        "postgresql://"
        f"{quote_plus(db_user)}:{quote_plus(db_password)}@"
        f"{db_host}:{db_port}/{db_name}?sslmode={db_sslmode}"
    )


def deep_size(obj, seen: set[int] | None = None) -> int:
    if seen is None:
        seen = set()

    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)

    size = sys.getsizeof(obj)

    # Numpy arrays keep most data in contiguous buffers.
    if isinstance(obj, np.ndarray):
        return size

    if isinstance(obj, dict):
        size += sum(deep_size(k, seen) + deep_size(v, seen) for k, v in obj.items())
    elif isinstance(obj, (list, tuple, set, frozenset)):
        size += sum(deep_size(i, seen) for i in obj)

    return size


def format_gb(num_bytes: int | float) -> str:
    return f"{num_bytes / BYTES_IN_GB:.2f} GB"


def format_mb(num_bytes: int | float) -> str:
    return f"{num_bytes / (1024**2):.1f} MB"


def gather_index_stats(index: dict) -> dict[str, int]:
    category_count = len(index)
    product_refs = 0
    unique_products = set()
    embeddings_bytes = 0
    names_count = 0
    names_chars = 0
    filter_items = 0
    dimension_items = 0

    for data in index.values():
        product_ids = data["product_ids"]
        names = data["names"]
        filters = data["filters"]
        dimensions = data["dimensions"]
        embeddings = data["embeddings"]

        product_refs += len(product_ids)
        unique_products.update(product_ids)
        names_count += len(names)
        names_chars += sum(len(name) for name in names)
        embeddings_bytes += int(embeddings.nbytes)
        filter_items += len(filters)
        dimension_items += len(dimensions)

    duplicated_product_refs = product_refs - len(unique_products)

    return {
        "category_count": category_count,
        "product_refs": product_refs,
        "unique_products": len(unique_products),
        "duplicated_product_refs": duplicated_product_refs,
        "embeddings_bytes": embeddings_bytes,
        "names_count": names_count,
        "names_chars": names_chars,
        "filter_items": filter_items,
        "dimension_items": dimension_items,
    }


def print_worker_projection(
    workers: Iterable[int],
    worker_runtime_bytes: int,
    fixed_overhead_bytes: int,
    target_rams_gb: Iterable[int],
):
    print("\n=== Worker Projection ===")
    print(
        f"Per worker (index + model + runtime overhead): {format_gb(worker_runtime_bytes)}"
    )
    print(f"Fixed overhead (OS/agent/etc): {format_gb(fixed_overhead_bytes)}")

    for n in workers:
        total = fixed_overhead_bytes + worker_runtime_bytes * n
        print(f"\nWorkers: {n}")
        print(f"Estimated total RAM needed: {format_gb(total)}")
        for ram_gb in target_rams_gb:
            capacity = ram_gb * BYTES_IN_GB
            free = capacity - total
            status = "OK" if free > 0 else "NOT ENOUGH"
            print(f"  {ram_gb} GB node -> {status}, free: {format_gb(free)}")


async def run(args):
    database_url = (
        args.database_url or os.getenv("DATABASE_URL") or build_db_url_from_env()
    )
    if not database_url:
        raise RuntimeError(
            "DB connection is not set. Pass --database-url, set DATABASE_URL, "
            "or set DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD."
        )

    url = database_url.replace("+asyncpg", "")

    pool = await asyncpg.create_pool(url, min_size=1, max_size=2)
    try:
        index = await load_all(pool)
    finally:
        await pool.close()

    stats = gather_index_stats(index)
    index_total_bytes = deep_size(index)
    model_bytes = int(args.model_gb * BYTES_IN_GB)
    worker_overhead_bytes = int(args.worker_overhead_gb * BYTES_IN_GB)
    fixed_overhead_bytes = int(args.fixed_overhead_gb * BYTES_IN_GB)

    worker_runtime_bytes = index_total_bytes + model_bytes + worker_overhead_bytes

    print("=== Index Stats ===")
    print(f"Categories loaded: {stats['category_count']}")
    print(f"Product refs in index: {stats['product_refs']}")
    print(f"Unique products: {stats['unique_products']}")
    print(f"Duplicated refs (synthetic categories): {stats['duplicated_product_refs']}")
    print(f"Embeddings only: {format_mb(stats['embeddings_bytes'])}")
    print(f"Names count: {stats['names_count']}")
    print(f"Names chars total: {stats['names_chars']}")
    print(f"Filter rows in memory: {stats['filter_items']}")
    print(f"Dimension rows in memory: {stats['dimension_items']}")
    print(f"Full index deep size: {format_gb(index_total_bytes)}")

    print("\n=== Memory Inputs ===")
    print(f"Model size assumption: {args.model_gb:.2f} GB")
    print(f"Per-worker runtime overhead: {args.worker_overhead_gb:.2f} GB")
    print(f"Fixed overhead: {args.fixed_overhead_gb:.2f} GB")

    print_worker_projection(
        workers=args.workers,
        worker_runtime_bytes=worker_runtime_bytes,
        fixed_overhead_bytes=fixed_overhead_bytes,
        target_rams_gb=args.target_rams_gb,
    )


def parse_args():
    parser = argparse.ArgumentParser(
        description="Estimate RAM needs for product-search runtime."
    )
    parser.add_argument(
        "--database-url",
        default=None,
        help="DB URL; fallback is DATABASE_URL, then DB_HOST/DB_PORT/DB_NAME/DB_USER/DB_PASSWORD.",
    )
    parser.add_argument(
        "--model-gb",
        type=float,
        default=3.0,
        help="Model RAM footprint per worker in GB.",
    )
    parser.add_argument(
        "--worker-overhead-gb",
        type=float,
        default=0.5,
        help="Extra RAM per worker (python process, libs, request buffers, etc).",
    )
    parser.add_argument(
        "--fixed-overhead-gb",
        type=float,
        default=1.0,
        help="Node-level overhead outside workers (OS, monitoring, docker, etc).",
    )
    parser.add_argument(
        "--workers",
        type=parse_csv_ints,
        default=[1, 2],
        help="Comma-separated worker counts to project, e.g. 1,2",
    )
    parser.add_argument(
        "--target-rams-gb",
        type=parse_csv_ints,
        default=[8, 16],
        help="Comma-separated node RAM capacities to check, e.g. 8,16",
    )
    return parser.parse_args()


if __name__ == "__main__":
    asyncio.run(run(parse_args()))
