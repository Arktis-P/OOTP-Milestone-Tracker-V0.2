from typing import Dict, List, Optional

from .game_rules import (
    BatterHitsFamilyRule,
    BatterHRFamilyRule,
    BatterRBIFamilyRule,
    BatterSBFamilyRule,
    CycleRule,
    GameMilestoneAchievement,
    GameMilestoneRule,
    GrandSlamRule,
    PitcherHierarchyRule,
    PitcherSOFamilyRule,
    TeamBattingRules,
    TeamPitchingHierarchyRule,
)

DEFAULT_GAME_MILESTONE_SETTINGS = {
    "GAME_HITS": {"enabled": True, "thresholds": [4, 5, 6, 7]},
    "GAME_RBI": {"enabled": True, "thresholds": [5, 6, 7, 8, 9, 10]},
    "GAME_HR": {"enabled": True, "thresholds": [2, 3, 4, 5]},
    "GAME_SB": {"enabled": True, "thresholds": [3, 4, 5, 6, 7]},
    "GAME_STRIKEOUTS": {"enabled": True, "thresholds": [10, 15, 20, 25, 30]},
}


class GameMilestoneEvaluator:
    def __init__(self, rules: List[GameMilestoneRule] = None, settings: Optional[Dict] = None):
        if rules is None:
            settings = settings or DEFAULT_GAME_MILESTONE_SETTINGS
            hits_cfg = settings.get("GAME_HITS", DEFAULT_GAME_MILESTONE_SETTINGS["GAME_HITS"])
            rbi_cfg = settings.get("GAME_RBI", DEFAULT_GAME_MILESTONE_SETTINGS["GAME_RBI"])
            hr_cfg = settings.get("GAME_HR", DEFAULT_GAME_MILESTONE_SETTINGS["GAME_HR"])
            sb_cfg = settings.get("GAME_SB", DEFAULT_GAME_MILESTONE_SETTINGS["GAME_SB"])
            so_cfg = settings.get("GAME_STRIKEOUTS", DEFAULT_GAME_MILESTONE_SETTINGS["GAME_STRIKEOUTS"])

            self.rules = [
                BatterHitsFamilyRule(thresholds=hits_cfg.get("thresholds"), enabled=hits_cfg.get("enabled", True)),
                BatterRBIFamilyRule(thresholds=rbi_cfg.get("thresholds"), enabled=rbi_cfg.get("enabled", True)),
                BatterHRFamilyRule(thresholds=hr_cfg.get("thresholds"), enabled=hr_cfg.get("enabled", True)),
                BatterSBFamilyRule(thresholds=sb_cfg.get("thresholds"), enabled=sb_cfg.get("enabled", True)),
                GrandSlamRule(),
                CycleRule(),
                PitcherSOFamilyRule(thresholds=so_cfg.get("thresholds"), enabled=so_cfg.get("enabled", True)),
                PitcherHierarchyRule(),
                TeamBattingRules(),
                TeamPitchingHierarchyRule(),
            ]
        else:
            self.rules = rules

    def evaluate_game(self, record, play_events=None) -> List[GameMilestoneAchievement]:
        achievements: List[GameMilestoneAchievement] = []
        for rule in self.rules:
            res = rule.evaluate(record, play_events)
            if res:
                achievements.extend(res)
        return achievements
