import pytest
from pathlib import Path
from ootp_milestone_tracker.db.database import Database
from ootp_milestone_tracker.db.repository import Repository
from ootp_milestone_tracker.importer.message_models import RawMessage
from ootp_milestone_tracker.importer.transaction_models import TransactionEventRecord, TransactionParticipant
from ootp_milestone_tracker.importer.transaction_parser import parse_transaction_message
from ootp_milestone_tracker.services.transaction_renderer import (
    render_trade_description, render_contract_description, render_transaction_asset
)
from ootp_milestone_tracker.services.transaction_service import TransactionService


def test_renderer_assets():
    # 1. Player asset
    p = TransactionParticipant(participant_kind="PLAYER", display_text="애런 저지")
    assert render_transaction_asset(p) == "애런 저지"

    # 2. Cash with amount
    c1 = TransactionParticipant(participant_kind="CASH", display_text="", cash_amount=10000000)
    assert render_transaction_asset(c1) == "현금 $10,000,000"

    # 3. Cash without amount
    c2 = TransactionParticipant(participant_kind="CASH", display_text="", cash_amount=None)
    assert render_transaction_asset(c2) == "현금"


def test_renderer_trade_description():
    # Two-player vs player + cash trade string
    side_a = [
        TransactionParticipant(participant_kind="PLAYER", display_text="애런 저지", sequence=1),
        TransactionParticipant(participant_kind="PLAYER", display_text="게릿 콜", sequence=2),
    ]
    side_b = [
        TransactionParticipant(participant_kind="PLAYER", display_text="오타니 쇼헤이", sequence=1),
        TransactionParticipant(participant_kind="CASH", display_text="", cash_amount=10000000, sequence=2),
    ]
    desc = render_trade_description(side_a, side_b)
    assert desc == "애런 저지 & 게릿 콜 <> 오타니 쇼헤이 & 현금 $10,000,000 트레이드"


def test_renderer_contract_description():
    # FA years + value
    assert render_contract_description("FA_SIGNING", years=12, total_value=333333000) == "12년 $333,333,000 FA 계약 체결"
    assert render_contract_description("FA_SIGNING", years=12, total_value=None) == "12년 FA 계약 체결"
    assert render_contract_description("FA_SIGNING", years=None, total_value=None) == "FA 계약 체결"

    # Extension years + value
    assert render_contract_description("CONTRACT_EXTENSION", years=4, total_value=3600000) == "4년 $3,600,000 연장 계약 체결"

    # Option omitted by default vs explicit option
    assert render_contract_description("CONTRACT_EXTENSION", years=10, option_years=2, option_explicit=False) == "10년 연장 계약 체결"
    assert render_contract_description("CONTRACT_EXTENSION", years=10, option_years=2, option_explicit=True) == "10+2년 연장 계약 체결"


def test_parser_trade_fixture():
    raw_text = (
        "San Diego, Los Angeles Execute Trade\n"
        "The <San Diego Padres:team#23> swapped 18-year old <Ariel Dilone:player#140146> "
        "and 17-year old <Jeferson Ogando:player#141020> to the <Los Angeles Angels:team#14> "
        "for 32-year old <Donovan Walton:player#21923> in return."
    )
    msg = RawMessage.create(
        msg_id=1001,
        filename="message1001.txt",
        filepath="/fake/message1001.txt",
        raw_text=raw_text,
        players=[("Ariel Dilone", 140146), ("Jeferson Ogando", 141020), ("Donovan Walton", 21923)],
        teams=[("San Diego Padres", 23), ("Los Angeles Angels", 14)],
    )
    events = parse_transaction_message(msg)
    assert len(events) == 1
    ev = events[0]
    assert ev.transaction_type == "TRADE"
    assert "Ariel Dilone & Jeferson Ogando <> Donovan Walton 트레이드" in ev.description
    assert len(ev.participants) == 3


def test_parser_trade_with_cash_fixture():
    raw_text = (
        "Twins, Angels Trade Players\n"
        "The <Minnesota Twins:team#17> have sent 33-year old <Victor Caratini:player#33893> "
        "and $2,590,000 in cash to the <Los Angeles Angels:team#14> in exchange for "
        "17-year old <Jeyson Horton:player#137429>."
    )
    msg = RawMessage.create(
        msg_id=1002,
        filename="message1002.txt",
        filepath="/fake/message1002.txt",
        raw_text=raw_text,
        players=[("Victor Caratini", 33893), ("Jeyson Horton", 137429)],
        teams=[("Minnesota Twins", 17), ("Los Angeles Angels", 14)],
    )
    events = parse_transaction_message(msg)
    assert len(events) == 1
    ev = events[0]
    assert ev.transaction_type == "TRADE"
    assert "Victor Caratini & 현금 $2,590,000 <> Jeyson Horton 트레이드" in ev.description


