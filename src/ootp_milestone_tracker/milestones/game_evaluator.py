from typing import List

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


class GameMilestoneEvaluator:
    def __init__(self, rules: List[GameMilestoneRule] = None):
        if rules is None:
            self.rules = [
                # Batter Threshold Families
                BatterHitsFamilyRule(),
                BatterRBIFamilyRule(),
                BatterHRFamilyRule(),
                BatterSBFamilyRule(),
                # Batter Named Rules
                GrandSlamRule(),
                CycleRule(),
                # Pitcher Threshold Families
                PitcherSOFamilyRule(),
                # Pitcher Hierarchy Rule (Highest Only)
                PitcherHierarchyRule(),
                # Team Rules
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
