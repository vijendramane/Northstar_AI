AVAILABLE_SLOTS = [
    "Saturday 10:00 AM",
    "Saturday 11:00 AM",
    "Saturday 3:00 PM",
    "Sunday 11:00 AM",
]


def get_available_slots():
    return AVAILABLE_SLOTS.copy()


def book_site_visit(
    session_id: str,
    slot: str,
):
    slot = slot.strip()

    if slot not in AVAILABLE_SLOTS:
        return {
            "success": False,
            "reason": "slot_unavailable",
            "message": "The requested slot is not available.",
            "available_slots": get_available_slots(),
        }

    booking_id = f"NS-{session_id[-6:].upper()}"

    return {
        "success": True,
        "booking_id": booking_id,
        "slot": slot,
        "message": "Site visit confirmed.",
    }