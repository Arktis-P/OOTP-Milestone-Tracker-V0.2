import hashlib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from .competition_classifier import classify_competition
from .game_models import BattingEvent, BattingLine, GameRecord, PitchingLine


def parse_ip_to_outs(ip_str: str) -> int:
    try:
        parts = ip_str.split(".")
        full_innings = int(parts[0])
        extra_outs = int(parts[1]) if len(parts) > 1 else 0
        return full_innings * 3 + extra_outs
    except ValueError:
        return 0


def parse_game_header(html: str, filename: str) -> Tuple[int, str, str, int, str, int, int, Optional[int], int, int]:
    game_id_m = re.search(r"game_box_(\d+)\.html", filename)
    game_id = int(game_id_m.group(1)) if game_id_m else 0

    title_m = re.search(r"<title>(.*?)</title>", html)
    title = title_m.group(1) if title_m else ""

    date_m = re.search(r"(\d{2}/\d{2}/\d{4})", title)
    game_date = date_m.group(1) if date_m else ""
    season = int(game_date.split("/")[2]) if game_date else 2027

    # Team IDs
    team_links = list(dict.fromkeys(re.findall(r"../teams/team_(\d+)\.html", html)))
    away_team_id = int(team_links[0]) if len(team_links) > 0 else 0
    home_team_id = int(team_links[1]) if len(team_links) > 1 else 0

    # League ID
    league_links = re.findall(r"../leagues/league_(\d+)_", html)
    league_id = int(league_links[0]) if league_links else None

    competition_type = classify_competition(title, league_id)

    # Scores from header linescore or table if available
    away_score = 0
    home_score = 0
    # Try finding final score in linescore
    scores_m = re.findall(r"<td[^>]*class=[\"\']dc[\"\'][^>]*><b>(\d+)</b></td>", html)
    if len(scores_m) >= 2:
        away_score = int(scores_m[0])
        home_score = int(scores_m[1])

    return game_id, title, game_date, season, competition_type, away_team_id, home_team_id, league_id, away_score, home_score


def parse_batting_table(html: str, away_team_id: int, home_team_id: int) -> Dict[int, BattingLine]:
    """Parse upper batting table for GAME_DELTA fields (AB, R, H, RBI, BB, SO, LOB)."""
    batting_lines: Dict[int, BattingLine] = {}
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL)

    current_team_id = away_team_id

    for r in rows:
        # Check team header in table
        if "BATTING LINESCORE" in r:
            if "HOME" in r or "CHICAGO" in r or "SEOUL" in r: # fallback heuristic if team headers switch
                current_team_id = home_team_id
            continue

        if "../players/player_" not in r:
            continue

        pid_m = re.search(r"../players/player_(\d+)\.html", r)
        if not pid_m:
            continue
        pid = int(pid_m.group(1))

        cols = [re.sub(r"<[^>]+>", "", cell).strip() for cell in re.findall(r"<td[^>]*>(.*?)</td>", r, re.DOTALL)]
        if len(cols) == 11:
            try:
                name = cols[0]
                ab = int(cols[1])
                r_val = int(cols[2])
                h_val = int(cols[3])
                rbi = int(cols[4])
                bb = int(cols[5])
                so = int(cols[6])
                lob = int(cols[7])

                is_sub = ("&#160;" in r) or ("&nbsp;" in r) or (re.search(r"\b[a-z]-", name) is not None)
                is_starter = not is_sub

                batting_lines[pid] = BattingLine(
                    player_id=pid,
                    name=name,
                    team_id=current_team_id,
                    ab=ab,
                    r=r_val,
                    h=h_val,
                    rbi=rbi,
                    bb=bb,
                    so=so,
                    lob=lob,
                    is_starter=is_starter,
                )
            except ValueError:
                pass


    return batting_lines


