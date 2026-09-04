import sqlite3
from pathlib import Path
import pytest

from ootp_milestone_tracker.db.database import Database
from ootp_milestone_tracker.db.repository import Repository
from ootp_milestone_tracker.importer.message_models import RawMessage
from ootp_milestone_tracker.importer.message_parser import (
    parse_injury_message, parse_allstar_message, parse_award_message, parse_monthly_award_message
)
from ootp_milestone_tracker.services.history_service import HistoryService


@pytest.fixture
def memory_repo(tmp_path):
    db_path = tmp_path / "test_history.db"
    db = Database(db_path)
    db.initialize()
    repo = Repository(db)

    
    # Seed a sample player and team
    with db.connect() as conn:
        conn.execute("INSERT INTO teams (id, name, short_name, is_tracked) VALUES (403, 'Seoul Yukies', 'SY', 1)")
        conn.execute("INSERT INTO teams (id, name, short_name, is_tracked) VALUES (18, 'New York Yankees', 'NYY', 0)")
        conn.execute("INSERT INTO players (id, team_id, name_en, name_ko, position, age, active) VALUES (45705, 403, 'Bo-kyung Moon', '문보경', '3B', 26, 1)")
        conn.execute("INSERT INTO players (id, team_id, name_en, name_ko, position, age, active) VALUES (33561, 18, 'Aaron Judge', '애런 저지', 'RF', 34, 1)")
        conn.commit()
        
    return repo


def test_injury_parser_single_duration_and_side():
    raw_text = """Injury Update for LG, Lee
The latest news from the clubhouse is this: reliever <Bo-kyung Moon:player#45705> is expected to be out of action for 4 weeks. He has a left hamstring strain, sustained on 03/16/2026."""
    msg = RawMessage.create(1, "message1.txt", "path/message1.txt", raw_text, [("Bo-kyung Moon", 45705)], [(403, "Seoul Yukies")])
    
    events = parse_injury_message(msg)
    assert len(events) == 1
    ev = events[0]
    assert ev.player_id == 45705
    assert ev.resolution_status == "published"
    assert "왼쪽 햄스트링 부상으로 4주 진단." in ev.title
    assert ev.event_date == "2026-03-16"


def test_injury_parser_range_duration_no_side():
    raw_text = """Lotte's Rodriguez Diagnosis Revealed
Team officials for Lotte have revealed that the recent injury to <Bo-kyung Moon:player#45705> will keep him out for 2-3 months. The starting pitcher suffered a torn rotator cuff on 03/28/2026."""
    msg = RawMessage.create(2, "message2.txt", "path/message2.txt", raw_text, [("Bo-kyung Moon", 45705)], [])
    
    events = parse_injury_message(msg)
    assert len(events) == 1
    ev = events[0]
    assert ev.resolution_status == "published"
    assert "회전근개 부상으로 2~3개월 진단." in ev.title


def test_allstar_parser_starter_and_reserve():
    raw_text = """Breaking MLB News: The All-Star Game Rosters Have Been Announced
It's time once again for the Major League Baseball All-Star game!

This year's American League standouts are:
SP <Aaron Judge:player#33561> (NYY)* - 9-2, 3.03 ERA
3B <Bo-kyung Moon:player#45705> (SY) - .374/.480/.831"""

    msg = RawMessage.create(7760, "message7760.txt", "path/message7760.txt", raw_text, [("Aaron Judge", 33561), ("Bo-kyung Moon", 45705)], [])
    
    events = parse_allstar_message(msg)
    assert len(events) == 2
    
    starter_ev = next(e for e in events if e.player_id == 33561)
    assert starter_ev.event_subtype == "ALL_STAR_STARTER"
    assert "팬 투표 1위로 AL 선발투수 올스타 선정" in starter_ev.title
    
    reserve_ev = next(e for e in events if e.player_id == 45705)
    assert reserve_ev.event_subtype == "ALL_STAR_RESERVE"
    assert "감독 추천으로 올스타 출전" in reserve_ev.title


def test_allstar_parser_excludes_minor_and_voting_updates():
    # Minor league All-Star game
    minor_text = """EL News Flash: The All-Star Game Rosters Have Been Announced
SP <Anthony Eyanson:player#52123> (POR) - 4-1, 4.12 ERA"""
    minor_msg = RawMessage.create(1829, "message1829.txt", "path/message1829.txt", minor_text, [], [])
    assert len(parse_allstar_message(minor_msg)) == 0

    # Voting update message
    update_text = """American League All-Star Fan Voting Update
Below are the current standings for the American League All-Star Fan voting (as of Mon. May 18th , 2026)"""
    update_msg = RawMessage.create(1084, "message1084.txt", "path/message1084.txt", update_text, [], [])
    assert len(parse_allstar_message(update_msg)) == 0


def test_award_parser_mvp_unanimous():
    raw_text = """Moon Wins WBC 2026 Most Valuable Player
<Bo-kyung Moon:player#45705> took National League by storm.
He received 32 first place votes out of a possible 32, as a unanimous winner."""
    msg = RawMessage.create(300, "message300.txt", "path/message300.txt", raw_text, [("Bo-kyung Moon", 45705)], [])
    
    events = parse_award_message(msg)
    assert len(events) == 1
    ev = events[0]
    assert ev.event_subtype == "MVP"
    assert "32표 만장일치로 NL MVP 수상" in ev.title


def test_monthly_award_parser():
    raw_text = """Frias Voted June's Top Rookie
<Bo-kyung Moon:player#45705> collected 17 hits to snare the Rookie of the Month for June."""
    msg = RawMessage.create(2189, "message2189.txt", "path/message2189.txt", raw_text, [("Bo-kyung Moon", 45705)], [])
    
    events = parse_monthly_award_message(msg)
    assert len(events) == 1
    ev = events[0]
    assert ev.event_subtype == "MONTHLY_ROOKIE"
    assert "이달의 신인 (6월) 선정" in ev.title


def test_manual_award_creation_and_idempotency(memory_repo):
    service = HistoryService(memory_repo)
    
    # 1. Insert manual league title award
    ok = service.add_manual_league_title_award(
        player_id=45705,
        season=2026,
        award_key="AVG",
        stat_value_str=".369",
        league_label="NL"
    )
    assert ok is True
    
    # Query history events
    evs = service.get_history_events()
    assert len(evs) == 1
    assert "시즌 타율 .369로 NL 타격왕 수상" in evs[0]["title"]
    assert evs[0]["source_mode"] == "MANUAL_USER"
    
    # 2. Duplicate insert should not create duplicate rows
    service.add_manual_league_title_award(
        player_id=45705,
        season=2026,
        award_key="AVG",
        stat_value_str=".369",
        league_label="NL"
    )
    evs_after = service.get_history_events()
    assert len(evs_after) == 1
