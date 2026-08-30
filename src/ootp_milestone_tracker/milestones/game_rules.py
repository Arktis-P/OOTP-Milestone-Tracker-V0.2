from dataclasses import dataclass
from typing import List, Optional


@dataclass
class GameMilestoneAchievement:
    game_id: int
    player_id: Optional[int]
    competition_type: str
    rule_key: str
    title: str
    achieved_value: Optional[float] = None
    inning: Optional[int] = None
    half: Optional[str] = None
    opponent_player_id: Optional[int] = None
    context_text: Optional[str] = None


def highest_reached(val: int, thresholds: List[int]) -> Optional[int]:
    """Return the highest threshold reached for a given value."""
    reached = [t for t in sorted(thresholds) if val >= t]
    return reached[-1] if reached else None


class GameMilestoneRule:
    rule_key: str
    title: str

    def evaluate(self, record, play_events=None) -> List[GameMilestoneAchievement]:
        raise NotImplementedError


# --- Batter Threshold Family Rules ---


class BatterHitsFamilyRule(GameMilestoneRule):
    THRESHOLDS = [4, 5, 6, 7]

    def evaluate(self, record, play_events=None) -> List[GameMilestoneAchievement]:
        achievements = []
        for line in record.batting_lines:
            t = highest_reached(line.h, self.THRESHOLDS)
            if t is not None:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=line.player_id,
                        competition_type=record.competition_type,
                        rule_key=f"GAME_HITS_{t}",
                        title=f"경기 {t}안타",
                        achieved_value=float(line.h),
                    )
                )
        return achievements


class BatterRBIFamilyRule(GameMilestoneRule):
    THRESHOLDS = [5, 6, 7, 8, 9, 10]

    def evaluate(self, record, play_events=None) -> List[GameMilestoneAchievement]:
        achievements = []
        for line in record.batting_lines:
            t = highest_reached(line.rbi, self.THRESHOLDS)
            if t is not None:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=line.player_id,
                        competition_type=record.competition_type,
                        rule_key=f"GAME_RBI_{t}",
                        title=f"경기 {t}타점",
                        achieved_value=float(line.rbi),
                    )
                )
        return achievements


class BatterHRFamilyRule(GameMilestoneRule):
    THRESHOLDS = [2, 3, 4, 5]

    def evaluate(self, record, play_events=None) -> List[GameMilestoneAchievement]:
        achievements = []
        for line in record.batting_lines:
            t = highest_reached(line.hr, self.THRESHOLDS)
            if t is not None:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=line.player_id,
                        competition_type=record.competition_type,
                        rule_key=f"GAME_HR_{t}",
                        title=f"경기 {t}홈런",
                        achieved_value=float(line.hr),
                    )
                )
        return achievements


class BatterSBFamilyRule(GameMilestoneRule):
    THRESHOLDS = [3, 4, 5, 6, 7]

    def evaluate(self, record, play_events=None) -> List[GameMilestoneAchievement]:
        achievements = []
        for line in record.batting_lines:
            t = highest_reached(line.sb, self.THRESHOLDS)
            if t is not None:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=line.player_id,
                        competition_type=record.competition_type,
                        rule_key=f"GAME_SB_{t}",
                        title=f"경기 {t}도루",
                        achieved_value=float(line.sb),
                    )
                )
        return achievements


# --- Batter Named Rules ---


class GrandSlamRule(GameMilestoneRule):
    rule_key = "GAME_GRAND_SLAM"
    title = "만루홈런"

    def evaluate(self, record, play_events=None) -> List[GameMilestoneAchievement]:
        achievements = []
        for ev in record.batting_events:
            if ev.event_type == "HOME_RUN" and ev.context_text and "3 on" in ev.context_text:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=ev.player_id,
                        competition_type=record.competition_type,
                        rule_key=self.rule_key,
                        title=self.title,
                        context_text=ev.context_text,
                    )
                )
        return achievements


class CycleRule(GameMilestoneRule):
    rule_key = "GAME_CYCLE"
    title = "히트 포 더 사이클"

    def evaluate(self, record, play_events=None) -> List[GameMilestoneAchievement]:
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
                        title=self.title,
                        achieved_value=float(line.h),
                    )
                )
        return achievements


# --- Pitcher Threshold Family Rules ---


class PitcherSOFamilyRule(GameMilestoneRule):
    THRESHOLDS = [10, 15, 20, 25, 30]

    def evaluate(self, record, play_events=None) -> List[GameMilestoneAchievement]:
        achievements = []
        for line in record.pitching_lines:
            t = highest_reached(line.so, self.THRESHOLDS)
            if t is not None:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=line.player_id,
                        competition_type=record.competition_type,
                        rule_key=f"GAME_STRIKEOUTS_{t}",
                        title=f"경기 {t}탈삼진",
                        achieved_value=float(line.so),
                    )
                )
        return achievements


# --- Pitcher Special Hierarchy Rule (Highest Only) ---


