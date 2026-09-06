import re
from typing import List, Optional
from ootp_milestone_tracker.importer.message_models import RawMessage
from ootp_milestone_tracker.importer.transaction_models import TransactionEventRecord, TransactionParticipant
from ootp_milestone_tracker.services.transaction_renderer import (
    render_trade_description, render_contract_description, format_usd
)

def parse_transaction_message(msg: RawMessage) -> List[TransactionEventRecord]:
    text = msg.raw_text
    text_lower = text.lower()
    first_line = msg.first_line.strip()
    first_line_lower = first_line.lower()

    # Ignore proposal/rumor/deadline/negotiation messages
    if any(k in first_line_lower or k in text_lower for k in [
        'trade proposal', 'trade deadline', 'talking trade', 'rumors around',
        'seeking trade', 'talks intensifying', 'negotiation', 'review of goals'
    ]):
        if 'trade proposal' in text_lower or 'proposes the following trade' in text_lower or 'rumors around' in text_lower or 'seeking trade' in first_line_lower:
            return []
        if 'trade deadline' in first_line_lower or 'talks intensifying' in first_line_lower or 'negotiation' in first_line_lower:
            return []

    date_str = None
    date_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', text)
    season = None
    if date_match:
        m, d, y = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
        date_str = f"{y:04d}-{m:02d}-{d:02d}"
        season = y
    else:
        year_match = re.search(r'\b(20\d{2})\b', text)
        if year_match:
            season = int(year_match.group(1))

    # 1. CONTRACT EXTENSION
    if 'extension' in first_line_lower or 'extension' in text_lower or 're-sign' in first_line_lower or 're-signed' in text_lower:
        if msg.players and ('extension' in text_lower or 're-sign' in text_lower or 're-signed' in text_lower or 'signed a' in text_lower or 'inked' in text_lower):
            p_name, p_id = msg.players[0]
            t_id = msg.teams[0][1] if msg.teams else None

            years = None
            y_match = re.search(r'(\d+)\s*-\s*years?|\b(\d+)\s*years?', text_lower)
            if y_match:
                years = int(y_match.group(1) or y_match.group(2))

            total_val = None
            v_match = re.search(r'\$([0-9,]+)', text)
            if v_match:
                total_val = int(v_match.group(1).replace(',', ''))

            # Check explicit option years
            opt_years = None
            opt_explicit = False
            opt_match = re.search(r'(\d+)\+(\d+)\s*years?', text_lower)
            if opt_match:
                years = int(opt_match.group(1))
                opt_years = int(opt_match.group(2))
                opt_explicit = True

            desc = render_contract_description(
                'CONTRACT_EXTENSION',
                years=years,
                total_value=total_val,
                option_years=opt_years,
                option_explicit=opt_explicit
            )
            participant = TransactionParticipant(
                participant_kind='PLAYER',
                display_text=p_name,
                player_id=p_id,
                from_team_id=t_id,
                to_team_id=t_id,
                role='EXTENDED',
                sequence=1
            )
            rec = TransactionEventRecord(
                source_family='MESSAGES',
                source_event_id=f"msg_{msg.msg_id}",
                source_signature=msg.signature,
                event_key=f"msg_{msg.msg_id}_ext",
                transaction_type='CONTRACT_EXTENSION',
                description=desc,
                event_date=date_str,
                season=season,
                source_ref=msg.filepath,
                participants=[participant]
            )
            return [rec]

    # 2. FA SIGNING
    if any(k in first_line_lower or k in text_lower for k in ['contract signed', 'inks deal', 'signs contract', 'signed a free agent', 'agrees to terms', 'signed a contract', 'signs with']):
        if msg.players:
            p_name, p_id = msg.players[0]
            t_id = msg.teams[0][1] if msg.teams else None

            years = None
            y_match = re.search(r'(\d+)\s*-\s*years?|\b(\d+)\s*years?', text_lower)
            if y_match:
                years = int(y_match.group(1) or y_match.group(2))

            total_val = None
            v_match = re.search(r'\$([0-9,]+)', text)
            if v_match:
                total_val = int(v_match.group(1).replace(',', ''))

            desc = render_contract_description('FA_SIGNING', years=years, total_value=total_val)
            participant = TransactionParticipant(
                participant_kind='PLAYER',
                display_text=p_name,
                player_id=p_id,
                from_team_id=None,
                to_team_id=t_id,
                role='SIGNED',
                sequence=1
            )
            rec = TransactionEventRecord(
                source_family='MESSAGES',
                source_event_id=f"msg_{msg.msg_id}",
                source_signature=msg.signature,
                event_key=f"msg_{msg.msg_id}_fa",
                transaction_type='FA_SIGNING',
                description=desc,
                event_date=date_str,
                season=season,
                source_ref=msg.filepath,
                participants=[participant]
            )
            return [rec]

    # 3. TRADE
    if ('trade' in text_lower or 'traded' in text_lower or 'swapped' in text_lower or 'acquired' in text_lower or 'sent' in text_lower) and ('to the' in text_lower or 'for' in text_lower or 'in exchange for' in text_lower or 'in return' in text_lower or 'agree to a swap' in text_lower or 'confirm trade' in first_line_lower or 'execute trade' in first_line_lower or 'swap players' in first_line_lower or 'trade players' in first_line_lower or 'deal:' in first_line_lower):
        if not msg.players:
            return []

        team_ids = [t_id for _, t_id in msg.teams]
        unique_teams = []
        for tid in team_ids:
            if tid not in unique_teams:
                unique_teams.append(tid)

        if len(unique_teams) < 2:
            raw_teams = [int(m) for m in re.findall(r'<[^:>]+:team#(\d+)>', text)]
            for tid in raw_teams:
                if tid not in unique_teams:
                    unique_teams.append(tid)

        if len(unique_teams) >= 2:
            team_a_id, team_b_id = unique_teams[0], unique_teams[1]
        else:
            team_a_id, team_b_id = None, None

        player_matches = re.findall(r'<([^:>]+):player#(\d+)>', text)
        seen_players = set()
        player_list = []
        for p_name, p_id_str in player_matches:
            p_id = int(p_id_str)
            if p_id not in seen_players:
                seen_players.add(p_id)
                player_list.append((p_name, p_id))

        if not player_list:
            return []

        side_a_players = []
        side_b_players = []

        pivot_match = re.search(r'\b(for|in exchange for|in return|receiving|getting)\b', text, re.IGNORECASE)
        if pivot_match:
            pivot_pos = pivot_match.start()
            for p_name, p_id in player_list:
                p_tag = f":player#{p_id}>"
                p_pos = text.find(p_tag)
                if p_pos != -1 and p_pos < pivot_pos:
                    side_a_players.append((p_name, p_id))
                else:
                    side_b_players.append((p_name, p_id))
        else:
            side_a_players = player_list[:1]
            side_b_players = player_list[1:]

        if not side_a_players or not side_b_players:
            half = max(1, len(player_list) // 2)
            side_a_players = player_list[:half]
            side_b_players = player_list[half:]

        participants = []
        seq = 1
        side_a_participants = []
        side_b_participants = []

        for p_name, p_id in side_a_players:
            p = TransactionParticipant(
                participant_kind='PLAYER',
                display_text=p_name,
                player_id=p_id,
                from_team_id=team_a_id,
                to_team_id=team_b_id,
                role='TRADED',
                sequence=seq
            )
            side_a_participants.append(p)
            participants.append(p)
            seq += 1

        cash_match = re.search(r'\$([0-9,]+)\s*(?:in\s+cash|cash)', text, re.IGNORECASE)
        if cash_match:
            cash_amt = int(cash_match.group(1).replace(',', ''))
            cash_p = TransactionParticipant(
                participant_kind='CASH',
                display_text=f"현금 {format_usd(cash_amt)}",
                player_id=None,
                from_team_id=team_a_id,
                to_team_id=team_b_id,
                cash_amount=cash_amt,
                role='CASH',
                sequence=seq
            )
            if pivot_match and cash_match.start() < pivot_match.start():
                side_a_participants.append(cash_p)
            else:
                side_b_participants.append(cash_p)
            participants.append(cash_p)
            seq += 1

        for p_name, p_id in side_b_players:
            p = TransactionParticipant(
                participant_kind='PLAYER',
                display_text=p_name,
                player_id=p_id,
                from_team_id=team_b_id,
                to_team_id=team_a_id,
                role='TRADED',
                sequence=seq
            )
            side_b_participants.append(p)
            participants.append(p)
            seq += 1

        try:
            desc = render_trade_description(side_a_participants, side_b_participants)
        except ValueError:
            return []

        rec = TransactionEventRecord(
            source_family='MESSAGES',
            source_event_id=f"msg_{msg.msg_id}",
            source_signature=msg.signature,
            event_key=f"msg_{msg.msg_id}_trade",
            transaction_type='TRADE',
            description=desc,
            event_date=date_str,
            season=season,
            source_ref=msg.filepath,
            participants=participants
        )
        return [rec]

    return []
