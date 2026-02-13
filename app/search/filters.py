from typing import Any


def apply_filters(
    results: list[tuple[str, float]],
    cat_data: dict[str, Any],
    filters: dict[str, Any],
) -> list[tuple[str, float]]:
    filtered: list[tuple[str, float]] = []

    for pid, score in results:
        keep = True

        if "holeSpacingCompatibility" in filters and filters["holeSpacingCompatibility"]:
            f = cat_data["filters"].get(pid, {})
            value = filters["holeSpacingCompatibility"]
            if value == "Single Hole" and not f.get("single_hole"):
                keep = False
            elif value == "Widespread" and not f.get("widespread"):
                keep = False
            elif value == "Centerset" and not f.get("centerset"):
                keep = False

        if "locations" in filters and filters["locations"]:
            f = cat_data["filters"].get(pid, {})
            for loc in filters["locations"]:
                if not f.get(loc):
                    keep = False
                    break

        if "hasTubSpout" in filters and filters["hasTubSpout"] is not None:
            f = cat_data["filters"].get(pid, {})
            if f.get("has_tub_spout") != filters["hasTubSpout"]:
                keep = False

        if "lengthMax" in filters and filters["lengthMax"] is not None:
            d = cat_data["dimensions"].get(pid, {})
            length = d.get("length")
            if length and length > filters["lengthMax"]:
                keep = False

        if "widthMax" in filters and filters["widthMax"] is not None:
            d = cat_data["dimensions"].get(pid, {})
            width = d.get("width")
            if width and width > filters["widthMax"]:
                keep = False

        if keep:
            filtered.append((pid, score))

    return filtered