def test_parser_fa_signing_fixture():
    raw_text = (
        "SP Jack Labosky: Contract Signed\n"
        "Thank you for letting me play! <Jack Labosky:player#19905> has signed a 3-year "
        "contract for $15,000,000 with the <Seoul Yukies:team#403>."
    )
    msg = RawMessage.create(
        msg_id=1003,
        filename="message1003.txt",
        filepath="/fake/message1003.txt",
        raw_text=raw_text,
        players=[("Jack Labosky", 19905)],
        teams=[("Seoul Yukies", 403)],
    )
    events = parse_transaction_message(msg)
    assert len(events) == 1
    ev = events[0]
    assert ev.transaction_type == "FA_SIGNING"
    assert ev.description == "3년 $15,000,000 FA 계약 체결"


def test_parser_extension_fixture():
    raw_text = (
        "Seoul, Moon Agree on 15-Year Extension\n"
        "<Bo-kyung Moon:player#45705> of <Seoul:team#403> signed a 15-year extension "
        "at $25,000,000."
    )
    msg = RawMessage.create(
        msg_id=1004,
        filename="message1004.txt",
        filepath="/fake/message1004.txt",
        raw_text=raw_text,
        players=[("Bo-kyung Moon", 45705)],
        teams=[("Seoul", 403)],
    )
    events = parse_transaction_message(msg)
    assert len(events) == 1
    ev = events[0]
    assert ev.transaction_type == "CONTRACT_EXTENSION"
    assert ev.description == "15년 $25,000,000 연장 계약 체결"


def test_parser_non_transaction_fixture():
    raw_text = "The weather was great today during practice."
    msg = RawMessage.create(
        msg_id=1005,
        filename="message1005.txt",
        filepath="/fake/message1005.txt",
        raw_text=raw_text,
        players=[],
        teams=[],
    )
    events = parse_transaction_message(msg)
    assert events == []


def test_persistence_fanout_and_idempotency(tmp_path: Path):
    db_path = tmp_path / "test_txn.db"
    db = Database(db_path)
    db.initialize()
    repo = Repository(db)
    service = TransactionService(repo)

    # Set up tracked team 403
    with db.connect() as conn:
        conn.execute("INSERT OR REPLACE INTO teams (id, name, short_name, is_tracked) VALUES (403, 'Seoul Yukies', 'SEO', 1)")
        conn.execute("INSERT OR REPLACE INTO teams (id, name, short_name, is_tracked) VALUES (14, 'LA Angels', 'LAA', 0)")
        conn.execute("INSERT OR REPLACE INTO players (id, team_id, name_en, name_ko, position, age) VALUES (140146, 403, 'Ariel Dilone', '아리엘 디로네', 'P', 18)")
        conn.execute("INSERT OR REPLACE INTO players (id, team_id, name_en, name_ko, position, age) VALUES (21923, 14, 'Donovan Walton', '도노반 월튼', '2B', 32)")

    # Create 1 trade event record with 2 players
    event = TransactionEventRecord(
        source_family="MESSAGES",
        source_event_id="msg_9999",
        source_signature="sig_9999",
        event_key="msg_9999_trade",
        transaction_type="TRADE",
        description="Ariel Dilone <> Donovan Walton 트레이드",
        event_date="2027-05-15",
        season=2027,
        participants=[
            TransactionParticipant(participant_kind="PLAYER", display_text="Ariel Dilone", player_id=140146, from_team_id=403, to_team_id=14, sequence=1),
            TransactionParticipant(participant_kind="PLAYER", display_text="Donovan Walton", player_id=21923, from_team_id=14, to_team_id=403, sequence=2),
        ]
    )

    # 1. Replace transactions
    persisted = service.replace_source_transactions("MESSAGES", "msg_9999", "sig_9999", [event])
    assert persisted == 1

    # Check 1 transaction event record
    with db.connect() as conn:
        tx_count = conn.execute("SELECT COUNT(*) FROM transaction_events WHERE source_event_id = 'msg_9999'").fetchone()[0]
        part_count = conn.execute("SELECT COUNT(*) FROM transaction_participants").fetchone()[0]
        history_count = conn.execute("SELECT COUNT(*) FROM player_history_events WHERE source_event_id = 'msg_9999'").fetchone()[0]
        assert tx_count == 1
        assert part_count == 2
        assert history_count == 2

    # Check identical description string on both player history rows
    h_events = repo.history_events(tracked_only=False, search="")
    tx_h = [h for h in h_events if h["event_type"] == "TRANSACTION"]
    assert len(tx_h) == 2
    assert tx_h[0]["title"] == "Ariel Dilone <> Donovan Walton 트레이드"
    assert tx_h[1]["title"] == "Ariel Dilone <> Donovan Walton 트레이드"

    # Check tracked_only filter (both leaving team 403 and coming to team 403 are visible)
    tracked_h = repo.history_events(tracked_only=True, search="")
    tracked_tx = [h for h in tracked_h if h["event_type"] == "TRANSACTION"]
    assert len(tracked_tx) == 2

    # 2. Idempotency test (repeat same replace call)
    persisted_again = service.replace_source_transactions("MESSAGES", "msg_9999", "sig_9999", [event])
    assert persisted_again == 1
    with db.connect() as conn:
        assert conn.execute("SELECT COUNT(*) FROM transaction_events").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM player_history_events WHERE event_type = 'TRANSACTION'").fetchone()[0] == 2

