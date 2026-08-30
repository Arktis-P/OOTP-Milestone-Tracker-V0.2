from pathlib import Path
import pytest

from ootp_milestone_tracker.db.database import Database
from ootp_milestone_tracker.db.repository import Repository
from ootp_milestone_tracker.importer.game_box_parser import parse_game_box
from ootp_milestone_tracker.importer.game_import_service import GameImportService
from ootp_milestone_tracker.importer.game_models import BattingEvent, BattingLine, GameRecord, PitchingLine
from ootp_milestone_tracker.milestones.game_evaluator import GameMilestoneEvaluator

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

    g1 = parse_game_box(SAMPLE_BOX_DIR / "game_box_1.html")
    assert g1.game_id == 1
    assert g1.game_date == "03/30/2027"
    assert g1.season == 2027

    g1000 = parse_game_box(SAMPLE_BOX_DIR / "game_box_1000.html")
    assert g1000.game_id == 1000
    hr_events = [ev for ev in g1000.batting_events if ev.event_type == "HOME_RUN"]
    assert len(hr_events) >= 2
    assert any(ev.season_total == 22 for ev in hr_events)


def test_hits_threshold_boundaries():
    evaluator = GameMilestoneEvaluator()

    for h_val, expected_key in [
        (3, None),
        (4, "GAME_HITS_4"),
        (5, "GAME_HITS_5"),
        (6, "GAME_HITS_6"),
        (7, "GAME_HITS_7"),
        (8, "GAME_HITS_7"),
    ]:
        rec = GameRecord(
            game_id=100,
            title="Test",
            game_date="05/01/2027",
            season=2027,
            competition_type="regular_season",
            away_team_id=1,
            home_team_id=2,
            batting_lines=[BattingLine(player_id=1, name="P1", team_id=1, ab=h_val, h=h_val)],
        )
        achs = [a for a in evaluator.evaluate_game(rec) if a.rule_key.startswith("GAME_HITS_")]
        if expected_key is None:
            assert len(achs) == 0
        else:
            assert len(achs) == 1
            assert achs[0].rule_key == expected_key
            assert achs[0].achieved_value == float(h_val)


def test_rbi_threshold_boundaries():
    evaluator = GameMilestoneEvaluator()

    for rbi_val, expected_key in [
        (4, None),
        (5, "GAME_RBI_5"),
        (6, "GAME_RBI_6"),
        (7, "GAME_RBI_7"),
        (8, "GAME_RBI_8"),
        (9, "GAME_RBI_9"),
        (10, "GAME_RBI_10"),
        (11, "GAME_RBI_10"),
    ]:
        rec = GameRecord(
            game_id=101,
            title="Test",
            game_date="05/01/2027",
            season=2027,
            competition_type="regular_season",
            away_team_id=1,
            home_team_id=2,
            batting_lines=[BattingLine(player_id=1, name="P1", team_id=1, rbi=rbi_val)],
        )
        achs = [a for a in evaluator.evaluate_game(rec) if a.rule_key.startswith("GAME_RBI_")]
        if expected_key is None:
            assert len(achs) == 0
        else:
            assert len(achs) == 1
            assert achs[0].rule_key == expected_key
            assert achs[0].achieved_value == float(rbi_val)


def test_hr_threshold_boundaries():
    evaluator = GameMilestoneEvaluator()

    for hr_val, expected_key in [
        (1, None),
        (2, "GAME_HR_2"),
        (3, "GAME_HR_3"),
        (4, "GAME_HR_4"),
        (5, "GAME_HR_5"),
        (6, "GAME_HR_5"),
    ]:
        rec = GameRecord(
            game_id=102,
            title="Test",
            game_date="05/01/2027",
            season=2027,
            competition_type="regular_season",
            away_team_id=1,
            home_team_id=2,
            batting_lines=[BattingLine(player_id=1, name="P1", team_id=1, hr=hr_val)],
        )
        achs = [a for a in evaluator.evaluate_game(rec) if a.rule_key.startswith("GAME_HR_")]
        if expected_key is None:
            assert len(achs) == 0
        else:
            assert len(achs) == 1
            assert achs[0].rule_key == expected_key
            assert achs[0].achieved_value == float(hr_val)


