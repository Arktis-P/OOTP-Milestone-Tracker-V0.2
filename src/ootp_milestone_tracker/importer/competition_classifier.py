from typing import Optional


def classify_competition(title: str, league_id: Optional[int] = None) -> str:
    """Classify game competition into canonical types:
    - regular_season
    - postseason
    - spring_training
    - international
    """
    title_lower = title.lower()
    if "spring training" in title_lower or "st box score" in title_lower:
        return "spring_training"
    if "wbc" in title_lower or "international" in title_lower:
        return "international"
    if "playoff" in title_lower or "postseason" in title_lower or "world series" in title_lower or "koreanseries" in title_lower:
        return "postseason"
    return "regular_season"
