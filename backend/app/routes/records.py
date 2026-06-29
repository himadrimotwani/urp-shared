"""
Instructor-facing data access routes for collected participant and round records.
"""

import os
from fastapi import APIRouter, Header, HTTPException, Query, Response
from dotenv import load_dotenv

from app.services.storage_service import (
    chat_logs_csv,
    get_records_summary,
    participants_csv,
    rounds_csv,
)


router = APIRouter()
load_dotenv(override=True)


def verify_instructor_code(code: str | None) -> None:
    expected = os.getenv("INSTRUCTOR_ACCESS_CODE")
    if not expected:
        raise HTTPException(status_code=503, detail="Instructor access code is not configured.")
    if code != expected:
        raise HTTPException(status_code=403, detail="Invalid instructor access code.")


@router.get("/records/summary")
def records_summary(
    limit: int = 25,
    x_instructor_code: str | None = Header(default=None),
) -> dict:
    verify_instructor_code(x_instructor_code)
    return get_records_summary(limit=max(1, min(limit, 200)))


@router.get("/records/participants.csv")
def download_participants_csv(code: str | None = Query(default=None)) -> Response:
    verify_instructor_code(code)
    return Response(
        content=participants_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=participants.csv"},
    )


@router.get("/records/rounds.csv")
def download_rounds_csv(code: str | None = Query(default=None)) -> Response:
    verify_instructor_code(code)
    return Response(
        content=rounds_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=rounds.csv"},
    )


@router.get("/records/chat-logs.csv")
def download_chat_logs_csv(code: str | None = Query(default=None)) -> Response:
    verify_instructor_code(code)
    return Response(
        content=chat_logs_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=chat_logs.csv"},
    )
