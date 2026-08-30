from pathlib import Path
import pytest

from ootp_milestone_tracker.db.database import Database
from ootp_milestone_tracker.db.repository import Repository
from ootp_milestone_tracker.importer.game_box_parser import parse_game_box
from ootp_milestone_tracker.importer.game_import_service import GameImportService
from ootp_milestone_tracker.importer.game_models import BattingEvent, BattingLine, GameRecord, PitchingLine
from ootp_milestone_tracker.milestones.game_evaluator import GameMilestoneEvaluator
from ootp_milestone_tracker.milestones.game_rules import (
    CycleRule,
    GrandSlamRule,
    HitsThresholdRule,
    MultiHRRule,
    NoHitterRule,
    PerfectGameRule,
    ShutoutRule,
    StrikeoutsThresholdRule,
)

SAMPLE_BOX_DIR = Path(
    r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg\news\html\box_scores"
)


@pytest.fixture
def test_db(tmp_path):
    db_path = tmp_path / "game_test.db"
    db = Database(db_path)
    db.initialize()
    return db


def test_game_box_parser_real_games():
    if not SAMPLE_BOX_DIR.exists():
        pytest.skip("Sample box score directory not available on local machine")

    # Game 1
    g1 = parse_game_box(SAMPLE_BOX_DIR / "game_box_1.html")
    assert g1.game_id == 1
    assert g1.game_date == "03/30/2027"
    assert g1.season == 2027
    assert len(g1.batting_lines) > 0
    assert len(g1.pitching_lines) > 0

    # Game 1000: HR text parsing verification
    g1000 = parse_game_box(SAMPLE_BOX_DIR / "game_box_1000.html")
    assert g1000.game_id == 1000
    hr_events = [ev for ev in g1000.batting_events if ev.event_type == "HOME_RUN"]
    assert len(hr_events) >= 2
    # Verify season total extracted from lower text
    assert any(ev.season_total == 22 for ev in hr_events)


def test_idempotency_and_persistence(test_db):
    if not SAMPLE_BOX_DIR.exists():
        pytest.skip("Sample box score directory not available")

    service = GameImportService(test_db)
    box_path = SAMPLE_BOX_DIR / "game_box_1000.html"

    # First import
    is_new1, count1 = service.import_game_file(box_path)
    assert is_new1 is True

    # Second import (same game)
    is_new2, count2 = service.import_game_file(box_path)
    assert is_new2 is False
    assert count2 == 0

    # Verify DB table row counts
    repo = Repository(test_db)
    achievements = repo.game_milestone_achievements()
    # Unique game_id in games table
    with test_db.connect() as conn:
        g_count = conn.execute("SELECT COUNT(*) FROM games WHERE game_id = 1000").fetchone()[0]
        assert g_count == 1


def test_game_rules_fixtures():
    # 1. 5 Hits Rule
    rec_hits = GameRecord(
        game_id=9001,
        title="Test Game",
        game_date="05/10/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        batting_lines=[BattingLine(player_id=101, name="Hit King", team_id=1, h=5, ab=5)],
    )
    evaluator = GameMilestoneEvaluator([HitsThresholdRule(5)])
    achs = evaluator.evaluate_game(rec_hits)
    assert len(achs) == 1
    assert achs[0].rule_key == "GAME_HITS_5"
    assert achs[0].player_id == 101

    # 2. Multi-HR Rule (using lower summary HR count)
    rec_hr = GameRecord(
        game_id=9002,
        title="Test Game",
        game_date="05/11/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        batting_lines=[BattingLine(player_id=102, name="Slugger", team_id=1, hr=2, ab=4, h=2)],
    )
    evaluator_hr = GameMilestoneEvaluator([MultiHRRule(2)])
    achs_hr = evaluator_hr.evaluate_game(rec_hr)
    assert len(achs_hr) == 1
    assert achs_hr[0].rule_key == "GAME_MULTI_HR"

    # 3. 10 Strikeouts Rule
    rec_so = GameRecord(
        game_id=9003,
        title="Test Game",
        game_date="05/12/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        pitching_lines=[PitchingLine(player_id=201, name="Ace Pitcher", team_id=1, outs=27, so=11)],
    )
    evaluator_so = GameMilestoneEvaluator([StrikeoutsThresholdRule(10)])
    achs_so = evaluator_so.evaluate_game(rec_so)
    assert len(achs_so) == 1
    assert achs_so[0].rule_key == "GAME_STRIKEOUTS_10"

    # 4. Grand Slam Rule
    rec_gs = GameRecord(
        game_id=9004,
        title="Test Game",
        game_date="05/13/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        batting_events=[
            BattingEvent(
                game_id=9004,
                player_id=103,
                event_index=1,
                event_type="HOME_RUN",
                context_text="1, 5th Inning off J. Doe, 3 on, 2 outs",
            )
        ],
    )
    evaluator_gs = GameMilestoneEvaluator([GrandSlamRule()])
    achs_gs = evaluator_gs.evaluate_game(rec_gs)
    assert len(achs_gs) == 1
    assert achs_gs[0].rule_key == "GAME_GRAND_SLAM"

    # 5. Cycle Rule
    rec_cycle = GameRecord(
        game_id=9005,
        title="Test Game",
        game_date="05/14/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        batting_lines=[
            BattingLine(player_id=104, name="Cycle Batter", team_id=1, ab=4, h=4, doubles=1, triples=1, hr=1)
        ],
    )
    evaluator_cycle = GameMilestoneEvaluator([CycleRule()])
    achs_cycle = evaluator_cycle.evaluate_game(rec_cycle)
    assert len(achs_cycle) == 1
    assert achs_cycle[0].rule_key == "GAME_CYCLE"

    # 6. Shutout & No-Hitter & Perfect Game Rules
    rec_perf = GameRecord(
        game_id=9006,
        title="Test Game",
        game_date="05/15/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        pitching_lines=[
            PitchingLine(player_id=202, name="Perfect Pitcher", team_id=1, outs=27, h=0, r=0, er=0, bb=0, so=15)
        ],
    )
    evaluator_pitch = GameMilestoneEvaluator([ShutoutRule(), NoHitterRule(), PerfectGameRule()])
    achs_pitch = evaluator_pitch.evaluate_game(rec_perf)
    assert len(achs_pitch) == 3
    rule_keys = [a.rule_key for a in achs_pitch]
    assert "GAME_SHUTOUT" in rule_keys
    assert "GAME_NO_HITTER" in rule_keys
    assert "GAME_PERFECT_GAME" in rule_keys
