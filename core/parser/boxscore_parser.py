"""
OOTP Boxscore HTML Parser (Phase 2.2 & 2.3)
Parses game_box_XXXX.html files and extracts game metadata, player batting/pitching lines,
and special events (Cycle, Grand Slam, Complete Game, Shutout, No-Hitter, Perfect Game, etc.).
"""

import os
import re
from datetime import datetime
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup


@dataclass
class ParsedBattingLine:
    ootp_player_id: int
    display_name: str
    team_name: str
    ab: int = 0
    r: int = 0
    h: int = 0
    d: int = 0
    t: int = 0
    hr: int = 0
    rbi: int = 0
    bb: int = 0
    k: int = 0
    sb: int = 0
    cs: int = 0
    sh: int = 0
    sf: int = 0
    hbp: int = 0
    raw_notes: str = ""


@dataclass
class ParsedPitchingLine:
    ootp_player_id: int
    display_name: str
    team_name: str
    ip_outs: int = 0
    h: int = 0
    r: int = 0
    er: int = 0
    bb: int = 0
    k: int = 0
    hr: int = 0
    w: int = 0
    l: int = 0
    sv: int = 0
    hld: int = 0
    cg: int = 0
    sho: int = 0
    raw_notes: str = ""


@dataclass
class ParsedSpecialEvent:
    event_type: str  # cycle, grand_slam, no_hitter, perfect_game, complete_game, shutout, etc.
    ootp_player_id: Optional[int]
    player_name: str
    team_name: str
    description: str


@dataclass
class ParsedBoxscore:
    season: int
    ootp_game_id: int
    game_date: str  # YYYY-MM-DD
    away_team_name: str
    home_team_name: str
    game_type: str = "RS"  # RS = Regular Season, PS = Postseason, ST = Spring Training
    batting_lines: List[ParsedBattingLine] = field(default_factory=list)
    pitching_lines: List[ParsedPitchingLine] = field(default_factory=list)
    special_events: List[ParsedSpecialEvent] = field(default_factory=list)


