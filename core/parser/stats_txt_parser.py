"""
OOTP Stats TXT Parser (Phase 2.1)
Parses player_batting_stats.txt and player_pitching_stats.txt export files.
Extracted data is kept purely in memory (read-only) and returned as structured DTOs.
"""

import os
import re
from dataclasses import dataclass
from typing import List, Dict, Any, Tuple, Optional


@dataclass
class ParsedTeamHeader:
    team_id: int
    name: str
    league_name: str
    league_id: int


@dataclass
class ParsedBattingBaseline:
    ootp_player_id: int
    first_name: str
    last_name: str
    year: int
    team_id: int
    team_abbr: str
    g: int
    ab: int
    r: int
    h: int
    d: int
    t: int
    hr: int
    rbi: int
    bb: int
    k: int
    sb: int
    cs: int
    avg: float
    obp: float
    slg: float
    ops: float
    is_career: bool = False


@dataclass
class ParsedPitchingBaseline:
    ootp_player_id: int
    first_name: str
    last_name: str
    year: int
    team_id: int
    team_abbr: str
    g: int
    gs: int
    w: int
    l: int
    sv: int
    hld: int
    ip_outs: int
    h: int
    r: int
    er: int
    bb: int
    k: int
    hr: int
    era: float
    whip: float
    is_career: bool = False


class StatsTxtParser:
    TEAM_MAPPING_REGEX = re.compile(r"^//(\d+)\s*=>\s*(.*?)\s*\((.*?)\s*=>\s*(\d+)\)")

    @classmethod
    def parse_team_headers(cls, file_path: str) -> List[ParsedTeamHeader]:
        teams: List[ParsedTeamHeader] = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if not line.startswith("//"):
                    break
                match = cls.TEAM_MAPPING_REGEX.match(line.strip())
                if match:
                    t_id = int(match.group(1))
                    t_name = match.group(2).strip()
                    l_name = match.group(3).strip()
                    l_id = int(match.group(4))
                    teams.append(ParsedTeamHeader(team_id=t_id, name=t_name, league_name=l_name, league_id=l_id))
        return teams

    @classmethod
    def parse_batting_stats(cls, file_path: str, filter_split_id: int = 1) -> List[ParsedBattingBaseline]:
        records: List[ParsedBattingBaseline] = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_str = line.strip()
                if not line_str or line_str.startswith("//"):
                    continue

                parts = [p.strip() for p in line_str.split(",")]
                if len(parts) < 36 or parts[-1] != "eol":
                    continue

                try:
                    split_id = int(parts[27])
                    if filter_split_id is not None and split_id != filter_split_id:
                        continue

                    # Extract ootp_player_id from second to last column
                    ootp_pid = int(parts[35]) if parts[35].isdigit() else int(parts[0])
                    lastname = parts[1]
                    firstname = parts[2]
                    year = int(parts[3])
                    team_id = int(parts[4])
                    g = int(parts[5])
                    ab = int(parts[8])
                    h = int(parts[9])
                    d = int(parts[10])
                    t = int(parts[11])
                    hr = int(parts[12])
                    rbi = int(parts[13])
                    r = int(parts[14])
                    sb = int(parts[15])
                    cs = int(parts[16])
                    bb = int(parts[17])
                    hp = int(parts[18])
                    k = int(parts[19])
                    sf = int(parts[21])
                    team_abbr = parts[28]

                    pa = ab + bb + hp + sf
                    avg = (h / ab) if ab > 0 else 0.0
                    obp = ((h + bb + hp) / pa) if pa > 0 else 0.0
                    tb = h + d + (2 * t) + (3 * hr)
                    slg = (tb / ab) if ab > 0 else 0.0
                    ops = obp + slg

                    records.append(
                        ParsedBattingBaseline(
                            ootp_player_id=ootp_pid,
                            first_name=firstname,
                            last_name=lastname,
                            year=year,
                            team_id=team_id,
                            team_abbr=team_abbr,
                            g=g,
                            ab=ab,
                            r=r,
                            h=h,
                            d=d,
                            t=t,
                            hr=hr,
                            rbi=rbi,
                            bb=bb,
                            k=k,
                            sb=sb,
                            cs=cs,
                            avg=round(avg, 3),
                            obp=round(obp, 3),
                            slg=round(slg, 3),
                            ops=round(ops, 3),
                        )
                    )
                except (ValueError, IndexError):
                    continue
        return records

    @classmethod
    def parse_pitching_stats(cls, file_path: str, filter_split_id: int = 1) -> List[ParsedPitchingBaseline]:
        records: List[ParsedPitchingBaseline] = []
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                line_str = line.strip()
                if not line_str or line_str.startswith("//"):
                    continue

                parts = [p.strip() for p in line_str.split(",")]
                if len(parts) < 55 or parts[-1] != "eol":
                    continue

                try:
                    split_id = int(parts[46])
                    if filter_split_id is not None and split_id != filter_split_id:
                        continue

                    ootp_pid = int(parts[54]) if parts[54].isdigit() else int(parts[0])
                    lastname = parts[1]
                    firstname = parts[2]
                    year = int(parts[3])
                    team_id = int(parts[4])
                    g = int(parts[5])
                    gs = int(parts[6])
                    w = int(parts[7])
                    l = int(parts[8])
                    sv = int(parts[9])

                    # ip string format or float outs
                    ip_raw = float(parts[10])
                    ip_full = int(ip_raw)
                    ip_fraction = round((ip_raw - ip_full) * 10)
                    ip_outs = (ip_full * 3) + ip_fraction

                    ha = int(parts[11])
                    r = int(parts[12])
                    er = int(parts[13])
                    bb = int(parts[14])
                    k = int(parts[16])
                    hr = int(parts[22])
                    cg = int(parts[35])
                    sho = int(parts[36])
                    hld = int(parts[37])
                    team_abbr = parts[47]

                    ip_float = ip_outs / 3.0
                    era = (er * 9.0 / ip_float) if ip_float > 0 else 0.0
                    whip = ((ha + bb) / ip_float) if ip_float > 0 else 0.0

                    records.append(
                        ParsedPitchingBaseline(
                            ootp_player_id=ootp_pid,
                            first_name=firstname,
                            last_name=lastname,
                            year=year,
                            team_id=team_id,
                            team_abbr=team_abbr,
                            g=g,
                            gs=gs,
                            w=w,
                            l=l,
                            sv=sv,
                            hld=hld,
                            ip_outs=ip_outs,
                            h=ha,
                            r=r,
                            er=er,
                            bb=bb,
                            k=k,
                            hr=hr,
                            era=round(era, 2),
                            whip=round(whip, 2),
                        )
                    )
                except (ValueError, IndexError):
                    continue
        return records
