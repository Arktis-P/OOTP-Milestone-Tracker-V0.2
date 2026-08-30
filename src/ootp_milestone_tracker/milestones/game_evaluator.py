from typing import List

from .game_rules import (
    CycleRule,
    GameMilestoneAchievement,
    GameMilestoneRule,
    GrandSlamRule,
    HitsThresholdRule,
    MultiHRRule,
    NoHitterRule,
    PerfectGameRule,
    ShutoutRule,
    StrikeoutsThresholdRule,
)


class GameMilestoneEvaluator:
    def __init__(self, rules: List[GameMilestoneRule] = None):
        if rules is None:
            self.rules = [
                HitsThresholdRule(5),
                MultiHRRule(2),
                StrikeoutsThresholdRule(10),
                GrandSlamRule(),
                CycleRule(),
                ShutoutRule(),
                NoHitterRule(),
                PerfectGameRule(),
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
