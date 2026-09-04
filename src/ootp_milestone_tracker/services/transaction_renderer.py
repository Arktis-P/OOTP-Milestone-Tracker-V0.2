from typing import Iterable, Optional

from ootp_milestone_tracker.importer.transaction_models import TransactionParticipant


def format_usd(amount: Optional[int]) -> Optional[str]:
    if amount is None:
        return None
    return f"${amount:,.0f}"


def render_transaction_asset(asset: TransactionParticipant) -> str:
    kind = asset.participant_kind.upper()
    if kind == "CASH":
        money = format_usd(asset.cash_amount)
        return f"현금 {money}" if money else "현금"
    return asset.display_text.strip()


def _render_side(assets: Iterable[TransactionParticipant]) -> str:
    ordered = sorted(assets, key=lambda a: a.sequence)
    return " & ".join(filter(None, (render_transaction_asset(asset) for asset in ordered)))


def render_trade_description(
    side_a: Iterable[TransactionParticipant],
    side_b: Iterable[TransactionParticipant],
) -> str:
    left = _render_side(side_a)
    right = _render_side(side_b)
    if not left or not right:
        raise ValueError("A trade description requires assets on both sides")
    return f"{left} <> {right} 트레이드"


def render_contract_description(
    transaction_type: str,
    years: Optional[int] = None,
    total_value: Optional[int] = None,
    option_years: Optional[int] = None,
    option_explicit: bool = False,
) -> str:
    transaction_type = transaction_type.upper()
    if transaction_type == "FA_SIGNING":
        suffix = "FA 계약 체결"
    elif transaction_type == "CONTRACT_EXTENSION":
        suffix = "연장 계약 체결"
    else:
        raise ValueError(f"Unsupported contract transaction type: {transaction_type}")

    parts = []
    if years is not None:
        if option_explicit and option_years:
            parts.append(f"{years}+{option_years}년")
        else:
            parts.append(f"{years}년")
    money = format_usd(total_value)
    if money:
        parts.append(money)
    parts.append(suffix)
    return " ".join(parts)
