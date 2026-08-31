from pathlib import Path
import pytest

from ootp_milestone_tracker.db.database import Database
from ootp_milestone_tracker.db.repository import Repository
from ootp_milestone_tracker.importer.game_import_service import GameImportService
from ootp_milestone_tracker.importer.game_models import BattingLine, GameRecord, PitchingLine
from ootp_milestone_tracker.milestones.context_models import AchievementContext
from ootp_milestone_tracker.milestones.context_renderer import render_korean_context
from ootp_milestone_tracker.services.career_service import CareerService
from ootp_milestone_tracker.services.season_service import SeasonService


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "career_test.db"
    db = Database(db_path)
    db.initialize()
    return db


def test_season_bb_extension(test_db):
    game_service = GameImportService(test_db)
    repo = Repository(test_db)

    # Import Game 1 with 49 BB
    rec1 = GameRecord(
        game_id=4001,
        title="Game 1",
        game_date="04/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        batting_lines=[BattingLine(player_id=1, name="Walker", team_id=1, ab=100, bb=49)],
    )
    game_service.import_game(rec1)

    s_achs1 = repo.season_milestone_achievements()
    assert not any(a["rule_key"] == "SEASON_BB_50" for a in s_achs1)

    # Import Game 2 with 2 BB (Total 51 BB -> crosses 50 BB threshold)
    rec2 = GameRecord(
        game_id=4002,
        title="Game 2",
        game_date="04/02/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        batting_lines=[BattingLine(player_id=1, name="Walker", team_id=1, ab=2, bb=2)],
    )
    game_service.import_game(rec2)

    s_achs2 = repo.season_milestone_achievements()
    bb_achs = [a for a in s_achs2 if a["rule_key"] == "SEASON_BB_50"]
    assert len(bb_achs) == 1
    assert bb_achs[0]["achieved_game_id"] == 4002
    assert bb_achs[0]["achieved_date"] == "04/02/2027"


def test_career_aggregation_and_open_ended_ladders(test_db):
    career_service = CareerService(test_db)
    game_service = GameImportService(test_db)
    repo = Repository(test_db)

    # Import 10 games with 150 H each (Total 1500 H -> crosses 1500 H career threshold)
    for i in range(1, 11):
        rec = GameRecord(
            game_id=5000 + i,
            title=f"Game {i}",
            game_date=f"04/{i:02d}/2027",
            season=2027,
            competition_type="regular_season",
            away_team_id=1,
            home_team_id=2,
            batting_lines=[BattingLine(player_id=1, name="Slugger", team_id=1, ab=150, h=150, hr=20)],
        )
        game_service.import_game(rec)

    totals = career_service.get_career_totals(1)
    assert totals["h"] == 1500
    assert totals["hr"] == 200

    c_achs = repo.career_milestone_achievements(player_id=1)
    keys = {a["rule_key"] for a in c_achs}
    assert "CAREER_HITS_1500" in keys
    assert "CAREER_HR_200" in keys


def test_unified_korean_context_renderer():
    # Grand Slam
    ctx_gs = AchievementContext(
        resolution_status="play_resolved",
        inning=6,
        half="bottom",
        outs_before=1,
        base_state_before="만루",
        rbi_count=4,
        opponent_player_name="B. Rodriguez",
    )
    rendered_gs = render_korean_context("GAME_GRAND_SLAM", ctx_gs)
    assert "6회말 1사 만루에서 만루 홈런" in rendered_gs

    # Pitcher Shutout Win
    ctx_sho = AchievementContext(
        resolution_status="game_resolved",
        game_line_summary="9.0이닝 무피안타 무실점 10탈삼진 완봉승",
    )
    rendered_sho = render_korean_context("GAME_SHUTOUT_WIN", ctx_sho)
    assert "완봉승" in rendered_sho

    # Team Lineup
    ctx_team = AchievementContext(
        resolution_status="game_resolved",
        lineup_names=["홍창기", "박해민", "딘", "문보경", "송찬의"],
    )
    rendered_team = render_korean_context("TEAM_STARTERS_ALL_HIT", ctx_team)
    assert "선발 (홍창기-박해민-딘-문보경-송찬의) 전원 안타" in rendered_team
