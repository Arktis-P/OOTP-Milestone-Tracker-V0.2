from typing import Dict, List, Optional


DEFAULT_CAREER_MILESTONE_SETTINGS = {
    "CAREER_G_BATTER": {"enabled": True, "thresholds": [1000, 1500, 2000, 2500, 3000]},
    "CAREER_HITS": {"enabled": True, "start": 1500, "step": 500},
    "CAREER_HR": {"enabled": True, "start": 200, "step": 100},
    "CAREER_RUNS": {"enabled": True, "start": 750, "step": 250},
    "CAREER_RBI": {"enabled": True, "start": 750, "step": 250},
    "CAREER_SB": {"enabled": True, "start": 200, "step": 100},
    "CAREER_BB": {"enabled": True, "start": 1000, "step": 500},
    "CAREER_G_PITCHER": {"enabled": True, "thresholds": [200, 300, 400, 500, 600, 700]},
    "CAREER_GS_PITCHER": {"enabled": True, "thresholds": [200, 250, 300, 350, 400, 450, 500]},
    "CAREER_IP": {"enabled": True, "start": 1500, "step": 500},
    "CAREER_STRIKEOUTS": {"enabled": True, "start": 1500, "step": 500},
    "CAREER_WINS": {"enabled": True, "start": 100, "step": 50},
    "CAREER_HOLDS": {"enabled": True, "start": 100, "step": 25},
    "CAREER_SAVES": {"enabled": True, "start": 200, "step": 50},
}


def get_ladder_thresholds(cfg: Dict, current_val: float) -> List[float]:
    """Generate threshold values for a milestone rule (explicit array or open-ended start/step)."""
    if not cfg.get("enabled", True):
        return []

    if "thresholds" in cfg:
        return [float(t) for t in cfg["thresholds"]]

    start = cfg.get("start", 100)
    step = cfg.get("step", 50)
    if step <= 0:
        return [float(start)]

    thresholds = []
    t = float(start)
    max_target = max(current_val, start) + step * 2
    while t <= max_target:
        thresholds.append(t)
        t += step

    return thresholds
