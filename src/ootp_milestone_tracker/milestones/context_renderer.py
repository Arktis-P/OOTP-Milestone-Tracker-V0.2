from typing import Optional
from .context_models import AchievementContext


def format_ip(outs: int) -> str:
    full = outs // 3
    rem = outs % 3
    return f"{full}.{rem}이닝"


def render_korean_context(rule_key: str, ctx: AchievementContext, achieved_val: Optional[float] = None) -> str:
    """Render canonical Korean context text according to design doc guidelines."""
    # 1. Pitching Season/Career Final Rates & IP/SO/W/HOLD/SV
    if rule_key.startswith("SEASON_AVG"):
        val_str = f"{achieved_val:.3f}" if achieved_val is not None else ""
        return f"시즌 타율 {val_str}".strip()
    if rule_key.startswith("SEASON_OBP"):
        val_str = f"{achieved_val:.3f}" if achieved_val is not None else ""
        return f"시즌 출루율 {val_str}".strip()
    if rule_key.startswith("SEASON_OPS"):
        val_str = f"{achieved_val:.3f}" if achieved_val is not None else ""
        return f"시즌 OPS {val_str}".strip()
    if rule_key.startswith("SEASON_ERA"):
        val_str = f"{achieved_val:.2f}" if achieved_val is not None else ""
        return f"시즌 ERA {val_str}".strip()

    # 2. Team Postseason & Progression
    if rule_key == "POSTSEASON_BERTH":
        if ctx.raw_context:
            return ctx.raw_context
        return "포스트시즌 진출"
    if rule_key == "DIVISION_CHAMPION":
        return ctx.raw_context or "디비전 우승 확정"
    if rule_key in ("WILD_CARD_SERIES_WIN", "DIVISION_SERIES_WIN", "LEAGUE_CHAMPIONSHIP_SERIES_WIN", "WORLD_SERIES_WIN"):
        if ctx.raw_context:
            return ctx.raw_context
        name_map = {
            "WILD_CARD_SERIES_WIN": "와일드 카드 시리즈 우승",
            "DIVISION_SERIES_WIN": "디비전 시리즈 우승",
            "LEAGUE_CHAMPIONSHIP_SERIES_WIN": "리그 챔피언십 시리즈 우승",
            "WORLD_SERIES_WIN": "월드 시리즈 우승",
        }
        return name_map[rule_key]

    # 3. Team Game Milestones
    if rule_key.startswith("TEAM_STARTERS_") or rule_key.startswith("TEAM_APPEARED_"):
        target_str = "선발" if "STARTERS" in rule_key else "출장 전원"
        stat_str = "안타" if "HIT" in rule_key else "타점"
        if ctx.lineup_names:
            names_join = "-".join(ctx.lineup_names)
            return f"{target_str} ({names_join}) 전원 {stat_str}"
        return f"{target_str} 전원 {stat_str}"

    if rule_key == "TEAM_SHUTOUT_WIN":
        score_str = ctx.raw_context or ""
        return f"{score_str} 승리 · 팀 완봉승".strip(" ·")
    if rule_key == "TEAM_NO_HIT_NO_RUN":
        score_str = ctx.raw_context or ""
        return f"{score_str} 승리 · 팀 노히트 노런 (합작)".strip(" ·")
    if rule_key == "TEAM_PERFECT_GAME":
        score_str = ctx.raw_context or ""
        return f"{score_str} 승리 · 팀 퍼펙트 게임".strip(" ·")

    # 4. Play-Resolved Events (Hit, HR, RBI, Run, SB, BB, SO)
    if ctx.resolution_status == "play_resolved" or (ctx.inning and ctx.half):
        parts = []
        half_str = "초" if ctx.half in ("top", "초") else "말"
        parts.append(f"{ctx.inning}회{half_str}")

        if ctx.outs_before is not None:
            outs_map = {0: "무사", 1: "1사", 2: "2사"}
            parts.append(outs_map.get(ctx.outs_before, f"{ctx.outs_before}사"))

        if ctx.base_state_before:
            parts.append(ctx.base_state_before)

        loc_str = " ".join(parts)

        # Walk
        if "BB" in rule_key or "WALK" in rule_key:
            pitch_str = f" {ctx.pitch_count}구" if ctx.pitch_count else ""
            return f"{loc_str}에서{pitch_str} 볼넷 출루".strip()

        # HR
        if "HR" in rule_key or "GRAND_SLAM" in rule_key:
            rbi = ctx.rbi_count or (4 if "GRAND_SLAM" in rule_key else 1)
            hr_type_map = {1: "솔로 홈런", 2: "2점 홈런", 3: "3점 홈런", 4: "만루 홈런"}
            hr_name = hr_type_map.get(rbi, f"{rbi}점 홈런")
            opp_str = f" off {ctx.opponent_player_name}" if ctx.opponent_player_name else ""
            return f"{loc_str}에서 {hr_name}{opp_str}".strip()

        # Hit / RBI
        if "HIT" in rule_key or "RBI" in rule_key:
            rbi_str = f" {ctx.rbi_count}타점" if ctx.rbi_count else ""
            play_res = ctx.play_result or "안타"
            return f"{loc_str}에서{rbi_str} {play_res}".strip()

        # Run
        if "RUN" in rule_key or "R" in rule_key:
            batter_str = f", {ctx.batter_name} 타석에" if ctx.batter_name else ""
            return f"{loc_str}{batter_str} 득점".strip()

        # Stolen Base
        if "SB" in rule_key or "STEAL" in rule_key:
            dest = ctx.destination_base or "2루"
            batter_str = f", {ctx.batter_name} 타석에" if ctx.batter_name else ""
            return f"{loc_str}{batter_str} {dest} 도루".strip()

        # Strikeout
        if "STRIKEOUT" in rule_key or "SO" in rule_key:
            pitch_str = f" {ctx.pitch_count}구" if ctx.pitch_count else ""
            opp_str = f" ({ctx.opponent_player_name})" if ctx.opponent_player_name else ""
            return f"{loc_str}{opp_str}{pitch_str} 헛스윙 삼진".strip()

    # 5. Game-Resolved Summaries
    if ctx.game_line_summary:
        return ctx.game_line_summary

    if ctx.raw_context:
        return ctx.raw_context

    return f"달성: {achieved_val:,.0f}" if achieved_val is not None else "달성"