class BoxscoreParser:
    PLAYER_ID_REGEX = re.compile(r"player_(\d+)\.html")
    DATE_REGEX = re.compile(r"GAME ID:\s*(\d+)\s*-\s*.*?,\s*([A-Za-z]+)\s+(\d+)\w*?\s*,\s*(\d{4})", re.IGNORECASE)
    TITLE_DATE_REGEX = re.compile(r"(\d{2})/(\d{2})/(\d{4})")

    MONTH_MAP = {
        "january": 1, "february": 2, "march": 3, "april": 4, "may": 5, "june": 6,
        "july": 7, "august": 8, "september": 9, "october": 10, "november": 11, "december": 12,
        "jan": 1, "feb": 2, "mar": 3, "apr": 4, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12
    }

    @classmethod
    def parse_file(cls, file_path: str) -> ParsedBoxscore:
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
        return cls.parse_html(content, file_path=file_path)

    @classmethod
    def parse_html(cls, html_content: str, file_path: str = "") -> ParsedBoxscore:
        soup = BeautifulSoup(html_content, "html.parser")

        # 1. Extract Game ID, Date, Season, Teams
        ootp_game_id = 0
        if file_path:
            filename = os.path.basename(file_path)
            m_id = re.search(r"game_box_(\d+)\.html", filename)
            if m_id:
                ootp_game_id = int(m_id.group(1))

        away_team = "Away"
        home_team = "Home"

        title_tag = soup.find("title")
        if title_tag:
            title_text = title_tag.text.strip()
            # e.g., "MLB Box Score, Athletics at Chicago White Sox, 03/30/2027"
            parts = [p.strip() for p in title_text.split(",")]
            if len(parts) >= 2:
                teams_part = parts[1]
                if " at " in teams_part:
                    away_team, home_team = [t.strip() for t in teams_part.split(" at ", 1)]

        # Extract Date
        game_date = "2026-01-01"
        season = 2026

        header_text = soup.get_text()
        date_match = cls.DATE_REGEX.search(header_text)
        if date_match:
            if not ootp_game_id:
                ootp_game_id = int(date_match.group(1))
            month_str = date_match.group(2).lower()
            day = int(date_match.group(3))
            season = int(date_match.group(4))
            month = cls.MONTH_MAP.get(month_str, 1)
            game_date = f"{season:04d}-{month:02d}-{day:02d}"
        else:
            title_date_match = cls.TITLE_DATE_REGEX.search(header_text)
            if title_date_match:
                month = int(title_date_match.group(1))
                day = int(title_date_match.group(2))
                season = int(title_date_match.group(3))
                game_date = f"{season:04d}-{month:02d}-{day:02d}"

        boxscore = ParsedBoxscore(
            season=season,
            ootp_game_id=ootp_game_id,
            game_date=game_date,
            away_team_name=away_team,
            home_team_name=home_team,
        )

        # 2. Extract Batting Lines & Notes
        cls._parse_batting(soup, boxscore)

        # 3. Extract Pitching Lines & Notes
        cls._parse_pitching(soup, boxscore)

        # 4. Extract Special Events
        cls._parse_special_events(soup, boxscore)

        return boxscore

    @classmethod
    def _parse_batting(cls, soup: BeautifulSoup, boxscore: ParsedBoxscore) -> None:
        tables = soup.find_all("table")
        current_team = boxscore.away_team_name

        for table in tables:
            text = table.text
            if "BATTING LINESCORE" in text:
                if boxscore.home_team_name.upper() in text.upper():
                    current_team = boxscore.home_team_name
                else:
                    current_team = boxscore.away_team_name

            for tr in table.find_all("tr"):
                a_tag = tr.find("a", href=lambda h: h and "player_" in h)
                if not a_tag:
                    continue

                player_href = a_tag["href"]
                m_pid = cls.PLAYER_ID_REGEX.search(player_href)
                if not m_pid:
                    continue
                ootp_pid = int(m_pid.group(1))
                display_name = a_tag.text.strip()

                tds = [td.text.strip() for td in tr.find_all("td")]
                if len(tds) >= 7 and tds[1].isdigit():
                    try:
                        ab = int(tds[1])
                        r = int(tds[2]) if tds[2].isdigit() else 0
                        h = int(tds[3]) if tds[3].isdigit() else 0
                        rbi = int(tds[4]) if tds[4].isdigit() else 0
                        bb = int(tds[5]) if tds[5].isdigit() else 0
                        k = int(tds[6]) if tds[6].isdigit() else 0

                        boxscore.batting_lines.append(
                            ParsedBattingLine(
                                ootp_player_id=ootp_pid,
                                display_name=display_name,
                                team_name=current_team,
                                ab=ab, r=r, h=h, rbi=rbi, bb=bb, k=k
                            )
                        )
                    except Exception:
                        continue

    @classmethod
    def _parse_pitching(cls, soup: BeautifulSoup, boxscore: ParsedBoxscore) -> None:
        tables = soup.find_all("table")
        current_team = boxscore.away_team_name

        for table in tables:
            text = table.text
            if "PITCHING LINESCORE" in text:
                if boxscore.home_team_name.upper() in text.upper():
                    current_team = boxscore.home_team_name
                else:
                    current_team = boxscore.away_team_name

            for tr in table.find_all("tr"):
                a_tag = tr.find("a", href=lambda h: h and "player_" in h)
                if not a_tag:
                    continue

                player_href = a_tag["href"]
                m_pid = cls.PLAYER_ID_REGEX.search(player_href)
                if not m_pid:
                    continue
                ootp_pid = int(m_pid.group(1))

                tds = [td.text.strip() for td in tr.find_all("td")]
                if len(tds) >= 8 and (tds[1].replace(".", "").isdigit()):
                    pitcher_cell_text = tds[0]
                    display_name = a_tag.text.strip()

                    w = 1 if " W " in pitcher_cell_text or pitcher_cell_text.endswith(" W") else 0
                    l = 1 if " L " in pitcher_cell_text or pitcher_cell_text.endswith(" L") else 0
                    sv = 1 if " SV " in pitcher_cell_text or pitcher_cell_text.endswith(" SV") else 0
                    hld = 1 if " HLD " in pitcher_cell_text or pitcher_cell_text.endswith(" HLD") else 0

                    try:
                        ip_val = float(tds[1])
                        ip_full = int(ip_val)
                        ip_frac = round((ip_val - ip_full) * 10)
                        ip_outs = (ip_full * 3) + ip_frac

                        ha = int(tds[2]) if tds[2].isdigit() else 0
                        r = int(tds[3]) if tds[3].isdigit() else 0
                        er = int(tds[4]) if tds[4].isdigit() else 0
                        bb = int(tds[5]) if tds[5].isdigit() else 0
                        k = int(tds[6]) if tds[6].isdigit() else 0
                        hr = int(tds[7]) if tds[7].isdigit() else 0

                        cg = 1 if ip_outs >= 27 and r > 0 else 0
                        sho = 1 if ip_outs >= 27 and r == 0 else 0

                        boxscore.pitching_lines.append(
                            ParsedPitchingLine(
                                ootp_player_id=ootp_pid,
                                display_name=display_name,
                                team_name=current_team,
                                ip_outs=ip_outs, h=ha, r=r, er=er, bb=bb, k=k, hr=hr,
                                w=w, l=l, sv=sv, hld=hld, cg=cg, sho=sho
                            )
                        )
                    except Exception:
                        continue

    @classmethod
    def _parse_special_events(cls, soup: BeautifulSoup, boxscore: ParsedBoxscore) -> None:
        full_text = soup.get_text()

        # Check Special Events in Notes
        if "hit for the cycle" in full_text.lower():
            boxscore.special_events.append(
                ParsedSpecialEvent(
                    event_type="cycle",
                    ootp_player_id=None,
                    player_name="",
                    team_name="",
                    description="Hit for the Cycle"
                )
            )

        if "grand slam" in full_text.lower():
            boxscore.special_events.append(
                ParsedSpecialEvent(
                    event_type="grand_slam",
                    ootp_player_id=None,
                    player_name="",
                    team_name="",
                    description="Grand Slam"
                )
            )

        if "no-hitter" in full_text.lower() or "no hitter" in full_text.lower():
            boxscore.special_events.append(
                ParsedSpecialEvent(
                    event_type="no_hitter",
                    ootp_player_id=None,
                    player_name="",
                    team_name="",
                    description="No-Hitter"
                )
            )

        if "perfect game" in full_text.lower():
            boxscore.special_events.append(
                ParsedSpecialEvent(
                    event_type="perfect_game",
                    ootp_player_id=None,
                    player_name="",
                    team_name="",
                    description="Perfect Game"
                )
            )
