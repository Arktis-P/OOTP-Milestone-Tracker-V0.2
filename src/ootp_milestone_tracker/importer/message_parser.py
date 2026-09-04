import re
from typing import List, Optional, Tuple
from ootp_milestone_tracker.importer.message_models import RawMessage, PlayerHistoryEventRecord
from ootp_milestone_tracker.services.history_renderer import (
    translate_body_side, translate_diagnosis, translate_position, translate_league,
    render_injury_description, render_allstar_description, render_award_description,
    render_monthly_award_description
)

MONTH_NAME_TO_NUM = {
    'january': 1, 'february': 2, 'march': 3, 'april': 4,
    'may': 5, 'june': 6, 'july': 7, 'august': 8,
    'september': 9, 'october': 10, 'november': 11, 'december': 12
}

def extract_date_and_season(msg: RawMessage) -> Tuple[Optional[str], Optional[int]]:
    # Extract date pattern YYYY-MM-DD or MM/DD/YYYY from text
    date_match = re.search(r'(\d{2})/(\d{2})/(\d{4})', msg.raw_text)
    if date_match:
        m, d, y = int(date_match.group(1)), int(date_match.group(2)), int(date_match.group(3))
        return f"{y:04d}-{m:02d}-{d:02d}", y
    
    date_iso = re.search(r'(\d{4})-(\d{2})-(\d{2})', msg.raw_text)
    if date_iso:
        y, m, d = int(date_iso.group(1)), int(date_iso.group(2)), int(date_iso.group(3))
        return f"{y:04d}-{m:02d}-{d:02d}", y
        
    year_match = re.search(r'\b(20\d{2})\b', msg.raw_text)
    year = int(year_match.group(1)) if year_match else None
    return None, year


def parse_injury_message(msg: RawMessage) -> List[PlayerHistoryEventRecord]:
    text_lower = msg.raw_text.lower()
    if not any(k in text_lower for k in ['injured', 'suffered', 'sustained', 'hurt', 'diagnosis']):
        return []
    
    if not msg.players:
        return []

    # Exclude IL activation/return or setback only messages if no occurrence duration
    player_name, main_player_id = msg.players[0]
    
    # 1. Body Side
    side_match = re.search(r'\b(left|right)\b', text_lower)
    side_en = side_match.group(1) if side_match else None
    side_ko = translate_body_side(side_en)
    
    # 2. Diagnosis / Injury Name
    diag_keywords = [
        'ulnar collateral ligament', 'ucl', 'rotator cuff', 'hamstring', 'labrum',
        'radial nerve compression', 'posterior cruciate ligament', 'knee', 'shoulder',
        'elbow', 'oblique', 'back', 'forearm', 'groin', 'hip', 'wrist', 'ankle', 'finger'
    ]
    diag_found = None
    for kw in diag_keywords:
        if kw in text_lower:
            diag_found = kw
            break
            
    diag_ko = translate_diagnosis(diag_found) if diag_found else "부상"
    
    # 3. Duration Normalization
    duration_ko = None
    
    # Check range (e.g. 4-5 months, 13-14 months, 2-3 weeks)
    range_match = re.search(r'(\d+)\s*[-~to]\s*(\d+)\s*(days?|weeks?|months?)', text_lower)
    if range_match:
        n1, n2, unit = range_match.group(1), range_match.group(2), range_match.group(3)
        unit_str = '일' if 'day' in unit else ('주' if 'week' in unit else '개월')
        duration_ko = f"{n1}~{n2}{unit_str}"
    else:
        # Check single duration (e.g. 4 months, 14 days, 3 weeks, up to a week)
        single_match = re.search(r'(\d+)\s*(days?|weeks?|months?)', text_lower)
        if single_match:
            n, unit = single_match.group(1), single_match.group(2)
            unit_str = '일' if 'day' in unit else ('주' if 'week' in unit else '개월')
            duration_ko = f"{n}{unit_str}"
        elif 'up to a week' in text_lower or 'a week' in text_lower:
            duration_ko = "1주"
        elif 'rest of the season' in text_lower or 'season-ending' in text_lower:
            duration_ko = "시즌 아웃"
            
    resolution_status = "published" if (diag_found and duration_ko) else "unresolved"
    
    if not duration_ko:
        duration_ko = "미정"

    description = render_injury_description(side_ko, diag_ko, duration_ko)
    event_date, season = extract_date_and_season(msg)
    main_team_id = msg.teams[0][1] if msg.teams else None

    rec = PlayerHistoryEventRecord(
        id=None,
        source_family="MESSAGES",
        source_event_id=f"msg_{msg.msg_id}",
        source_signature=msg.signature,
        source_mode="AUTOMATIC_MESSAGE",
        event_type="INJURY",
        event_subtype="INJURY_OCCURRENCE",
        player_id=main_player_id,
        team_id=main_team_id,
        league_id=None,
        league_label=None,
        season=season,
        event_date=event_date,
        position_label=None,
        title=description,
        context_text=msg.first_line,
        structured_context_json=None,
        resolution_status=resolution_status,
        source_ref=msg.filepath
    )
    return [rec]


