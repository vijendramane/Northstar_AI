from services.booking_service import book_site_visit


print(
    book_site_visit(
        "demo-123456",
        "Saturday 11:00 AM",
    )
)


print(
    book_site_visit(
        "demo-123456",
        "Saturday 2:00 PM",
    )
)