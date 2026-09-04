import re
from typing import Optional, Dict

BODY_SIDE_MAP = {
    'left': '왼쪽',
    'right': '오른쪽'
}

DIAGNOSIS_MAP = {
    'ulnar collateral ligament': '팔꿈치 인대 (UCL)',
    'ucl': '팔꿈치 인대 (UCL)',
    'rotator cuff': '회전근개',
    'hamstring': '햄스트링',
    'labrum': '와순',
    'radial nerve compression': '요골신경 압박',
    'posterior cruciate ligament': '후방십자인대',
    'knee': '무릎',
    'shoulder': '어깨',
    'elbow': '팔꿈치',
    'oblique': '복사근',
    'back': '등/허리',
    'forearm': '전완근',
    'groin': '사타구니',
    'hip': '고관절',
    'wrist': '손목',
    'ankle': '발목',
    'finger': '손가락',
}

POSITION_MAP = {
    'C': '포수',
    'CATCHER': '포수',
    '1B': '1루수',
    'FIRST BASE': '1루수',
    'FIRST BASEMAN': '1루수',
    '2B': '2루수',
    'SECOND BASE': '2루수',
    'SECOND BASEMAN': '2루수',
    '3B': '3루수',
    'THIRD BASE': '3루수',
    'THIRD BASEMAN': '3루수',
    'SS': '유격수',
    'SHORTSTOP': '유격수',
    'LF': '좌익수',
    'LEFT FIELD': '좌익수',
    'LEFT FIELDER': '좌익수',
    'CF': '중견수',
    'CENTER FIELD': '중견수',
    'CENTER FIELDER': '중견수',
    'RF': '우익수',
    'RIGHT FIELD': '우익수',
    'RIGHT FIELDER': '우익수',
    'DH': '지명타자',
    'DESIGNATED HITTER': '지명타자',
    'P': '투수',
    'SP': '선발투수',
    'RP': '구원투수',
    'CL': '마무리투수',
    'STARTING PITCHER': '선발투수',
    'RELIEVER': '구원투수',
}

LEAGUE_MAP = {
    'AMERICAN LEAGUE': 'AL',
    'NATIONAL LEAGUE': 'NL',
    'AL': 'AL',
    'NL': 'NL',
    'KBO LEAGUE': 'KBO',
    'KBO': 'KBO',
    'MLB': 'MLB',
}

def translate_body_side(side_en: Optional[str]) -> Optional[str]:
    if not side_en:
        return None
    return BODY_SIDE_MAP.get(side_en.strip().lower())

def translate_diagnosis(diag_en: str) -> str:
    lower = diag_en.strip().lower()
    for k, v in DIAGNOSIS_MAP.items():
        if k in lower:
            return v
    return diag_en.strip()

def translate_position(pos_en: Optional[str]) -> str:
    if not pos_en:
        return ""
    upper = pos_en.strip().upper()
    return POSITION_MAP.get(upper, pos_en)

def translate_league(league_en: Optional[str]) -> str:
    if not league_en:
        return ""
    upper = league_en.strip().upper()
    return LEAGUE_MAP.get(upper, league_en)

def render_injury_description(side_ko: Optional[str], diag_ko: str, duration_ko: str) -> str:
    if side_ko:
        return f"{side_ko} {diag_ko} 부상으로 {duration_ko} 진단."
    return f"{diag_ko} 부상으로 {duration_ko} 진단."

def render_allstar_description(is_starter: bool, league_ko: str, pos_ko: str) -> str:
    league_prefix = f"{league_ko} " if league_ko else ""
    pos_prefix = f"{pos_ko} " if pos_ko else ""
    if is_starter:
        return f"팬 투표 1위로 {league_prefix}{pos_prefix}올스타 선정"
    return "감독 추천으로 올스타 출전"

def render_award_description(award_subtype: str, league_ko: str, pos_ko: str, vote_count: Optional[int], is_unanimous: bool) -> str:
    league_prefix = f"{league_ko} " if league_ko else ""
    pos_prefix = f"{pos_ko} " if pos_ko else ""
    
    if award_subtype == 'SILVER_SLUGGER':
        return f"{league_prefix}{pos_prefix}플래티넘 스틱 수상"
    elif award_subtype == 'GOLD_GLOVE':
        return f"{league_prefix}{pos_prefix}골든 글러브 수상"
    elif award_subtype in ('MVP', 'CY_YOUNG', 'ROOKIE_OF_YEAR', 'RELIEVER_OF_YEAR'):
        award_names = {
            'MVP': 'MVP',
            'CY_YOUNG': '사이영상',
            'ROOKIE_OF_YEAR': '신인왕',
            'RELIEVER_OF_YEAR': '구원투수상'
        }
        name = award_names.get(award_subtype, award_subtype)
        if vote_count is not None:
            if is_unanimous:
                return f"{vote_count}표 만장일치로 {league_prefix}{name} 수상"
            return f"{vote_count}표로 {league_prefix}{name} 수상"
        return f"{league_prefix}{name} 수상"
    return f"{league_prefix}{award_subtype} 수상"

def render_monthly_award_description(month_num: int, award_category: str) -> str:
    # award_category: 'hitter', 'pitcher', 'rookie'
    type_name = {'hitter': '타자', 'pitcher': '투수', 'rookie': '신인'}.get(award_category, '선수')
    return f"이달의 {type_name} ({month_num}월) 선정"

def render_manual_league_title_description(stat_key: str, stat_val_str: str, league_ko: str) -> str:
    league_prefix = f"{league_ko} " if league_ko else ""
    title_map = {
        'AVG': f"시즌 타율 {stat_val_str}로 {league_prefix}타격왕 수상",
        'H': f"시즌 {stat_val_str}안타로 {league_prefix}안타왕 수상",
        'OBP': f"시즌 출루율 {stat_val_str}로 {league_prefix}출루왕 수상",
        'HR': f"시즌 {stat_val_str}홈런으로 {league_prefix}홈런왕 수상",
        'RBI': f"시즌 {stat_val_str}타점으로 {league_prefix}타점왕 수상",
        'SB': f"시즌 {stat_val_str}도루로 {league_prefix}도루왕 수상",
        'R': f"시즌 {stat_val_str}득점으로 {league_prefix}득점왕 수상",
        'OPS': f"시즌 OPS {stat_val_str}로 {league_prefix}OPS 1위 수상",
        'W': f"시즌 {stat_val_str}승으로 {league_prefix}다승왕 수상",
        'ERA': f"시즌 ERA {stat_val_str}로 {league_prefix}ERA 1위 수상",
        'IP': f"시즌 {stat_val_str}이닝으로 {league_prefix}최다이닝 1위 수상",
        'SO': f"시즌 {stat_val_str}탈삼진으로 {league_prefix}탈삼진왕 수상",
        'SV': f"시즌 {stat_val_str}세이브로 {league_prefix}구원왕 수상",
        'HOLD': f"시즌 {stat_val_str}홀드로 {league_prefix}홀드왕 수상",
        'WPCT': f"시즌 승률 {stat_val_str}로 {league_prefix}승률 1위 수상",
    }
    return title_map.get(stat_key, f"시즌 {stat_val_str} {stat_key}로 {league_prefix}1위 수상")
