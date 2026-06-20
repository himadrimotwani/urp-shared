"""
Participant routes for pre-game login/data collection.
"""

from fastapi import APIRouter, HTTPException

from app.schemas import ParticipantCreateRequest, ParticipantCreateResponse
from app.services.storage_service import create_participant_record


router = APIRouter()


@router.post("/participants", response_model=ParticipantCreateResponse)
def create_participant(request: ParticipantCreateRequest) -> ParticipantCreateResponse:
    name = request.name.strip()
    if not name:
        raise HTTPException(status_code=400, detail="Name is required.")

    record = create_participant_record(
        name=name,
        email=request.email,
        student_id=request.student_id,
        section=request.section,
    )
    return ParticipantCreateResponse(participant_id=record["participant_id"])
