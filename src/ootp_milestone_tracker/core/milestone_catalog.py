MILESTONE_LADDERS = {
    # Player career batting / playing-time milestones.
    ("player", "career", "H"): {
        "title": "Career Hits",
        "unit": "H",
        "thresholds": (2000, 2500, 3000, 3500),
    },
    ("player", "career", "HR"): {
        "title": "Career Home Runs",
        "unit": "HR",
        "thresholds": (300, 400, 500, 600, 700),
    },
    ("player", "career", "RBI"): {
        "title": "Career RBI",
        "unit": "RBI",
        "thresholds": (1000, 1250, 1500, 1750, 2000),
    },
    ("player", "career", "G"): {
        "title": "Career Games",
        "unit": "G",
        "thresholds": (1000, 1500, 2000, 2500, 3000),
    },

    # Player career pitching milestones.
    ("player", "career", "W"): {
        "title": "Career Wins",
        "unit": "W",
        "thresholds": (100, 150, 200, 250, 300),
    },
    ("player", "career", "SO"): {
        "title": "Career Strikeouts",
        "unit": "SO",
        "thresholds": (1000, 1500, 2000, 2500, 3000),
    },

    # Player single-season milestones represented by the current sample DB.
    ("player", "season", "H"): {
        "title": "Season Hits",
        "unit": "H",
        "thresholds": (150, 175, 200, 225, 250),
    },
    ("player", "season", "HR"): {
        "title": "Season Home Runs",
        "unit": "HR",
        "thresholds": (30, 40, 50, 60, 70),
    },
    ("player", "season", "W"): {
        "title": "Season Wins",
        "unit": "W",
        "thresholds": (10, 15, 20, 25, 30),
    },

    # Repeated award-count milestones represented by the current sample DB.
    ("player", "award", "ALLSTAR"): {
        "title": "All-Star Selections",
        "unit": "",
        "thresholds": (5, 10, 15, 20, 25),
    },

    # Prepared for a future team-detail view. Entity type is part of the key so
    # team wins do not collide with a pitcher's career-win ladder.
    ("team", "career", "W"): {
        "title": "Team Career Wins",
        "unit": "W",
        "thresholds": (1000, 2000, 3000, 4000, 5000),
    },
}


def milestone_ladder(*args):
    """Return display metadata for a configured multi-threshold milestone series.

    Two arguments keep the current Player Records caller compact and imply a
    player entity. Three arguments allow future team/player detail views to use
    the same catalog without stat-key collisions.
    """
    if len(args) == 2:
        entity_type = "player"
        scope, stat_key = args
    elif len(args) == 3:
        entity_type, scope, stat_key = args
    else:
        raise TypeError("milestone_ladder expects (scope, stat_key) or (entity_type, scope, stat_key)")
    return MILESTONE_LADDERS.get((entity_type, scope, stat_key))
