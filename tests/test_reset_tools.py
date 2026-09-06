import pytest
from pathlib import Path
from ootp_milestone_tracker.db.database import Database
from ootp_milestone_tracker.db.repository import Repository
from ootp_milestone_tracker.services.reset_service import ResetService
from ootp_milestone_tracker.services.history_service import HistoryService


def test_reset_history_tracking(tmp_path: Path):
    db_path = tmp_path / "test_reset.db"
    db = Database(db_path)
    db.initialize()
    repo = Repository(db)
    history_service = HistoryService(repo)
    reset_service = ResetService(repo)

    # 1. Add automatic and manual history events
    history_service.add_manual_league_title_award(
        player_id=101, season=2027, award_key="HR", stat_value_str="58"
    )

    with db.connect() as conn:
        conn.execute(
            """INSERT INTO player_history_events (
                source_family, source_event_id, source_signature, source_mode,
                event_type, event_subtype, player_id, team_id, season, title, resolution_status,
                created_at, updated_at
            ) VALUES ('MESSAGES', 'msg_1', 'sig1', 'AUTOMATIC_MESSAGE', 'ALL_STAR', 'ALL_STAR_STARTER', 101, 403, 2027, '올스타 선정', 'published', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"""
        )
        conn.execute(
            """INSERT INTO transaction_events (
                source_family, source_event_id, source_signature, event_key, transaction_type, description,
                created_at, updated_at
            ) VALUES ('MESSAGES', 'msg_1', 'sig1', 'k1', 'TRADE', '트레이드', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)"""
        )
        conn.commit()

    # Verify counts before reset
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM player_history_events").fetchone()[0] == 2
        assert conn.execute("SELECT COUNT(*) FROM transaction_events").fetchone()[0] == 1

    # Execute reset_history_tracking (preserve_manual=True)
    counts = reset_service.reset_history_tracking(preserve_manual=True)
    assert counts["player_history_events"] == 1
    assert counts["transaction_events"] == 1

    # Verify manual event is preserved
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM player_history_events").fetchone()[0] == 1
        rem = conn.execute("SELECT source_family FROM player_history_events").fetchone()[0]
        assert rem == "MANUAL_USER"

    # Idempotency test
    counts2 = reset_service.reset_history_tracking(preserve_manual=True)
    assert counts2["player_history_events"] == 0
    assert counts2["transaction_events"] == 0


def test_reset_all_tracking(tmp_path: Path):
    db_path = tmp_path / "test_reset_all.db"
    db = Database(db_path)
    db.initialize()
    repo = Repository(db)
    reset_service = ResetService(repo)

    # Add game ledger and settings data
    repo.set_setting("save_path", "/fake/save.lg")
    with db.connect() as conn:
        conn.execute("UPDATE teams SET is_tracked = 0")
        conn.execute("INSERT OR REPLACE INTO teams (id, name, short_name, is_tracked) VALUES (403, 'Seoul Yukies', 'SEO', 1)")
        conn.execute("INSERT OR REPLACE INTO players (id, team_id, name_en, name_ko, position, age) VALUES (101, 403, 'Bo-kyung Moon', '문보경', '3B', 26)")
        conn.execute("INSERT INTO games (game_id, season, game_date, home_team_id, away_team_id, competition_type) VALUES (1, 2027, '2027-04-01', 403, 14, 'regular_season')")
        conn.commit()

    # Execute reset_all_tracking
    counts = reset_service.reset_all_tracking()
    assert counts["games"] == 1

    # Verify settings, tracked team, and player Korean name mappings are preserved
    assert repo.get_setting("save_path") == "/fake/save.lg"
    tracked = repo.tracked_team()
    assert tracked is not None and tracked["id"] == 403

    p = repo.player(101)
    assert p is not None and p["name_ko"] == "문보경"

    # Idempotency test
    counts2 = reset_service.reset_all_tracking()
    assert counts2["games"] == 0