def parse_batting_summary_text(html: str, game_id: int, batting_lines: Dict[int, BattingLine]) -> List[BattingEvent]:
    """Parse lower textual batting summary for 2B, 3B, HR, SB deltas and events."""
    events: List[BattingEvent] = []
    event_idx = 0

    # Pattern for summary blocks: <b>Category: </b> ...
    category_patterns = [
        ("Doubles:", "DOUBLE"),
        ("Triples:", "TRIPLE"),
        ("Home Runs:", "HOME_RUN"),
        ("Stolen Bases:", "STOLEN_BASE"),
        ("SB:", "STOLEN_BASE"),
    ]

    for cat_label, event_type in category_patterns:
        match = re.search(rf"<b>{cat_label}\s*</b>(.*?)(?:<br><b>|<td|Total Bases:|$)", html, re.DOTALL | re.IGNORECASE)
        if not match:
            continue

        block = match.group(1)
        # Find player links inside block: <a href="../players/player_123.html">Name</a> [count] (season_total, context...)
        item_matches = re.findall(
            r"<a\s+href=[\"\'].*?player_(\d+)\.html[\"\'][^>]*>(.*?)</a>(?:\s*(\d+))?\s*\((.*?)\)",
            block,
            re.DOTALL,
        )

        for pid_str, name, count_str, info_str in item_matches:
            pid = int(pid_str)
            game_count = int(count_str) if count_str.strip() else 1
            info = info_str.strip()

            # Season total is first integer inside info parentheses: e.g., "(22, 3rd Inning...)" or "(1)"
            season_total_m = re.match(r"^(\d+)", info)
            season_total = int(season_total_m.group(1)) if season_total_m else None

            # Check opponent pitcher if mentioned
            pitcher_m = re.search(r"off\s+(?:<a[^>]*>)?([A-Za-z\s\.\-\']+)(?:</a>|\,)", info)
            context_text = info

            # Update batting line deltas
            if pid in batting_lines:
                line = batting_lines[pid]
                if event_type == "DOUBLE":
                    line.doubles += game_count
                elif event_type == "TRIPLE":
                    line.triples += game_count
                elif event_type == "HOME_RUN":
                    line.hr += game_count
                elif event_type == "STOLEN_BASE":
                    line.sb += game_count

            # Create individual events for each occurrence
            for _ in range(game_count):
                event_idx += 1
                events.append(
                    BattingEvent(
                        game_id=game_id,
                        player_id=pid,
                        event_index=event_idx,
                        event_type=event_type,
                        season_total=season_total,
                        context_text=context_text,
                    )
                )

    return events


def parse_pitching_table(html: str, away_team_id: int, home_team_id: int) -> List[PitchingLine]:
    """Parse pitching table for outs, H, R, ER, BB, SO, HR, BF, Pitches, W/L/SV/HOLD."""
    pitching_lines: List[PitchingLine] = []
    rows = re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL)
    current_team_id = away_team_id

    for r in rows:
        if "PITCHING LINESCORE" in r:
            if "HOME" in r or "CHICAGO" in r or "SEOUL" in r:
                current_team_id = home_team_id
            continue

        if "../players/player_" not in r:
            continue

        pid_m = re.search(r"../players/player_(\d+)\.html", r)
        if not pid_m:
            continue
        pid = int(pid_m.group(1))

        cols = [re.sub(r"<[^>]+>", "", cell).strip() for cell in re.findall(r"<td[^>]*>(.*?)</td>", r, re.DOTALL)]
        if len(cols) >= 10:
            try:
                name = cols[0]
                outs = parse_ip_to_outs(cols[1])
                h_val = int(cols[2])
                r_val = int(cols[3])
                er = int(cols[4])
                bb = int(cols[5])
                so = int(cols[6])
                hr = int(cols[7])
                bf = int(cols[8])
                pitches = int(cols[9])

                win = " W " in f" {name} " or " W(" in name
                loss = " L " in f" {name} " or " L(" in name
                save = " SV " in f" {name} " or " SV(" in name
                hold = " H " in f" {name} " or " H(" in name

                pitching_lines.append(
                    PitchingLine(
                        player_id=pid,
                        name=name,
                        team_id=current_team_id,
                        outs=outs,
                        h=h_val,
                        r=r_val,
                        er=er,
                        bb=bb,
                        so=so,
                        hr=hr,
                        bf=bf,
                        pitches=pitches,
                        win=win,
                        loss=loss,
                        save=save,
                        hold=hold,
                    )
                )
            except ValueError:
                pass

    return pitching_lines


def parse_game_box(file_path: Path) -> GameRecord:
    content = file_path.read_bytes()
    source_hash = hashlib.sha256(content).hexdigest()
    html = content.decode("utf-8", errors="replace")

    game_id, title, game_date, season, comp_type, away_id, home_id, league_id, away_score, home_score = (
        parse_game_header(html, file_path.name)
    )

    batting_lines_dict = parse_batting_table(html, away_id, home_id)
    batting_events = parse_batting_summary_text(html, game_id, batting_lines_dict)
    pitching_lines = parse_pitching_table(html, away_id, home_id)

    return GameRecord(
        game_id=game_id,
        title=title,
        game_date=game_date,
        season=season,
        competition_type=comp_type,
        league_id=league_id,
        away_team_id=away_id,
        home_team_id=home_id,
        away_score=away_score,
        home_score=home_score,
        source_hash=source_hash,
        batting_lines=list(batting_lines_dict.values()),
        pitching_lines=pitching_lines,
        batting_events=batting_events,
    )
