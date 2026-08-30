from pathlib import Path
import pytest

from ootp_milestone_tracker.db.database import Database
from ootp_milestone_tracker.db.repository import Repository
from ootp_milestone_tracker.importer.game_import_service import GameImportService
from ootp_milestone_tracker.importer.game_models import BattingLine, GameRecord, PitchingLine
from ootp_milestone_tracker.services.season_service import SeasonService

SAMPLE_EXPORT_DIR = Path(
    r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg\import_export"
)


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "season_test.db"
    db = Database(db_path)
    db.initialize()
    return db


def test_live_season_aggregation_and_threshold_crossing(test_db):
    service = GameImportService(test_db)

    # Game 1: Player 1 gets 148 Hits
    rec1 = GameRecord(
        game_id=1001,
        title="Game 1",
        game_date="04/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        batting_lines=[BattingLine(player_id=1, name="Hitter", team_id=1, ab=148, h=148)],
    )
    service.import_game(rec1)

    repo = Repository(test_db)
    s_achs1 = repo.season_milestone_achievements()
    assert len(s_achs1) == 0  # 148 H < 150 H threshold

    # Game 2: Player 1 gets 4 Hits (Total 152 H -> crosses 150 H threshold)
    rec2 = GameRecord(
        game_id=1002,
        title="Game 2",
        game_date="04/02/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        batting_lines=[BattingLine(player_id=1, name="Hitter", team_id=1, ab=4, h=4)],
    )
    service.import_game(rec2)

    s_achs2 = repo.season_milestone_achievements()
    assert len(s_achs2) == 1
    assert s_achs2[0]["rule_key"] == "SEASON_HITS_150"
    assert s_achs2[0]["achieved_game_id"] == 1002
    assert s_achs2[0]["achieved_date"] == "04/02/2027"


def test_consecutive_threshold_preservation(test_db):
    season_service = SeasonService(test_db)
    repo = Repository(test_db)

    # Custom settings: Hits = [10, 20]
    custom_settings = {
        "SEASON_HITS": {"enabled": True, "thresholds": [10, 20]},
        "GENERAL": {"regular_season_game_target": 162},
    }
    season_service.save_season_settings(custom_settings)
    game_service = GameImportService(test_db)

    # Game 1: 12 H (crosses 10 H)
    rec1 = GameRecord(
        game_id=2001,
        title="Game 1",
        game_date="04/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        batting_lines=[BattingLine(player_id=1, name="Hitter", team_id=1, ab=12, h=12)],
    )
    game_service.import_game(rec1)

    achs1 = repo.season_milestone_achievements()
    assert len(achs1) == 1
    assert achs1[0]["rule_key"] == "SEASON_HITS_10"

    # Game 2: 10 H (Total 22 H -> crosses 20 H)
    rec2 = GameRecord(
        game_id=2002,
        title="Game 2",
        game_date="04/02/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        batting_lines=[BattingLine(player_id=1, name="Hitter", team_id=1, ab=10, h=10)],
    )
    game_service.import_game(rec2)

    achs2 = repo.season_milestone_achievements()
    keys2 = {a["rule_key"] for a in achs2}
    # BOTH thresholds preserved!
    assert "SEASON_HITS_10" in keys2
    assert "SEASON_HITS_20" in keys2


def test_finalization_eligibility_and_unreconciled(test_db):
    season_service = SeasonService(test_db)
    game_service = GameImportService(test_db)

    # Set tracked team to ID 1
    repo = Repository(test_db)
    repo.set_tracked_team(1)

    # Import 1 game (1/162 games -> Not eligible)
    rec1 = GameRecord(
        game_id=3001,
        title="Game 1",
        game_date="04/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        away_score=5,
        home_score=2,
        pitching_lines=[PitchingLine(player_id=10, name="Ace", team_id=1, outs=27, win=True, er=1, h=4, bb=1)],
    )
    game_service.import_game(rec1)

    proc, target, eligible = season_service.check_finalization_eligibility(2027, 1)
    assert proc == 1
    assert target == 162
    assert eligible is False

    # Continue Without Export
    res = season_service.finalize_season(2027, 1, continue_without_export=True)
    assert res["status"] == "finalized_unreconciled"

    state = repo.current_season_state(2027)
    assert state["status"] == "finalized_unreconciled"


def test_reconciliation_with_export(test_db):
    if not SAMPLE_EXPORT_DIR.exists():
        pytest.skip("Sample export directory not available")

    season_service = SeasonService(test_db)
    repo = Repository(test_db)
    repo.set_tracked_team(1)

    # Finalize with real export dir
    res = season_service.finalize_season(2027, 1, export_dir=SAMPLE_EXPORT_DIR, continue_without_export=True)
    assert res["status"] in ("finalized_reconciled", "finalized_unreconciled")

    # Check season achievement rows
    achs = repo.season_milestone_achievements()
    assert isinstance(achs, list)