class PitcherHierarchyRule(GameMilestoneRule):
    """Evaluates Pitcher Special Result Hierarchy (Highest Only):
    PERFECT_GAME > NO_HIT_NO_RUN > SHUTOUT_WIN > COMPLETE_GAME_WIN
    """

    def evaluate(self, record, play_events=None) -> List[GameMilestoneAchievement]:
        achievements = []
        for line in record.pitching_lines:
            # Complete Game Win requires outs >= 27 and win = True
            if line.outs >= 27 and line.win:
                if line.h == 0 and line.r == 0 and line.bb == 0:
                    achievements.append(
                        GameMilestoneAchievement(
                            game_id=record.game_id,
                            player_id=line.player_id,
                            competition_type=record.competition_type,
                            rule_key="GAME_PERFECT_GAME",
                            title="퍼펙트 게임",
                            achieved_value=float(line.outs / 3.0),
                        )
                    )
                elif line.h == 0 and line.r == 0:
                    achievements.append(
                        GameMilestoneAchievement(
                            game_id=record.game_id,
                            player_id=line.player_id,
                            competition_type=record.competition_type,
                            rule_key="GAME_NO_HIT_NO_RUN",
                            title="노히트 노런",
                            achieved_value=float(line.outs / 3.0),
                        )
                    )
                elif line.r == 0:
                    achievements.append(
                        GameMilestoneAchievement(
                            game_id=record.game_id,
                            player_id=line.player_id,
                            competition_type=record.competition_type,
                            rule_key="GAME_SHUTOUT_WIN",
                            title="완봉승",
                            achieved_value=float(line.outs / 3.0),
                        )
                    )
                else:
                    achievements.append(
                        GameMilestoneAchievement(
                            game_id=record.game_id,
                            player_id=line.player_id,
                            competition_type=record.competition_type,
                            rule_key="GAME_COMPLETE_GAME_WIN",
                            title="완투승",
                            achieved_value=float(line.outs / 3.0),
                        )
                    )
        return achievements


# --- Team Batting Rules ---


class TeamBattingRules(GameMilestoneRule):
    def evaluate(self, record, play_events=None) -> List[GameMilestoneAchievement]:
        achievements = []
        teams_batting = {}
        for line in record.batting_lines:
            if line.team_id is not None:
                teams_batting.setdefault(line.team_id, []).append(line)

        for team_id, lines in teams_batting.items():
            starters = [l for l in lines if l.is_starter]
            if starters:
                if all(l.h >= 1 for l in starters):
                    achievements.append(
                        GameMilestoneAchievement(
                            game_id=record.game_id,
                            player_id=None,
                            competition_type=record.competition_type,
                            rule_key="TEAM_STARTERS_ALL_HIT",
                            title="팀 선발 전원 안타",
                        )
                    )
                if all(l.rbi >= 1 for l in starters):
                    achievements.append(
                        GameMilestoneAchievement(
                            game_id=record.game_id,
                            player_id=None,
                            competition_type=record.competition_type,
                            rule_key="TEAM_STARTERS_ALL_RBI",
                            title="팀 선발 전원 타점",
                        )
                    )

            if lines:
                if all(l.h >= 1 for l in lines):
                    achievements.append(
                        GameMilestoneAchievement(
                            game_id=record.game_id,
                            player_id=None,
                            competition_type=record.competition_type,
                            rule_key="TEAM_APPEARED_ALL_HIT",
                            title="팀 출장 전원 안타",
                        )
                    )
                if all(l.rbi >= 1 for l in lines):
                    achievements.append(
                        GameMilestoneAchievement(
                            game_id=record.game_id,
                            player_id=None,
                            competition_type=record.competition_type,
                            rule_key="TEAM_APPEARED_ALL_RBI",
                            title="팀 출장 전원 타점",
                        )
                    )
        return achievements


# --- Team Pitching Hierarchy Rule (Highest Only) ---


class TeamPitchingHierarchyRule(GameMilestoneRule):
    """Evaluates Team Pitching Result Hierarchy (Highest Only):
    TEAM_PERFECT_GAME > TEAM_NO_HIT_NO_RUN > TEAM_SHUTOUT_WIN
    """

    def evaluate(self, record, play_events=None) -> List[GameMilestoneAchievement]:
        achievements = []

        # Determine winning team
        if record.home_score > record.away_score:
            winning_team_id = record.home_team_id
            losing_team_id = record.away_team_id
        elif record.away_score > record.home_score:
            winning_team_id = record.away_team_id
            losing_team_id = record.home_team_id
        else:
            return achievements  # Tie game -> no team shutout win

        # Get pitching lines for winning team
        winning_pitchers = [p for p in record.pitching_lines if p.team_id == winning_team_id]
        if not winning_pitchers:
            return achievements

        total_outs = sum(p.outs for p in winning_pitchers)
        total_h = sum(p.h for p in winning_pitchers)
        total_r = sum(p.r for p in winning_pitchers)
        total_bb = sum(p.bb for p in winning_pitchers)

        if total_outs >= 27 and total_r == 0:
            if total_h == 0 and total_bb == 0:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=None,
                        competition_type=record.competition_type,
                        rule_key="TEAM_PERFECT_GAME",
                        title="팀 퍼펙트 게임",
                    )
                )
            elif total_h == 0:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=None,
                        competition_type=record.competition_type,
                        rule_key="TEAM_NO_HIT_NO_RUN",
                        title="팀 노히트 노런",
                    )
                )
            else:
                achievements.append(
                    GameMilestoneAchievement(
                        game_id=record.game_id,
                        player_id=None,
                        competition_type=record.competition_type,
                        rule_key="TEAM_SHUTOUT_WIN",
                        title="팀 완봉승",
                    )
                )

        return achievements
