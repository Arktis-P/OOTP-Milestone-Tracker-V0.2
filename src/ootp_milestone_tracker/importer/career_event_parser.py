import re
from typing import List, Optional
from ootp_milestone_tracker.importer.message_models import RawMessage, PlayerHistoryEventRecord
from ootp_milestone_tracker.importer.message_parser import extract_date_and_season

def parse_career_event_message(msg: RawMessage) -> List[PlayerHistoryEventRecord]:
    text = msg.raw_text
    text_lower = text.lower()
    first_line = msg.first_line.strip()
    first_line_lower = first_line.lower()

    if not msg.players:
        return []

    event_date, season = extract_date_and_season(msg)
    main_player_name, main_player_id = msg.players[0]
    main_team_id = msg.teams[0][1] if msg.teams else None

    events = []

    # 1. HALL OF FAME
    if 'hall of fame' in text_lower or 'inducted into' in text_lower:
        if 'elected' in text_lower or 'inducted' in text_lower or 'enshrined' in text_lower:
            pct_match = re.search(r'(\d+\.?\d*)\%\s*(?:of\s*the\s*vote|vote)', text_lower)
            if pct_match:
                pct_str = pct_match.group(1)
                desc = f"{pct_str}% 득표로 명예의 전당 헌액"
            else:
                desc = "명예의 전당 헌액"

            rec = PlayerHistoryEventRecord(
                id=None, source_family="MESSAGES", source_event_id=f"msg_{msg.msg_id}",
                source_signature=msg.signature, source_mode="AUTOMATIC_MESSAGE",
                event_type="HALL_OF_FAME", event_subtype="HOF_INDUCTION",
                player_id=main_player_id, team_id=main_team_id, league_id=None, league_label=None,
                season=season, event_date=event_date, position_label=None,
                title=desc, context_text=msg.first_line, structured_context_json=None,
                resolution_status="published", source_ref=msg.filepath
            )
            return [rec]

    # 2. RETIREMENT
    if 'retire' in text_lower or 'retires' in text_lower or 'retired' in text_lower or 'retiring' in text_lower:
        if any(k in text_lower for k in ['announced his retirement', 'decided to retire', 'leaving baseball', 'hang up his spikes', 'will retire']):
            desc = "현역 은퇴"
            rec = PlayerHistoryEventRecord(
                id=None, source_family="MESSAGES", source_event_id=f"msg_{msg.msg_id}",
                source_signature=msg.signature, source_mode="AUTOMATIC_MESSAGE",
                event_type="RETIREMENT", event_subtype="RETIREMENT",
                player_id=main_player_id, team_id=main_team_id, league_id=None, league_label=None,
                season=season, event_date=event_date, position_label=None,
                title=desc, context_text=msg.first_line, structured_context_json=None,
                resolution_status="published", source_ref=msg.filepath
            )
            return [rec]

    # 3. MLB DEBUT
    if 'debut' in text_lower and ('major league' in text_lower or 'mlb' in text_lower or 'big league' in text_lower):
        if 'made his' in text_lower or 'debut season' in text_lower or 'in his debut' in text_lower or 'first appearance' in text_lower:
            desc = "MLB 데뷔"
            rec = PlayerHistoryEventRecord(
                id=None, source_family="MESSAGES", source_event_id=f"msg_{msg.msg_id}",
                source_signature=msg.signature, source_mode="AUTOMATIC_MESSAGE",
                event_type="MLB_DEBUT", event_subtype="MLB_DEBUT",
                player_id=main_player_id, team_id=main_team_id, league_id=None, league_label=None,
                season=season, event_date=event_date, position_label=None,
                title=desc, context_text=msg.first_line, structured_context_json=None,
                resolution_status="published", source_ref=msg.filepath
            )
            return [rec]

    # 4. DRAFT
    if 'draft' in text_lower or 'drafted' in text_lower:
        if 'drafted' in text_lower or 'selected in the' in text_lower or 'draft pick' in text_lower:
            round_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*round', text_lower)
            pick_match = re.search(r'(\d+)(?:st|nd|rd|th)?\s*(?:overall|pick)', text_lower)

            rnd = round_match.group(1) if round_match else None
            pick = pick_match.group(1) if pick_match else None

            if rnd and pick:
                desc = f"신인 드래프트 {rnd}라운드 {pick}순위 지명"
            elif rnd:
                desc = f"신인 드래프트 {rnd}라운드 지명"
            else:
                desc = "신인 드래프트 지명"

            rec = PlayerHistoryEventRecord(
                id=None, source_family="MESSAGES", source_event_id=f"msg_{msg.msg_id}",
                source_signature=msg.signature, source_mode="AUTOMATIC_MESSAGE",
                event_type="DRAFT", event_subtype="DRAFT_SELECTION",
                player_id=main_player_id, team_id=main_team_id, league_id=None, league_label=None,
                season=season, event_date=event_date, position_label=None,
                title=desc, context_text=msg.first_line, structured_context_json=None,
                resolution_status="published", source_ref=msg.filepath
            )
            return [rec]

    # 5. WAIVER CLAIM
    if 'waiver' in text_lower or 'claimed' in text_lower:
        if 'claimed off waivers' in text_lower or 'claimed on waivers' in text_lower or 'claimed from' in text_lower:
            team_name = msg.teams[0][0] if msg.teams else ""
            desc = f"{team_name}에서 웨이버 클레임" if team_name else "웨이버 클레임 이적"
            rec = PlayerHistoryEventRecord(
                id=None, source_family="MESSAGES", source_event_id=f"msg_{msg.msg_id}",
                source_signature=msg.signature, source_mode="AUTOMATIC_MESSAGE",
                event_type="TRANSACTION", event_subtype="WAIVER_CLAIM",
                player_id=main_player_id, team_id=main_team_id, league_id=None, league_label=None,
                season=season, event_date=event_date, position_label=None,
                title=desc, context_text=msg.first_line, structured_context_json=None,
                resolution_status="published", source_ref=msg.filepath
            )
            return [rec]

    # 6. RELEASE
    if 'released' in text_lower or 'release' in text_lower:
        if 'released by' in text_lower or 'released from' in text_lower or 'was released' in text_lower:
            team_name = msg.teams[0][0] if msg.teams else ""
            desc = f"{team_name}에서 방출" if team_name else "방출"
            rec = PlayerHistoryEventRecord(
                id=None, source_family="MESSAGES", source_event_id=f"msg_{msg.msg_id}",
                source_signature=msg.signature, source_mode="AUTOMATIC_MESSAGE",
                event_type="TRANSACTION", event_subtype="RELEASE",
                player_id=main_player_id, team_id=main_team_id, league_id=None, league_label=None,
                season=season, event_date=event_date, position_label=None,
                title=desc, context_text=msg.first_line, structured_context_json=None,
                resolution_status="published", source_ref=msg.filepath
            )
            return [rec]

    # 7. DFA
    if 'designated for assignment' in text_lower or 'dfa' in text_lower:
        if 'designated for assignment' in text_lower or 'placed in dfa' in text_lower:
            desc = "지명할당"
            rec = PlayerHistoryEventRecord(
                id=None, source_family="MESSAGES", source_event_id=f"msg_{msg.msg_id}",
                source_signature=msg.signature, source_mode="AUTOMATIC_MESSAGE",
                event_type="TRANSACTION", event_subtype="DFA",
                player_id=main_player_id, team_id=main_team_id, league_id=None, league_label=None,
                season=season, event_date=event_date, position_label=None,
                title=desc, context_text=msg.first_line, structured_context_json=None,
                resolution_status="published", source_ref=msg.filepath
            )
            return [rec]

    # 8. ROSTER MOVE (Call-up / Option / Demotion)
    if any(k in text_lower for k in ['promoted to', 'recalled', 'called up', 'optioned to', 'demoted to']):
        if 'recalled' in text_lower or 'promoted to major' in text_lower or 'called up' in text_lower:
            desc = "MLB 콜업"
            subtype = "MLB_CALLUP"
        elif 'optioned to aaa' in text_lower or 'optioned to' in text_lower:
            desc = "AAA로 옵션"
            subtype = "OPTION_AAA"
        elif 'demoted' in text_lower:
            desc = "마이너리그 강등"
            subtype = "DEMOTION"
        else:
            desc = None

        if desc:
            rec = PlayerHistoryEventRecord(
                id=None, source_family="MESSAGES", source_event_id=f"msg_{msg.msg_id}",
                source_signature=msg.signature, source_mode="AUTOMATIC_MESSAGE",
                event_type="ROSTER_MOVE", event_subtype=subtype,
                player_id=main_player_id, team_id=main_team_id, league_id=None, league_label=None,
                season=season, event_date=event_date, position_label=None,
                title=desc, context_text=msg.first_line, structured_context_json=None,
                resolution_status="published", source_ref=msg.filepath
            )
            return [rec]

    return []
