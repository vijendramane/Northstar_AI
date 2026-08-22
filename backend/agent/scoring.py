def calculate_lead_score(profile: dict) -> int:
    """
    Simple transparent qualification score.

    This is a qualification/readiness score,
    not a probability of conversion.
    """

    score = 0

    if profile.get("name"):
        score += 10

    if profile.get("configuration"):
        score += 20

    if profile.get("budget"):
        score += 20

    if profile.get("purpose"):
        score += 15

    if profile.get("timeline"):
        score += 20

    if profile.get("site_visit_status") == "confirmed":
        score += 15

    return min(score, 100)


def get_lead_temperature(score: int) -> str:

    if score >= 80:
        return "HOT"

    if score >= 50:
        return "WARM"

    return "COLD"