def parse_allstar_message(msg: RawMessage) -> List[PlayerHistoryEventRecord]:
    text_lower = msg.raw_text.lower()
    if 'all-star' not in text_lower and 'all star' not in text_lower:
        return []
        
    # Explicitly ignore intermediate voting updates
    if 'voting update' in text_lower or 'fan voting' in text_lower:
        return []
        
    # Must be MLB roster announcement (exclude minor leagues like EL, TL, MWL, CAL, SAL, PCL, SL, etc.)
    if not ('mlb' in text_lower or 'major league' in text_lower or ('american league' in text_lower and 'national league' in text_lower)):
        return []

    events = []
    event_date, season = extract_date_and_season(msg)
    
    # Parse roster lines in MLB message
    # Format e.g.:
    # SP <Garrett Crochet:player#44286> (BOS) - ...
    # 1B <Ben Rice:player#50594> (NYY)* - ...
    current_league = "AL"
    
    lines = msg.raw_text.splitlines()
    for line in lines:
        line_s = line.strip()
        if 'American League' in line_s:
            current_league = "AL"
        elif 'National League' in line_s:
            current_league = "NL"
            
        m = re.match(r'^(SP|RP|CL|C|1B|2B|3B|SS|LF|CF|RF|DH)\s+<([^:>]+):player#(\d+)>\s*\(([A-Z0-9]+)\)(\*)?', line_s)
        if m:
            pos_en = m.group(1)
            player_name = m.group(2)
            player_id = int(m.group(3))
            team_code = m.group(4)
            is_starter = (m.group(5) == '*')
            
            pos_ko = translate_position(pos_en)
            league_ko = translate_league(current_league)
            
            subtype = "ALL_STAR_STARTER" if is_starter else "ALL_STAR_RESERVE"
            desc = render_allstar_description(is_starter, league_ko, pos_ko)
            
            rec = PlayerHistoryEventRecord(
                id=None,
                source_family="MESSAGES",
                source_event_id=f"msg_{msg.msg_id}",
                source_signature=msg.signature,
                source_mode="AUTOMATIC_MESSAGE",
                event_type="ALL_STAR",
                event_subtype=subtype,
                player_id=player_id,
                team_id=None,
                league_id=None,
                league_label=current_league,
                season=season,
                event_date=event_date,
                position_label=pos_en,
                title=desc,
                context_text=msg.first_line,
                structured_context_json=None,
                resolution_status="published",
                source_ref=msg.filepath
            )
            events.append(rec)
            
    return events


