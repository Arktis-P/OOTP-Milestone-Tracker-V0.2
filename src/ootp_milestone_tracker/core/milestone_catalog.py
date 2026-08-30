MILESTONE_LADDERS = {
    ("career", "H"): {
        "title": "Career Hits",
        "unit": "H",
        "thresholds": (2000, 2500, 3000, 3500),
    },
}


def milestone_ladder(scope: str, stat_key: str):
    """Return display metadata for a multi-threshold milestone series, if configured."""
    return MILESTONE_LADDERS.get((scope, stat_key))