def test_sb_threshold_boundaries():
    evaluator = GameMilestoneEvaluator()

    for sb_val, expected_key in [
        (2, None),
        (3, "GAME_SB_3"),
        (4, "GAME_SB_4"),
        (5, "GAME_SB_5"),
        (6, "GAME_SB_6"),
        (7, "GAME_SB_7"),
        (8, "GAME_SB_7"),
    ]:
        rec = GameRecord(
            game_id=103,
            title="Test",
            game_date="05/01/2027",
            season=2027,
            competition_type="regular_season",
            away_team_id=1,
            home_team_id=2,
            batting_lines=[BattingLine(player_id=1, name="P1", team_id=1, sb=sb_val)],
        )
        achs = [a for a in evaluator.evaluate_game(rec) if a.rule_key.startswith("GAME_SB_")]
        if expected_key is None:
            assert len(achs) == 0
        else:
            assert len(achs) == 1
            assert achs[0].rule_key == expected_key
            assert achs[0].achieved_value == float(sb_val)


def test_so_threshold_boundaries():
    evaluator = GameMilestoneEvaluator()

    for so_val, expected_key in [
        (9, None),
        (10, "GAME_STRIKEOUTS_10"),
        (14, "GAME_STRIKEOUTS_10"),
        (15, "GAME_STRIKEOUTS_15"),
        (19, "GAME_STRIKEOUTS_15"),
        (20, "GAME_STRIKEOUTS_20"),
        (25, "GAME_STRIKEOUTS_25"),
        (30, "GAME_STRIKEOUTS_30"),
        (31, "GAME_STRIKEOUTS_30"),
    ]:
        rec = GameRecord(
            game_id=104,
            title="Test",
            game_date="05/01/2027",
            season=2027,
            competition_type="regular_season",
            away_team_id=1,
            home_team_id=2,
            pitching_lines=[PitchingLine(player_id=2, name="Ace", team_id=1, outs=27, so=so_val)],
        )
        achs = [a for a in evaluator.evaluate_game(rec) if a.rule_key.startswith("GAME_STRIKEOUTS_")]
        if expected_key is None:
            assert len(achs) == 0
        else:
            assert len(achs) == 1
            assert achs[0].rule_key == expected_key
            assert achs[0].achieved_value == float(so_val)


def test_pitcher_hierarchy_suppression():
    evaluator = GameMilestoneEvaluator()

    # 1. Complete Game Win with runs allowed -> GAME_COMPLETE_GAME_WIN only
    rec_cg = GameRecord(
        game_id=200,
        title="Test",
        game_date="05/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        pitching_lines=[PitchingLine(player_id=1, name="P1", team_id=1, outs=27, win=True, r=2, h=5)],
    )
    achs_cg = [
        a
        for a in evaluator.evaluate_game(rec_cg)
        if a.rule_key
        in ("GAME_PERFECT_GAME", "GAME_NO_HIT_NO_RUN", "GAME_SHUTOUT_WIN", "GAME_COMPLETE_GAME_WIN")
    ]
    assert len(achs_cg) == 1
    assert achs_cg[0].rule_key == "GAME_COMPLETE_GAME_WIN"

    # 2. Complete Game Loss -> No CG win achievement
    rec_loss = GameRecord(
        game_id=201,
        title="Test",
        game_date="05/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        pitching_lines=[PitchingLine(player_id=1, name="P1", team_id=1, outs=27, win=False, loss=True, r=1, h=3)],
    )
    achs_loss = [
        a
        for a in evaluator.evaluate_game(rec_loss)
        if a.rule_key
        in ("GAME_PERFECT_GAME", "GAME_NO_HIT_NO_RUN", "GAME_SHUTOUT_WIN", "GAME_COMPLETE_GAME_WIN")
    ]
    assert len(achs_loss) == 0

    # 3. Shutout Win -> GAME_SHUTOUT_WIN only
    rec_so = GameRecord(
        game_id=202,
        title="Test",
        game_date="05/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        pitching_lines=[PitchingLine(player_id=1, name="P1", team_id=1, outs=27, win=True, r=0, h=3)],
    )
    achs_so = [
        a
        for a in evaluator.evaluate_game(rec_so)
        if a.rule_key
        in ("GAME_PERFECT_GAME", "GAME_NO_HIT_NO_RUN", "GAME_SHUTOUT_WIN", "GAME_COMPLETE_GAME_WIN")
    ]
    assert len(achs_so) == 1
    assert achs_so[0].rule_key == "GAME_SHUTOUT_WIN"

    # 4. No-Hit No-Run -> GAME_NO_HIT_NO_RUN only
    rec_nh = GameRecord(
        game_id=203,
        title="Test",
        game_date="05/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        pitching_lines=[PitchingLine(player_id=1, name="P1", team_id=1, outs=27, win=True, r=0, h=0, bb=2)],
    )
    achs_nh = [
        a
        for a in evaluator.evaluate_game(rec_nh)
        if a.rule_key
        in ("GAME_PERFECT_GAME", "GAME_NO_HIT_NO_RUN", "GAME_SHUTOUT_WIN", "GAME_COMPLETE_GAME_WIN")
    ]
    assert len(achs_nh) == 1
    assert achs_nh[0].rule_key == "GAME_NO_HIT_NO_RUN"

    # 5. Perfect Game -> GAME_PERFECT_GAME only
    rec_pg = GameRecord(
        game_id=204,
        title="Test",
        game_date="05/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=1,
        home_team_id=2,
        pitching_lines=[PitchingLine(player_id=1, name="P1", team_id=1, outs=27, win=True, r=0, h=0, bb=0)],
    )
    achs_pg = [
        a
        for a in evaluator.evaluate_game(rec_pg)
        if a.rule_key
        in ("GAME_PERFECT_GAME", "GAME_NO_HIT_NO_RUN", "GAME_SHUTOUT_WIN", "GAME_COMPLETE_GAME_WIN")
    ]
    assert len(achs_pg) == 1
    assert achs_pg[0].rule_key == "GAME_PERFECT_GAME"


