from pathlib import Path
import pytest

from ootp_milestone_tracker.db.database import Database
from ootp_milestone_tracker.db.repository import Repository
from ootp_milestone_tracker.importer.game_import_service import GameImportService
from ootp_milestone_tracker.importer.game_models import BattingEvent, BattingLine, GameRecord, PitchingLine
from ootp_milestone_tracker.milestones.game_evaluator import DEFAULT_GAME_MILESTONE_SETTINGS, GameMilestoneEvaluator

SAMPLE_BOX_DIR = Path(
    r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg\news\html\box_scores"
)


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "game_settings_test.db"
    db = Database(db_path)
    db.initialize()
    return db


def test_team_appeared_semantics():
    evaluator = GameMilestoneEvaluator()

    # Case 1: All parsed rows H>=1 -> APPEARED_ALL_HIT Yes
    rec1 = GameRecord(
        game_id=500,
        title="Test",
        game_date="05/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=10,
        home_team_id=20,
        batting_lines=[
            BattingLine(player_id=i, name=f"P{i}", team_id=10, h=1, is_starter=True) for i in range(1, 10)
        ]
        + [BattingLine(player_id=99, name="Sub", team_id=10, h=1, ab=0, bb=0, is_starter=False)],
    )
    achs1 = [a.rule_key for a in evaluator.evaluate_game(rec1)]
    assert "TEAM_STARTERS_ALL_HIT" in achs1
    assert "TEAM_APPEARED_ALL_HIT" in achs1

    # Case 2: One parsed row H=0 (even with 0 AB/BB) -> APPEARED_ALL_HIT No
    rec2 = GameRecord(
        game_id=501,
        title="Test",
        game_date="05/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=10,
        home_team_id=20,
        batting_lines=[
            BattingLine(player_id=i, name=f"P{i}", team_id=10, h=1, is_starter=True) for i in range(1, 10)
        ]
        + [BattingLine(player_id=99, name="Sub", team_id=10, h=0, ab=0, bb=0, is_starter=False)],
    )
    achs2 = [a.rule_key for a in evaluator.evaluate_game(rec2)]
    assert "TEAM_STARTERS_ALL_HIT" in achs2
    assert "TEAM_APPEARED_ALL_HIT" not in achs2

    # Case 3: All parsed rows RBI>=1 -> APPEARED_ALL_RBI Yes
    rec3 = GameRecord(
        game_id=502,
        title="Test",
        game_date="05/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=10,
        home_team_id=20,
        batting_lines=[
            BattingLine(player_id=i, name=f"P{i}", team_id=10, rbi=1, is_starter=True) for i in range(1, 10)
        ]
        + [BattingLine(player_id=99, name="Sub", team_id=10, rbi=1, is_starter=False)],
    )
    achs3 = [a.rule_key for a in evaluator.evaluate_game(rec3)]
    assert "TEAM_STARTERS_ALL_RBI" in achs3
    assert "TEAM_APPEARED_ALL_RBI" in achs3

    # Case 4: One parsed row RBI=0 -> APPEARED_ALL_RBI No
    rec4 = GameRecord(
        game_id=503,
        title="Test",
        game_date="05/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=10,
        home_team_id=20,
        batting_lines=[
            BattingLine(player_id=i, name=f"P{i}", team_id=10, rbi=1, is_starter=True) for i in range(1, 10)
        ]
        + [BattingLine(player_id=99, name="Sub", team_id=10, rbi=0, is_starter=False)],
    )
    achs4 = [a.rule_key for a in evaluator.evaluate_game(rec4)]
    assert "TEAM_STARTERS_ALL_RBI" in achs4
    assert "TEAM_APPEARED_ALL_RBI" not in achs4


