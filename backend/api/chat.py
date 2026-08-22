from fastapi import APIRouter
from pydantic import BaseModel

from agent.agent import (
    generate_agent_response,
    extract_profile_update,
)

from agent.memory import (
    add_message,
    get_messages,
    get_profile,
    update_profile,
)


router = APIRouter()


# =========================================================
# REQUEST MODEL
# =========================================================

class ChatRequest(BaseModel):
    session_id: str
    message: str


# =========================================================
# RESPONSE MODEL
# =========================================================

class ChatResponse(BaseModel):
    session_id: str
    message: str
    profile: dict


# =========================================================
# CHAT ENDPOINT
# =========================================================

@router.post(
    "/chat",
    response_model=ChatResponse,
)
def chat(request: ChatRequest):

    # -----------------------------------------------------
    # 1. Get existing conversation
    # -----------------------------------------------------

    history = get_messages(
        request.session_id
    )

    # -----------------------------------------------------
    # 2. Get existing customer profile
    # -----------------------------------------------------

    profile = get_profile(
        request.session_id
    )

    # -----------------------------------------------------
    # 3. Extract new customer information + intent
    # -----------------------------------------------------

    profile_update = extract_profile_update(
        message=request.message,
        existing_profile=profile,
    )

    # -----------------------------------------------------
    # 4. Save extracted profile information
    # -----------------------------------------------------

    if profile_update:

        update_profile(
            session_id=request.session_id,
            updates=profile_update,
        )

    # -----------------------------------------------------
    # 5. Handle customer intent
    # -----------------------------------------------------

    intent = profile_update.get(
        "intent"
    )

    if intent == "human_escalation":

        update_profile(
            session_id=request.session_id,
            updates={
                "human_escalation": True,
            },
        )

    elif intent == "do_not_contact":

        update_profile(
            session_id=request.session_id,
            updates={
                "do_not_contact": True,
                "follow_up_required": False,
            },
        )

    elif intent == "callback":

        update_profile(
            session_id=request.session_id,
            updates={
                "follow_up_required": True,
            },
        )

    # -----------------------------------------------------
    # 6. Generate AI response
    #
    # Gemini may also call tools here:
    #
    # - create_site_visit
    # - get_site_visit_slots
    # - request_human_callback
    # -----------------------------------------------------

    response, tool_results = generate_agent_response(
        message=request.message,
        conversation_history=history,
        session_id=request.session_id,
    )

    # -----------------------------------------------------
    # 7. Process tool results
    # -----------------------------------------------------

    for tool_result in tool_results:

        tool_name = tool_result.get(
            "tool"
        )

        result = tool_result.get(
            "result",
            {},
        )

        # -------------------------------------------------
        # Site visit booking
        # -------------------------------------------------

        if tool_name == "create_site_visit":

            if result.get("success"):

                update_profile(
                    session_id=request.session_id,
                    updates={
                        "site_visit_status": "confirmed",
                        "follow_up_required": False,
                    },
                )

            else:

                update_profile(
                    session_id=request.session_id,
                    updates={
                        "site_visit_status": "failed",
                    },
                )

        # -------------------------------------------------
        # Human escalation
        # -------------------------------------------------

        elif tool_name == "request_human_callback":

            if result.get("success"):

                update_profile(
                    session_id=request.session_id,
                    updates={
                        "human_escalation": True,
                    },
                )

    # -----------------------------------------------------
    # 8. Save customer message
    # -----------------------------------------------------

    add_message(
        session_id=request.session_id,
        role="customer",
        content=request.message,
    )

    # -----------------------------------------------------
    # 9. Save AI response
    # -----------------------------------------------------

    add_message(
        session_id=request.session_id,
        role="assistant",
        content=response,
    )

    # -----------------------------------------------------
    # 10. Get final updated profile
    # -----------------------------------------------------

    profile = get_profile(
        request.session_id
    )

    # -----------------------------------------------------
    # 11. Return response
    # -----------------------------------------------------

    return ChatResponse(
        session_id=request.session_id,
        message=response,
        profile=profile,
    )