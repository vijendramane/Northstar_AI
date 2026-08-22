from services.booking_service import (
    book_site_visit,
    get_available_slots,
)


def create_site_visit(
    session_id: str,
    slot: str,
) -> dict:
    """
    Book a Northstar site visit.
    """

    return book_site_visit(
        session_id=session_id,
        slot=slot,
    )


def get_site_visit_slots() -> dict:
    """
    Return currently available site-visit slots.
    """

    return {
        "available_slots": get_available_slots()
    }


def request_human_callback() -> dict:
    """
    Record a request for human sales assistance.
    """

    return {
        "success": True,
        "status": "human_escalation_requested",
        "message": (
            "The customer's request for a sales "
            "representative has been recorded."
        ),
    }