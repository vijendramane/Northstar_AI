from typing import Any


# ---------------------------------------------------------
# In-memory session storage
# ---------------------------------------------------------

sessions: dict[str, dict[str, Any]] = {}


# ---------------------------------------------------------
# Create / retrieve session
# ---------------------------------------------------------

def get_session(session_id: str) -> dict[str, Any]:

    if session_id not in sessions:

        sessions[session_id] = {
            "messages": [],
            "profile": {
                "name": None,
                "configuration": None,
                "budget": None,
                "purpose": None,
                "timeline": None,
                "location_preference": None,
                "preferred_language": None,
                "interest_level": None,
                "intent": None,
                "objections": [],
                "site_visit_status": "not_requested",
                "follow_up_required": False,
                "human_escalation": False,
                "do_not_contact": False,
            },
        }

    return sessions[session_id]


# ---------------------------------------------------------
# Add conversation message
# ---------------------------------------------------------

def add_message(
    session_id: str,
    role: str,
    content: str,
) -> None:

    session = get_session(session_id)

    session["messages"].append(
        {
            "role": role,
            "content": content,
        }
    )


# ---------------------------------------------------------
# Get conversation history
# ---------------------------------------------------------

def get_messages(session_id: str) -> list[dict]:

    session = get_session(session_id)

    return session["messages"]


# ---------------------------------------------------------
# Get customer profile
# ---------------------------------------------------------

def get_profile(session_id: str) -> dict:

    session = get_session(session_id)

    return session["profile"]


# ---------------------------------------------------------
# Update customer profile
# ---------------------------------------------------------

def update_profile(
    session_id: str,
    updates: dict,
) -> None:

    session = get_session(session_id)

    session["profile"].update(updates)


# ---------------------------------------------------------
# Reset conversation
# ---------------------------------------------------------

def reset_session(session_id: str) -> None:

    sessions.pop(session_id, None)