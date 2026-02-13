import numpy as np
from typing import Any


def score_products(
    cat_data: dict[str, Any],
    query: str,
    query_emb: np.ndarray,
) -> list[tuple[str, float]]:
    query_lower = query.lower().strip()
    query_tokens = set(query_lower.split())

    product_ids = cat_data["product_ids"]
    embeddings = cat_data["embeddings"]
    names = cat_data["names"]

    vector_scores = embeddings @ query_emb

    results: list[tuple[str, float]] = []
    for i, pid in enumerate(product_ids):
        vs = float(vector_scores[i])
        exact_match = 1.0 if query_lower in names[i] else 0.0
        name_tokens = set(names[i].split())
        overlap = len(query_tokens & name_tokens) / len(query_tokens) if query_tokens else 0.0

        score = 0.70 * vs + 0.20 * exact_match + 0.10 * overlap
        results.append((pid, score))

    return results