def parse_award_message(msg: RawMessage) -> List[PlayerHistoryEventRecord]:
    text_lower = msg.raw_text.lower()
    event_date, season = extract_date_and_season(msg)
    events = []

    # 1. Position Awards (Platinum Stick / Silver Slugger, Gold Glove)
    if 'platinum stick' in text_lower or 'silver slugger' in text_lower:
        subtype = 'SILVER_SLUGGER'
        # Parse block lines e.g.:
        # <Third Baseman:value_bold#0>
        # <Juan Hernandez:player#137746> (<Detroit (FCL) Tigers:team#108>)
        curr_pos = None
        for line in msg.raw_text.splitlines():
            line_s = line.strip()
            pos_match = re.search(r'<([^:>]+):value_bold#0>', line_s)
            if pos_match:
                curr_pos = pos_match.group(1)
            player_match = re.search(r'<([^:>]+):player#(\d+)>', line_s)
            if player_match and curr_pos:
                p_id = int(player_match.group(2))
                pos_ko = translate_position(curr_pos)
                league_label = "NL" if "nl" in text_lower or "national league" in text_lower else ("AL" if "al" in text_lower or "american league" in text_lower else "")
                league_ko = translate_league(league_label)
                desc = render_award_description(subtype, league_ko, pos_ko, None, False)
                events.append(PlayerHistoryEventRecord(
                    id=None, source_family="MESSAGES", source_event_id=f"msg_{msg.msg_id}",
                    source_signature=msg.signature, source_mode="AUTOMATIC_MESSAGE",
                    event_type="AWARD", event_subtype=subtype, player_id=p_id,
                    team_id=None, league_id=None, league_label=league_label,
                    season=season, event_date=event_date, position_label=curr_pos,
                    title=desc, context_text=msg.first_line, structured_context_json=None,
                    resolution_status="published", source_ref=msg.filepath
                ))
        if events:
            return events

    if 'gold glove' in text_lower or 'golden glove' in text_lower:
        subtype = 'GOLD_GLOVE'
        curr_pos = None
        for line in msg.raw_text.splitlines():
            line_s = line.strip()
            pos_match = re.search(r'<([^:>]+):value_bold#0>', line_s)
            if pos_match:
                curr_pos = pos_match.group(1)
            player_match = re.search(r'<([^:>]+):player#(\d+)>', line_s)
            if player_match and curr_pos:
                p_id = int(player_match.group(2))
                pos_ko = translate_position(curr_pos)
                league_label = "NL" if "nl" in text_lower or "national league" in text_lower else ("AL" if "al" in text_lower or "american league" in text_lower else "")
                league_ko = translate_league(league_label)
                desc = render_award_description(subtype, league_ko, pos_ko, None, False)
                events.append(PlayerHistoryEventRecord(
                    id=None, source_family="MESSAGES", source_event_id=f"msg_{msg.msg_id}",
                    source_signature=msg.signature, source_mode="AUTOMATIC_MESSAGE",
                    event_type="AWARD", event_subtype=subtype, player_id=p_id,
                    team_id=None, league_id=None, league_label=league_label,
                    season=season, event_date=event_date, position_label=curr_pos,
                    title=desc, context_text=msg.first_line, structured_context_json=None,
                    resolution_status="published", source_ref=msg.filepath
                ))
        if events:
            return events

    # 2. Major Voted Awards (MVP, Cy Young, Rookie of the Year, Reliever of the Year)
    award_subtype = None
    if 'most valuable player' in text_lower or 'mvp' in text_lower:
        award_subtype = 'MVP'
    elif 'cy young' in text_lower or 'pitcher of the year' in text_lower:
        award_subtype = 'CY_YOUNG'
    elif 'rookie of the year' in text_lower:
        award_subtype = 'ROOKIE_OF_YEAR'
    elif 'reliever of the year' in text_lower or 'reliever award' in text_lower:
        award_subtype = 'RELIEVER_OF_YEAR'

    if award_subtype and msg.players:
        winner_name, winner_id = msg.players[0]
        
        # League label
        league_label = "AL" if ("american league" in text_lower or " al " in text_lower or " al)" in text_lower) else ("NL" if ("national league" in text_lower or " nl " in text_lower or " nl)" in text_lower) else "")
        league_ko = translate_league(league_label)
        
        # Vote count & Unanimity
        vote_count = None
        total_votes = None
        is_unanimous = 'unanimous' in text_lower
        
        vote_match = re.search(r'received\s+(\d+)\s+first\s+place\s+votes\s+out\s+of\s+a\s+possible\s+(\d+)', text_lower)
        if vote_match:
            vote_count = int(vote_match.group(1))
            total_votes = int(vote_match.group(2))
            if vote_count == total_votes:
                is_unanimous = True
        else:
            vote_unanimous_match = re.search(r'received\s+(\d+)\s+first\s+place\s+votes.*unanimous', text_lower)
            if vote_unanimous_match:
                vote_count = int(vote_unanimous_match.group(1))
                is_unanimous = True

        desc = render_award_description(award_subtype, league_ko, "", vote_count, is_unanimous)
        
        rec = PlayerHistoryEventRecord(
            id=None, source_family="MESSAGES", source_event_id=f"msg_{msg.msg_id}",
            source_signature=msg.signature, source_mode="AUTOMATIC_MESSAGE",
            event_type="AWARD", event_subtype=award_subtype, player_id=winner_id,
            team_id=msg.teams[0][1] if msg.teams else None, league_id=None, league_label=league_label,
            season=season, event_date=event_date, position_label=None,
            title=desc, context_text=msg.first_line, structured_context_json=None,
            resolution_status="published", source_ref=msg.filepath
        )
        return [rec]

    return []


def parse_monthly_award_message(msg: RawMessage) -> List[PlayerHistoryEventRecord]:
    text_lower = msg.raw_text.lower()
    if not any(k in text_lower for k in ['player of the month', 'pitcher of the month', 'rookie of the month']):
        return []
        
    if not msg.players:
        return []

    winner_name, winner_id = msg.players[0]
    event_date, season = extract_date_and_season(msg)
    
    # Month resolution
    month_num = 6 # default
    for m_name, m_val in MONTH_NAME_TO_NUM.items():
        if m_name in text_lower:
            month_num = m_val
            break
            
    award_cat = 'hitter'
    if 'pitcher of the month' in text_lower:
        award_cat = 'pitcher'
    elif 'rookie of the month' in text_lower:
        award_cat = 'rookie'
        
    desc = render_monthly_award_description(month_num, award_cat)
    
    rec = PlayerHistoryEventRecord(
        id=None, source_family="MESSAGES", source_event_id=f"msg_{msg.msg_id}",
        source_signature=msg.signature, source_mode="AUTOMATIC_MESSAGE",
        event_type="MONTHLY_AWARD", event_subtype=f"MONTHLY_{award_cat.upper()}", player_id=winner_id,
        team_id=msg.teams[0][1] if msg.teams else None, league_id=None, league_label=None,
        season=season, event_date=event_date, position_label=None,
        title=desc, context_text=msg.first_line, structured_context_json=None,
        resolution_status="published", source_ref=msg.filepath
    )
    return [rec]
