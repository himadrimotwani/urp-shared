"""
Append-only storage helpers for participant and round data collection.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
from threading import Lock
from typing import Any
from uuid import uuid4


STORAGE_DIR = Path("storage")
PARTICIPANTS_PATH = STORAGE_DIR / "participants.jsonl"
ROUNDS_PATH = STORAGE_DIR / "rounds.jsonl"

_write_lock = Lock()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _json_default(value: Any) -> Any:
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump()
    return str(value)


def _append_jsonl(path: Path, record: dict[str, Any]) -> None:
    STORAGE_DIR.mkdir(parents=True, exist_ok=True)
    with _write_lock:
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, default=_json_default, sort_keys=True) + "\n")


def create_participant_record(
    *,
    name: str,
    email: str | None = None,
    student_id: str | None = None,
    section: str | None = None,
) -> dict[str, Any]:
    participant_id = str(uuid4())
    record = {
        "participant_id": participant_id,
        "name": name.strip(),
        "email": email.strip() if email else None,
        "student_id": student_id.strip() if student_id else None,
        "section": section.strip() if section else None,
        "created_at": _now_iso(),
    }
    _append_jsonl(PARTICIPANTS_PATH, record)
    return record


def log_round_record(
    *,
    participant_id: str | None,
    session_id: str,
    round_summary: Any,
    round_output: Any,
) -> None:
    record = {
        "logged_at": _now_iso(),
        "participant_id": participant_id,
        "session_id": session_id,
        "round": round_summary,
        "round_output": round_output,
    }
    _append_jsonl(ROUNDS_PATH, record)
