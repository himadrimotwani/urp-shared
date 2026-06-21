"""
Demand history scenario helpers.
"""

from pathlib import Path
import re
from typing import Any

from simulation.core import load_demand_history_from_csv

DEFAULT_HISTORY_ID = "default"
DEFAULT_HISTORY_PATH = Path("data/D_hist.csv")
DEMAND_HISTORIES_DIR = Path("data/demand_histories")


def _label_from_history_id(history_id: str) -> str:
    if history_id == DEFAULT_HISTORY_ID:
        return "Default Demand History"
    match = re.fullmatch(r"n_(\d+)_(\d+)(?:_(.+))?", history_id)
    if match:
        label = f"N({match.group(1)},{match.group(2)})"
        suffix = match.group(3)
        if suffix:
            label += "-" + suffix.replace("_", "-")
        return label
    return history_id.replace("_", " ").title()


def _summary(values: list[int]) -> dict[str, Any]:
    return {
        "count": len(values),
        "min": min(values) if values else None,
        "max": max(values) if values else None,
        "sample": values[:10],
    }


def list_demand_histories() -> list[dict[str, Any]]:
    histories: list[dict[str, Any]] = []

    default_values = load_demand_history_from_csv(DEFAULT_HISTORY_PATH)
    histories.append({
        "id": DEFAULT_HISTORY_ID,
        "label": _label_from_history_id(DEFAULT_HISTORY_ID),
        **_summary(default_values),
    })

    if DEMAND_HISTORIES_DIR.exists():
        for path in sorted(DEMAND_HISTORIES_DIR.glob("*.csv")):
            history_id = path.stem
            values = load_demand_history_from_csv(path)
            histories.append({
                "id": history_id,
                "label": _label_from_history_id(history_id),
                **_summary(values),
            })

    return histories


def load_demand_history_by_id(history_id: str | None) -> list[int]:
    if not history_id or history_id == DEFAULT_HISTORY_ID:
        return load_demand_history_from_csv(DEFAULT_HISTORY_PATH)

    safe_id = Path(history_id).name
    path = DEMAND_HISTORIES_DIR / f"{safe_id}.csv"
    if not path.exists():
        raise ValueError(f"Unknown demand history: {history_id}")

    return load_demand_history_from_csv(path)
