import pytest
from ootp_milestone_tracker.importer.message_models import RawMessage
from ootp_milestone_tracker.importer.career_event_parser import parse_career_event_message


def test_parse_mlb_debut():
    raw_text = "Carson Williams of the Rays had a good year. In his Major League debut season..."
    msg = RawMessage.create(
        msg_id=2001, filename="message2001.txt", filepath="/fake/2001.txt",
        raw_text=raw_text, players=[("Carson Williams", 52670)], teams=[("Rays", 27)]
    )
    events = parse_career_event_message(msg)
    assert len(events) == 1
    assert events[0].event_type == "MLB_DEBUT"
    assert events[0].title == "MLB 데뷔"


def test_parse_draft():
    raw_text = "Khal Stephen was drafted in the 1st round (3rd overall pick) by New York."
    msg = RawMessage.create(
        msg_id=2002, filename="message2002.txt", filepath="/fake/2002.txt",
        raw_text=raw_text, players=[("Khal Stephen", 52877)], teams=[("New York", 18)]
    )
    events = parse_career_event_message(msg)
    assert len(events) == 1
    assert events[0].event_type == "DRAFT"
    assert events[0].title == "신인 드래프트 1라운드 3순위 지명"


def test_parse_retirement():
    raw_text = "Tim Hill announced his retirement today at a press conference, saying it would be his last season."
    msg = RawMessage.create(
        msg_id=2003, filename="message2003.txt", filepath="/fake/2003.txt",
        raw_text=raw_text, players=[("Tim Hill", 23960)], teams=[("New York", 18)]
    )
    events = parse_career_event_message(msg)
    assert len(events) == 1
    assert events[0].event_type == "RETIREMENT"
    assert events[0].title == "현역 은퇴"


def test_parse_hall_of_fame():
    raw_text = "Ichiro Suzuki was elected to the Hall of Fame today, receiving 92.4% of the vote."
    msg = RawMessage.create(
        msg_id=2004, filename="message2004.txt", filepath="/fake/2004.txt",
        raw_text=raw_text, players=[("Ichiro Suzuki", 1111)], teams=[]
    )
    events = parse_career_event_message(msg)
    assert len(events) == 1
    assert events[0].event_type == "HALL_OF_FAME"
    assert events[0].title == "92.4% 득표로 명예의 전당 헌액"


def test_parse_roster_move():
    raw_text = "The Mariners announced that player <Jonny Farmelo:player#52029> was recalled from AAA Tacoma."
    msg = RawMessage.create(
        msg_id=2005, filename="message2005.txt", filepath="/fake/2005.txt",
        raw_text=raw_text, players=[("Jonny Farmelo", 52029)], teams=[]
    )
    events = parse_career_event_message(msg)
    assert len(events) == 1
    assert events[0].event_type == "ROSTER_MOVE"
    assert events[0].title == "MLB 콜업"


def test_parse_secondary_transactions():
    # Waiver
    msg_w = RawMessage.create(
        msg_id=2006, filename="message2006.txt", filepath="/fake/2006.txt",
        raw_text="<Donovan Walton:player#21923> was claimed off waivers by the <Los Angeles Dodgers:team#15>.",
        players=[("Donovan Walton", 21923)], teams=[("Los Angeles Dodgers", 15)]
    )
    events_w = parse_career_event_message(msg_w)
    assert len(events_w) == 1
    assert events_w[0].event_subtype == "WAIVER_CLAIM"

    # Release
    msg_r = RawMessage.create(
        msg_id=2007, filename="message2007.txt", filepath="/fake/2007.txt",
        raw_text="The <New York Yankees:team#18> announced that <Tim Hill:player#23960> was released from his contract.",
        players=[("Tim Hill", 23960)], teams=[("New York Yankees", 18)]
    )
    events_r = parse_career_event_message(msg_r)
    assert len(events_r) == 1
    assert events_r[0].event_subtype == "RELEASE"

    # DFA
    msg_d = RawMessage.create(
        msg_id=2008, filename="message2008.txt", filepath="/fake/2008.txt",
        raw_text="<Tyler Bell:player#55202> has been designated for assignment by the club.",
        players=[("Tyler Bell", 55202)], teams=[]
    )
    events_d = parse_career_event_message(msg_d)
    assert len(events_d) == 1
    assert events_d[0].event_subtype == "DFA"
