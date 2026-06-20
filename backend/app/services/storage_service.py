"""
Append-only storage helpers for participant and round data collection.
"""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
import csv
from io import StringIO
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


def _read_jsonl(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        return []

    with _write_lock:
        lines = path.read_text(encoding="utf-8").splitlines()

    records = []
    for line in lines:
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return records


def get_participant_record(participant_id: str | None) -> dict[str, Any] | None:
    if not participant_id or not PARTICIPANTS_PATH.exists():
        return None

    with _write_lock:
        lines = PARTICIPANTS_PATH.read_text(encoding="utf-8").splitlines()

    for line in reversed(lines):
        if not line.strip():
            continue
        try:
            record = json.loads(line)
        except json.JSONDecodeError:
            continue
        if record.get("participant_id") == participant_id:
            return record
    return None


def list_participant_records() -> list[dict[str, Any]]:
    return _read_jsonl(PARTICIPANTS_PATH)


def list_round_records() -> list[dict[str, Any]]:
    return _read_jsonl(ROUNDS_PATH)


def get_records_summary(limit: int = 25) -> dict[str, Any]:
    participants = list_participant_records()
    rounds = list_round_records()
    return {
        "participant_count": len(participants),
        "round_count": len(rounds),
        "participants": participants[-limit:],
        "rounds": rounds[-limit:],
    }


def _csv_response(rows: list[dict[str, Any]], fields: list[str]) -> str:
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    return output.getvalue()


def participants_csv() -> str:
    return _csv_response(
        list_participant_records(),
        ["participant_id", "name", "email", "student_id", "section", "created_at"],
    )


def rounds_csv() -> str:
    rows = []
    for record in list_round_records():
        participant = record.get("participant") or {}
        round_data = record.get("round") or {}
        round_output = record.get("round_output") or {}
        rows.append({
            "logged_at": record.get("logged_at"),
            "participant_id": record.get("participant_id"),
            "name": participant.get("name"),
            "email": participant.get("email"),
            "student_id": participant.get("student_id"),
            "section": participant.get("section"),
            "session_id": record.get("session_id"),
            "round_index": round_data.get("round_index"),
            "order_quantity": round_data.get("order_quantity"),
            "realized_demand": round_data.get("realized_demand"),
            "sales": round_output.get("sales"),
            "returns": round_output.get("returns"),
            "leftovers": round_output.get("leftovers"),
            "buyer_revenue": round_data.get("buyer_revenue"),
            "buyer_cost": round_data.get("buyer_cost"),
            "buyer_profit": round_data.get("buyer_profit"),
            "supplier_revenue": round_data.get("supplier_revenue"),
            "supplier_cost": round_data.get("supplier_cost"),
            "supplier_profit": round_data.get("supplier_profit"),
            "wholesale_price": round_data.get("wholesale_price"),
            "buyback_price": round_data.get("buyback_price"),
            "contract_length": round_data.get("contract_length"),
            "remaining_rounds": round_data.get("remaining_rounds"),
            "contract_type": round_data.get("contract_type"),
        })
    return _csv_response(
        rows,
        [
            "logged_at", "participant_id", "name", "email", "student_id", "section",
            "session_id", "round_index", "order_quantity", "realized_demand", "sales",
            "returns", "leftovers", "buyer_revenue", "buyer_cost", "buyer_profit",
            "supplier_revenue", "supplier_cost", "supplier_profit", "wholesale_price",
            "buyback_price", "contract_length", "remaining_rounds", "contract_type",
        ],
    )


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
    participant = get_participant_record(participant_id)
    record = {
        "logged_at": _now_iso(),
        "participant_id": participant_id,
        "participant": participant,
        "session_id": session_id,
        "round": round_summary,
        "round_output": round_output,
    }
    _append_jsonl(ROUNDS_PATH, record)