def test_custom_threshold_configuration():
    custom_settings = {
        "GAME_HITS": {"enabled": True, "thresholds": [3, 5, 8]},
        "GAME_RBI": {"enabled": False, "thresholds": [5, 6]},
        "GAME_HR": {"enabled": True, "thresholds": [2, 4]},
        "GAME_SB": {"enabled": True, "thresholds": [3]},
        "GAME_STRIKEOUTS": {"enabled": True, "thresholds": [12]},
    }
    evaluator = GameMilestoneEvaluator(settings=custom_settings)

    # Boundary testing for Hits [3, 5, 8]
    test_cases = [
        (2, None),
        (3, "GAME_HITS_3"),
        (4, "GAME_HITS_3"),
        (5, "GAME_HITS_5"),
        (7, "GAME_HITS_5"),
        (8, "GAME_HITS_8"),
        (9, "GAME_HITS_8"),
    ]
    for h_val, expected_key in test_cases:
        rec = GameRecord(
            game_id=600 + h_val,
            title="Test",
            game_date="05/01/2027",
            season=2027,
            competition_type="regular_season",
            away_team_id=1,
            home_team_id=2,
            batting_lines=[BattingLine(player_id=1, name="P1", team_id=1, h=h_val)],
        )
        achs = [a for a in evaluator.evaluate_game(rec) if a.rule_key.startswith("GAME_HITS_")]
        if expected_key is None:
            assert len(achs) == 0
        else:
            assert len(achs) == 1
            assert achs[0].rule_key == expected_key
            assert achs[0].achieved_value == float(h_val)

    # Test Disabled Family (GAME_RBI disabled -> 0 achievements for RBI=6)
    rec_rbi = GameRecord(
        game_id=699,
        title="Test",
        game_date="05/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        batting_lines=[BattingLine(player_id=1, name="P1", team_id=1, rbi=6)],
    )
    achs_rbi = [a for a in evaluator.evaluate_game(rec_rbi) if a.rule_key.startswith("GAME_RBI_")]
    assert len(achs_rbi) == 0


def test_repository_settings_and_rebuild(test_db):
    repo = Repository(test_db)

    # 1. Defaults initial read
    defaults = repo.get_game_milestone_rule_settings()
    assert defaults["GAME_HITS"]["thresholds"] == [4, 5, 6, 7]

    # 2. Store sample game under defaults
    rec = GameRecord(
        game_id=700,
        title="Test",
        game_date="05/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        batting_lines=[BattingLine(player_id=10, name="Slugger", team_id=1, ab=4, h=4, doubles=1, triples=1, hr=1, rbi=5)],
        batting_events=[
            BattingEvent(game_id=700, player_id=10, event_index=1, event_type="HOME_RUN", context_text="3 on")
        ],
    )
    service = GameImportService(test_db)
    service.import_game(rec)

    # Check achievements under defaults: GAME_HITS_4, GAME_RBI_5, GAME_GRAND_SLAM, GAME_CYCLE
    achs_before = repo.game_milestone_achievements()
    keys_before = {a["rule_key"] for a in achs_before}
    assert "GAME_HITS_4" in keys_before
    assert "GAME_RBI_5" in keys_before
    assert "GAME_GRAND_SLAM" in keys_before
    assert "GAME_CYCLE" in keys_before

    # 3. Change settings: Hits = [3, 6], RBI = disabled
    new_settings = {
        "GAME_HITS": {"enabled": True, "thresholds": [3, 6]},
        "GAME_RBI": {"enabled": False, "thresholds": [5, 6]},
        "GAME_HR": {"enabled": True, "thresholds": [2, 3, 4, 5]},
        "GAME_SB": {"enabled": True, "thresholds": [3, 4, 5, 6, 7]},
        "GAME_STRIKEOUTS": {"enabled": True, "thresholds": [10, 15, 20, 25, 30]},
    }
    repo.save_game_milestone_rule_settings(new_settings)
    repo.rebuild_game_milestone_achievements(new_settings)

    # 4. Check achievements after rebuild
    achs_after = repo.game_milestone_achievements()
    keys_after = {a["rule_key"] for a in achs_after}

    # GAME_HITS_4 should be replaced by GAME_HITS_3 (since H=4 reaches threshold 3 in [3, 6])
    assert "GAME_HITS_3" in keys_after
    assert "GAME_HITS_4" not in keys_after
    # GAME_RBI should be removed since RBI is disabled
    assert not any(k.startswith("GAME_RBI_") for k in keys_after)
    # Named achievements (GAME_GRAND_SLAM, GAME_CYCLE) must remain intact!
    assert "GAME_GRAND_SLAM" in keys_after
    assert "GAME_CYCLE" in keys_after

    # 5. Re-run rebuild -> Idempotent, identical rows
    repo.rebuild_game_milestone_achievements(new_settings)
    achs_rebuild2 = repo.game_milestone_achievements()
    assert len(achs_rebuild2) == len(achs_after)