def test_team_batting_starter_vs_sub():
    evaluator = GameMilestoneEvaluator()

    # Case 1: Starters all hit, sub is 0-for-1 -> STARTERS_ALL_HIT Yes, APPEARED_ALL_HIT No
    rec1 = GameRecord(
        game_id=300,
        title="Test",
        game_date="05/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=10,
        home_team_id=20,
        batting_lines=[
            BattingLine(player_id=i, name=f"P{i}", team_id=10, ab=3, h=1, is_starter=True) for i in range(1, 10)
        ]
        + [BattingLine(player_id=99, name="Sub", team_id=10, ab=1, h=0, is_starter=False)],
    )
    achs1 = [a.rule_key for a in evaluator.evaluate_game(rec1)]
    assert "TEAM_STARTERS_ALL_HIT" in achs1
    assert "TEAM_APPEARED_ALL_HIT" not in achs1

    # Case 2: All appeared hit -> both Yes
    rec2 = GameRecord(
        game_id=301,
        title="Test",
        game_date="05/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=10,
        home_team_id=20,
        batting_lines=[
            BattingLine(player_id=i, name=f"P{i}", team_id=10, ab=3, h=1, is_starter=True) for i in range(1, 10)
        ]
        + [BattingLine(player_id=99, name="Sub", team_id=10, ab=1, h=1, is_starter=False)],
    )
    achs2 = [a.rule_key for a in evaluator.evaluate_game(rec2)]
    assert "TEAM_STARTERS_ALL_HIT" in achs2
    assert "TEAM_APPEARED_ALL_HIT" in achs2



def test_team_pitching_hierarchy():
    evaluator = GameMilestoneEvaluator()

    # Team Shutout Win (combined pitching, 0 runs, hits allowed)
    rec1 = GameRecord(
        game_id=400,
        title="Test",
        game_date="05/01/2027",
        season=2027,
        competition_type="regular_season",
        away_team_id=10,
        home_team_id=20,
        away_score=0,
        home_score=3,
        pitching_lines=[
            PitchingLine(player_id=1, name="Starter", team_id=20, outs=18, r=0, h=2, bb=1),
            PitchingLine(player_id=2, name="Reliever", team_id=20, outs=9, r=0, h=1, bb=0),
        ],
    )
    achs1 = [
        a.rule_key
        for a in evaluator.evaluate_game(rec1)
        if a.rule_key in ("TEAM_PERFECT_GAME", "TEAM_NO_HIT_NO_RUN", "TEAM_SHUTOUT_WIN")
    ]
    assert len(achs1) == 1
    assert achs1[0] == "TEAM_SHUTOUT_WIN"


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

    repo = Repository(test_db)
    achievements = repo.game_milestone_achievements()
    assert len(achievements) > 0
