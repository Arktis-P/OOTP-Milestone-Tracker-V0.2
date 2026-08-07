"""
Unit tests for OOTP Data Parsers (Phase 2.1, 2.2, 2.3)
Tests stats TXT parser and boxscore HTML parser with real sample fixtures.
"""

import os
import pytest
from core.parser.stats_txt_parser import StatsTxtParser
from core.parser.boxscore_parser import BoxscoreParser

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_parse_batting_stats_sample():
    file_path = os.path.join(FIXTURES_DIR, "player_batting_stats_sample.txt")
    if not os.path.exists(file_path):
        pytest.skip("Sample batting stats fixture missing.")

    records = StatsTxtParser.parse_batting_stats(file_path, filter_split_id=1)
    assert len(records) > 0

    first = records[0]
    assert first.ootp_player_id > 0
    assert isinstance(first.first_name, str)
    assert isinstance(first.last_name, str)
    assert first.ab >= 0
    assert first.avg >= 0.0


def test_parse_pitching_stats_sample():
    file_path = os.path.join(FIXTURES_DIR, "player_pitching_stats_sample.txt")
    if not os.path.exists(file_path):
        pytest.skip("Sample pitching stats fixture missing.")

    records = StatsTxtParser.parse_pitching_stats(file_path, filter_split_id=1)
    assert len(records) > 0

    first = records[0]
    assert first.ootp_player_id > 0
    assert isinstance(first.first_name, str)
    assert first.ip_outs >= 0
    assert first.era >= 0.0


def test_parse_boxscore_sample():
    file_path = os.path.join(FIXTURES_DIR, "game_box_1.html")
    if not os.path.exists(file_path):
        pytest.skip("Sample boxscore HTML fixture missing.")

    box = BoxscoreParser.parse_file(file_path)
    assert box.ootp_game_id == 1
    assert box.season == 2027
    assert box.game_date == "2027-03-30"
    assert len(box.batting_lines) > 0
    assert len(box.pitching_lines) > 0

    # Verify player IDs extracted
    b_player = box.batting_lines[0]
    assert b_player.ootp_player_id > 0
    assert b_player.ab > 0

    p_player = box.pitching_lines[0]
    assert p_player.ootp_player_id > 0
    assert p_player.ip_outs > 0


def test_parse_special_events_synthetic():
    html_content = """
    <html>
    <head><title>MLB Box Score, Red Sox at Yankees, 07/04/2026</title></head>
    <body>
    GAME ID: 999 - SATURDAY, JULY 4TH , 2026 -
    <table>
    <tr><td>BATTING LINESCORE</td></tr>
    <tr><td><a href="../players/player_101.html">Super Star</a></td><td>4</td><td>2</td><td>4</td><td>4</td><td>0</td><td>0</td></tr>
    </table>
    <div>Super Star hit for the cycle! Also hit a grand slam!</div>
    </body>
    </html>
    """
    box = BoxscoreParser.parse_html(html_content)
    assert box.ootp_game_id == 999
    assert box.season == 2026
    assert box.game_date == "2026-07-04"
    assert len(box.batting_lines) == 1

    event_types = {e.event_type for e in box.special_events}
    assert "cycle" in event_types
    assert "grand_slam" in event_types
