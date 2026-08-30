from dataclasses import dataclass
from typing import Optional


@dataclass
class GameMilestoneAchievement:
    game_id: int
    player_id: int
    competition_type: str
    rule_key: str
    title: str
    achieved_value: Optional[float] = None
    inning: Optional[int] = None
    half: Optional[str] = None
    opponent_player_id: Optional[int] = None
    context_text: Optional[str] = None


class GameMilestoneRule:
    rule_key: str
    title: str

    def evaluate(self, record, play_events=None) -> list[GameMilestoneAchievement]:
        raise NotImplementedError


class HitsThresholdRule(GameMilestoneRule):
    def __init__(self, threshold: int = 5):
        self.threshold = threshold
        self.rule_key = f"GAME_HITS_{threshold}"
        self.title = f"{threshold}+ Hits in a Game"

    def evaluate(self, record, play_events=None) -> list[GameMilestoneAchievement]:
        achievements = []
        for line in record.batting_lines:
            if line.h >= self.threshold:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=line.player_id,
                        competition_type=record.competition_type,
                        rule_key=self.rule_key,
                        title=f"{line.h} Hits Game",
                        achieved_value=float(line.h),
                    )
                )
        return achievements


class MultiHRRule(GameMilestoneRule):
    def __init__(self, threshold: int = 2):
        self.threshold = threshold
        self.rule_key = "GAME_MULTI_HR"
        self.title = f"{threshold}+ Home Runs in a Game"

    def evaluate(self, record, play_events=None) -> list[GameMilestoneAchievement]:
        achievements = []
        for line in record.batting_lines:
            if line.hr >= self.threshold:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=line.player_id,
                        competition_type=record.competition_type,
                        rule_key=self.rule_key,
                        title=f"Multi-HR Game ({line.hr} HRs)",
                        achieved_value=float(line.hr),
                    )
                )
        return achievements


class StrikeoutsThresholdRule(GameMilestoneRule):
    def __init__(self, threshold: int = 10):
        self.threshold = threshold
        self.rule_key = f"GAME_STRIKEOUTS_{threshold}"
        self.title = f"{threshold}+ Strikeouts in a Game"

    def evaluate(self, record, play_events=None) -> list[GameMilestoneAchievement]:
        achievements = []
        for line in record.pitching_lines:
            if line.so >= self.threshold:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=line.player_id,
                        competition_type=record.competition_type,
                        rule_key=self.rule_key,
                        title=f"{line.so} Strikeouts Game",
                        achieved_value=float(line.so),
                    )
                )
        return achievements


class GrandSlamRule(GameMilestoneRule):
    def __init__(self):
        self.rule_key = "GAME_GRAND_SLAM"
        self.title = "Grand Slam"

    def evaluate(self, record, play_events=None) -> list[GameMilestoneAchievement]:
        achievements = []
        # Check lower batting events first for "3 on"
        for ev in record.batting_events:
            if ev.event_type == "HOME_RUN" and ev.context_text and "3 on" in ev.context_text:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=ev.player_id,
                        competition_type=record.competition_type,
                        rule_key=self.rule_key,
                        title="Grand Slam",
                        context_text=ev.context_text,
                    )
                )
        return achievements


class CycleRule(GameMilestoneRule):
    def __init__(self):
        self.rule_key = "GAME_CYCLE"
        self.title = "Hit for the Cycle"

    def evaluate(self, record, play_events=None) -> list[GameMilestoneAchievement]:
        achievements = []
        for line in record.batting_lines:
            singles = line.h - line.doubles - line.triples - line.hr
            if singles >= 1 and line.doubles >= 1 and line.triples >= 1 and line.hr >= 1:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=line.player_id,
                        competition_type=record.competition_type,
                        rule_key=self.rule_key,
                        title="Hit for the Cycle",
                        achieved_value=float(line.h),
                    )
                )
        return achievements


class ShutoutRule(GameMilestoneRule):
    def __init__(self):
        self.rule_key = "GAME_SHUTOUT"
        self.title = "Complete Game Shutout"

    def evaluate(self, record, play_events=None) -> list[GameMilestoneAchievement]:
        achievements = []
        for line in record.pitching_lines:
            if line.outs >= 27 and line.r == 0:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=line.player_id,
                        competition_type=record.competition_type,
                        rule_key=self.rule_key,
                        title="Shutout (CG)",
                        achieved_value=float(line.outs / 3.0),
                    )
                )
        return achievements


class NoHitterRule(GameMilestoneRule):
    def __init__(self):
        self.rule_key = "GAME_NO_HITTER"
        self.title = "No-Hitter"

    def evaluate(self, record, play_events=None) -> list[GameMilestoneAchievement]:
        achievements = []
        for line in record.pitching_lines:
            if line.outs >= 27 and line.h == 0 and line.r == 0:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=line.player_id,
                        competition_type=record.competition_type,
                        rule_key=self.rule_key,
                        title="No-Hitter",
                        achieved_value=float(line.outs / 3.0),
                    )
                )
        return achievements


class PerfectGameRule(GameMilestoneRule):
    def __init__(self):
        self.rule_key = "GAME_PERFECT_GAME"
        self.title = "Perfect Game"

    def evaluate(self, record, play_events=None) -> list[GameMilestoneAchievement]:
        achievements = []
        for line in record.pitching_lines:
            if line.outs >= 27 and line.h == 0 and line.r == 0 and line.bb == 0:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=line.player_id,
                        competition_type=record.competition_type,
                        rule_key=self.rule_key,
                        title="Perfect Game",
                        achieved_value=float(line.outs / 3.0),
                    )
                )
        return achievements
