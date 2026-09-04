import pytest

from ootp_milestone_tracker.importer.transaction_models import TransactionParticipant
from ootp_milestone_tracker.services.transaction_renderer import (
    render_contract_description,
    render_trade_description,
)


def test_trade_description_with_cash():
    left = [
        TransactionParticipant("PLAYER", "애런 저지", player_id=1, sequence=0),
        TransactionParticipant("PLAYER", "게릿 콜", player_id=2, sequence=1),
    ]
    right = [
        TransactionParticipant("PLAYER", "오타니 쇼헤이", player_id=3, sequence=0),
        TransactionParticipant("CASH", "cash", cash_amount=10_000_000, sequence=1),
    ]
    assert render_trade_description(left, right) == (
        "애런 저지 & 게릿 콜 <> 오타니 쇼헤이 & 현금 $10,000,000 트레이드"
    )


def test_trade_cash_without_amount_does_not_invent_value():
    left = [TransactionParticipant("PLAYER", "선수 A")]
    right = [TransactionParticipant("CASH", "cash")]
    assert render_trade_description(left, right) == "선수 A <> 현금 트레이드"


def test_fa_contract_description():
    assert render_contract_description("FA_SIGNING", years=12, total_value=333_333_000) == (
        "12년 $333,333,000 FA 계약 체결"
    )


def test_extension_description():
    assert render_contract_description("CONTRACT_EXTENSION", years=4, total_value=3_600_000) == (
        "4년 $3,600,000 연장 계약 체결"
    )


def test_contract_option_is_not_inferred():
    assert render_contract_description(
        "FA_SIGNING", years=12, total_value=333_333_000, option_years=2, option_explicit=False
    ).startswith("12년 ")


def test_explicit_contract_option_is_rendered():
    assert render_contract_description(
        "FA_SIGNING", years=10, total_value=333_333_000, option_years=2, option_explicit=True
    ).startswith("10+2년 ")


def test_trade_requires_two_sides():
    with pytest.raises(ValueError):
        render_trade_description([TransactionParticipant("PLAYER", "선수 A")], [])
