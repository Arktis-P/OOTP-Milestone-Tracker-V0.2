from typing import Dict, List, Optional
from .season_models import SeasonMilestoneAchievement


DEFAULT_SEASON_MILESTONE_SETTINGS = {
    "SEASON_HITS": {"enabled": True, "thresholds": [150, 200, 250, 300, 350]},
    "SEASON_HR": {"enabled": True, "thresholds": [20, 30, 40, 50, 60, 70, 80, 90, 100]},
    "SEASON_RBI": {"enabled": True, "thresholds": [75, 100, 125, 150, 175, 200]},
    "SEASON_RUNS": {"enabled": True, "thresholds": [75, 100, 125, 150, 175, 200]},
    "SEASON_SB": {"enabled": True, "thresholds": [20, 30, 40, 50, 60, 70, 80, 90, 100]},
    "SEASON_IP": {"enabled": True, "thresholds": [150, 200, 250, 300, 350]},
    "SEASON_STRIKEOUTS": {"enabled": True, "thresholds": [150, 200, 250, 300, 350, 400]},
    "SEASON_WINS": {"enabled": True, "thresholds": [10, 15, 20, 25, 30]},
    "SEASON_HOLDS": {"enabled": True, "thresholds": [10, 15, 20, 25, 30]},
    "SEASON_SAVES": {"enabled": True, "thresholds": [20, 30, 40, 50, 60, 70]},
    "TEAM_WINS": {"enabled": True, "thresholds": [100, 110, 120, 130, 140]},
    "SEASON_AVG": {"enabled": True, "thresholds": [0.275, 0.300, 0.325, 0.350, 0.375, 0.400]},
    "SEASON_OBP": {"enabled": True, "thresholds": [0.350, 0.375, 0.400, 0.425, 0.450, 0.475, 0.500]},
    "SEASON_OPS": {"enabled": True, "thresholds": [0.800, 0.900, 1.000, 1.100, 1.200, 1.300, 1.400, 1.500]},
    "SEASON_ERA": {"enabled": True, "thresholds": [3.0, 2.0, 1.0]},
    "GENERAL": {
        "regular_season_game_target": 162,
        "batting_rate_pa_per_team_game": 3.1,
        "pitching_rate_ip_per_team_game": 1.0,
    },
}


def evaluate_season_rate_milestones(
    batting_seasons: List[Dict],
    pitching_seasons: List[Dict],
    settings: Optional[Dict] = None,
) -> List[SeasonMilestoneAchievement]:
    """Evaluate final rate milestones for qualified players upon season finalization."""
    settings = settings or DEFAULT_SEASON_MILESTONE_SETTINGS
    gen_cfg = settings.get("GENERAL", DEFAULT_SEASON_MILESTONE_SETTINGS["GENERAL"])
    target_games = gen_cfg.get("regular_season_game_target", 162)

    pa_qualifier = gen_cfg.get("batting_rate_pa_per_team_game", 3.1) * target_games
    outs_qualifier = gen_cfg.get("pitching_rate_ip_per_team_game", 1.0) * target_games * 3

    achievements = []

    # 1. Batting Rates
    avg_cfg = settings.get("SEASON_AVG", DEFAULT_SEASON_MILESTONE_SETTINGS["SEASON_AVG"])
    obp_cfg = settings.get("SEASON_OBP", DEFAULT_SEASON_MILESTONE_SETTINGS["SEASON_OBP"])
    ops_cfg = settings.get("SEASON_OPS", DEFAULT_SEASON_MILESTONE_SETTINGS["SEASON_OPS"])

    for b in batting_seasons:
        if b.get("pa", 0) < pa_qualifier:
            continue

        pid = b["player_id"]
        season = b["season"]
        comp = b.get("competition_type", "regular_season")

        avg_val = b.get("avg", 0.0)
        obp_val = b.get("obp", 0.0)
        ops_val = b.get("ops", 0.0)

        # AVG (Highest tier only)
        if avg_cfg.get("enabled", True):
            reached = [t for t in sorted(avg_cfg.get("thresholds", [])) if avg_val >= t]
            if reached:
                t = reached[-1]
                achievements.append(
                    SeasonMilestoneAchievement(
                        entity_type="player",
                        entity_id=pid,
                        season=season,
                        competition_type=comp,
                        rule_key=f"SEASON_AVG_{int(t*1000)}",
                        title=f"시즌 타율 {t:.3f}+",
                        threshold_value=t,
                        achieved_value=avg_val,
                        source="final_export",
                    )
                )

        # OBP (Highest tier only)
        if obp_cfg.get("enabled", True):
            reached = [t for t in sorted(obp_cfg.get("thresholds", [])) if obp_val >= t]
            if reached:
                t = reached[-1]
                achievements.append(
                    SeasonMilestoneAchievement(
                        entity_type="player",
                        entity_id=pid,
                        season=season,
                        competition_type=comp,
                        rule_key=f"SEASON_OBP_{int(t*1000)}",
                        title=f"시즌 출루율 {t:.3f}+",
                        threshold_value=t,
                        achieved_value=obp_val,
                        source="final_export",
                    )
                )

        # OPS (Highest tier only)
        if ops_cfg.get("enabled", True):
            reached = [t for t in sorted(ops_cfg.get("thresholds", [])) if ops_val >= t]
            if reached:
                t = reached[-1]
                achievements.append(
                    SeasonMilestoneAchievement(
                        entity_type="player",
                        entity_id=pid,
                        season=season,
                        competition_type=comp,
                        rule_key=f"SEASON_OPS_{int(t*1000)}",
                        title=f"시즌 OPS {t:.3f}+",
                        threshold_value=t,
                        achieved_value=ops_val,
                        source="final_export",
                    )
                )

    # 2. Pitching Rates (ERA Bucket)
    era_cfg = settings.get("SEASON_ERA", DEFAULT_SEASON_MILESTONE_SETTINGS["SEASON_ERA"])
    for p in pitching_seasons:
        if p.get("outs", 0) < outs_qualifier:
            continue

        pid = p["player_id"]
        season = p["season"]
        comp = p.get("competition_type", "regular_season")
        era_val = p.get("era", 99.0)

        if era_cfg.get("enabled", True):
            if era_val < 1.0:
                achievements.append(
                    SeasonMilestoneAchievement(
                        entity_type="player",
                        entity_id=pid,
                        season=season,
                        competition_type=comp,
                        rule_key="SEASON_ERA_0XX",
                        title="시즌 평균자책점 0점대",
                        threshold_value=1.0,
                        achieved_value=era_val,
                        source="final_export",
                    )
                )
            elif era_val < 2.0:
                achievements.append(
                    SeasonMilestoneAchievement(
                        entity_type="player",
                        entity_id=pid,
                        season=season,
                        competition_type=comp,
                        rule_key="SEASON_ERA_1XX",
                        title="시즌 평균자책점 1점대",
                        threshold_value=2.0,
                        achieved_value=era_val,
                        source="final_export",
                    )
                )
            elif era_val < 3.0:
                achievements.append(
                    SeasonMilestoneAchievement(
                        entity_type="player",
                        entity_id=pid,
                        season=season,
                        competition_type=comp,
                        rule_key="SEASON_ERA_2XX",
                        title="시즌 평균자책점 2점대",
                        threshold_value=3.0,
                        achieved_value=era_val,
                        source="final_export",
                    )
                )

    return achievements
