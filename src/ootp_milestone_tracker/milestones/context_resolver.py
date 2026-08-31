from typing import List, Optional
from ..importer.game_models import GameRecord
from .context_models import AchievementContext


class ContextResolver:
    @staticmethod
    def resolve_game_batter_context(record: GameRecord, player_id: int, rule_key: str, achieved_val: float) -> AchievementContext:
        """Resolve context for batter game milestones."""
        b_line = next((b for b in record.batting_lines if b.player_id == player_id), None)
        if not b_line:
            return AchievementContext(resolution_status="partial", game_id=record.game_id, game_date=record.game_date)

        summary = f"{b_line.ab}타수 {b_line.h}안타"
        if b_line.hr > 0:
            summary += f" {b_line.hr}홈런"
        if b_line.rbi > 0:
            summary += f" {b_line.rbi}타점"
        if b_line.sb > 0:
            summary += f" {b_line.sb}도루"

        # Check multi-HR or Grand Slam events
        events = [ev for ev in record.batting_events if ev.player_id == player_id]
        hr_events = [ev for ev in events if ev.event_type == "HR"]

        if rule_key == "GAME_GRAND_SLAM" and hr_events:
            ev = hr_events[0]
            ctx_text = ev.context_text or ""
            return AchievementContext(
                resolution_status="play_resolved",
                game_id=record.game_id,
                game_date=record.game_date,
                opponent_player_id=ev.opponent_player_id,
                rbi_count=4,
                raw_context=ctx_text if ctx_text else summary,
                game_line_summary=summary,
            )

        if "HR" in rule_key and len(hr_events) >= 2:
            raw_hr = " & ".join(ev.context_text for ev in hr_events if ev.context_text)
            return AchievementContext(
                resolution_status="play_resolved",
                game_id=record.game_id,
                game_date=record.game_date,
                raw_context=raw_hr if raw_hr else summary,
                game_line_summary=summary,
            )

        return AchievementContext(
            resolution_status="game_resolved",
            game_id=record.game_id,
            game_date=record.game_date,
            game_line_summary=summary,
        )

    @staticmethod
    def resolve_game_pitcher_context(record: GameRecord, player_id: int, rule_key: str, achieved_val: float) -> AchievementContext:
        """Resolve context for pitcher game milestones."""
        p_line = next((p for p in record.pitching_lines if p.player_id == player_id), None)
        if not p_line:
            return AchievementContext(resolution_status="partial", game_id=record.game_id, game_date=record.game_date)

        outs = p_line.outs
        ip_str = f"{outs // 3}.{outs % 3}이닝"
        summary = f"{ip_str} {p_line.h}피안타 {p_line.er}실점 {p_line.so}탈삼진"

        if rule_key == "GAME_SHUTOUT_WIN":
            summary = f"{ip_str} 무피안타 무실점 {p_line.so}탈삼진 완봉승" if p_line.h == 0 else f"{ip_str} {p_line.h}피안타 무실점 {p_line.so}탈삼진 완봉승"
        elif rule_key == "GAME_COMPLETE_GAME_WIN":
            summary += " 완투승"
        elif rule_key == "GAME_NO_HIT_NO_RUN":
            summary = f"{ip_str} 무피안타 무실점 {p_line.so}탈삼진 노히트 노런 승리"
        elif rule_key == "GAME_PERFECT_GAME":
            summary = f"{ip_str} 무피안타 무실점 {p_line.so}탈삼진 퍼펙트 게임 승리"

        return AchievementContext(
            resolution_status="game_resolved",
            game_id=record.game_id,
            game_date=record.game_date,
            game_line_summary=summary,
        )

    @staticmethod
    def resolve_game_team_context(record: GameRecord, rule_key: str) -> AchievementContext:
        """Resolve context for team game milestones."""
        score_summary = f"{record.away_score}-{record.home_score}"

        if rule_key.startswith("TEAM_STARTERS_") or rule_key.startswith("TEAM_APPEARED_"):
            lines = record.batting_lines
            if "STARTERS" in rule_key:
                lines = [b for b in lines if getattr(b, "is_starter", False) or True][:9]
            names = [b.name for b in lines if b.name]
            return AchievementContext(
                resolution_status="game_resolved",
                game_id=record.game_id,
                game_date=record.game_date,
                lineup_names=names,
            )

        return AchievementContext(
            resolution_status="game_resolved",
            game_id=record.game_id,
            game_date=record.game_date,
            raw_context=score_summary,
        )

    @staticmethod
    def resolve_crossing_play_context(
        record: GameRecord, player_id: int, stat_key: str, pre_game_total: float, target_val: float
    ) -> AchievementContext:
        """Resolve exact threshold crossing play for season and career counting milestones."""
        events = [ev for ev in record.batting_events if ev.player_id == player_id]

        if stat_key == "HR":
            hr_events = [ev for ev in events if ev.event_type == "HR"]
            if hr_events:
                ev = hr_events[-1]
                return AchievementContext(
                    resolution_status="play_resolved",
                    game_id=record.game_id,
                    game_date=record.game_date,
                    opponent_player_id=ev.opponent_player_id,
                    raw_context=ev.context_text,
                )

        b_line = next((b for b in record.batting_lines if b.player_id == player_id), None)
        p_line = next((p for p in record.pitching_lines if p.player_id == player_id), None)

        line_summary = None
        if b_line:
            line_summary = f"{b_line.ab}타수 {b_line.h}안타"
        elif p_line:
            outs = p_line.outs
            line_summary = f"{outs // 3}.{outs % 3}이닝 {p_line.so}탈삼진"

        return AchievementContext(
            resolution_status="game_resolved",
            game_id=record.game_id,
            game_date=record.game_date,
            game_line_summary=line_summary,
        )
