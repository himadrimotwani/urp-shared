"""
Instructor-facing data access routes for collected participant and round records.
"""

from fastapi import APIRouter, Response

from app.services.storage_service import (
    get_records_summary,
    participants_csv,
    rounds_csv,
)


router = APIRouter()


@router.get("/records/summary")
def records_summary(limit: int = 25) -> dict:
    return get_records_summary(limit=max(1, min(limit, 200)))


@router.get("/records/participants.csv")
def download_participants_csv() -> Response:
    return Response(
        content=participants_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=participants.csv"},
    )


@router.get("/records/rounds.csv")
def download_rounds_csv() -> Response:
    return Response(
        content=rounds_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=rounds.csv"},
    )
