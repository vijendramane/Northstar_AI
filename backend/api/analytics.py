
from fastapi import APIRouter
from agent.memory import get_profile

router = APIRouter()


@router.get("/analytics/{session_id}")
def analytics(session_id: str):

    profile = get_profile(session_id)

    return {
        "lead": profile
    }