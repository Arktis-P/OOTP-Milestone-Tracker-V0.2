import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class BattingLine:
    player_id: int
    name: str
    ab: int
    r: int
    h: int
    rbi: int
    bb: int
    so: int
    lob: int
    hr: int
    sb: int


@dataclass
class PitchingLine:
    player_id: int
    name: str
    outs: int
    h: int
    r: int
    er: int
    bb: int
    so: int
    hr: int
    bf: int
    pitches: int
    win: bool = False
    loss: bool = False
    save: bool = False
    hold: bool = False


@dataclass
class GameRecord:
    game_id: int
    title: str
    game_date: str
    season: int
    competition_type: str
    away_team_id: int
    home_team_id: int
    league_id: Optional[int]
    batting_lines: List[BattingLine] = field(default_factory=list)
    pitching_lines: List[PitchingLine] = field(default_factory=list)


def parse_ip_to_outs(ip_str: str) -> int:
    try:
        parts = ip_str.split(".")
        full_innings = int(parts[0])
        extra_outs = int(parts[1]) if len(parts) > 1 else 0
        return full_innings * 3 + extra_outs
    except ValueError:
        return 0


def parse_game_box(file_path: Path) -> GameRecord:
    game_id = int(re.search(r"game_box_(\d+)\.html", file_path.name).group(1))
    html = file_path.read_text(encoding="utf-8", errors="replace")

    # Title & Metadata
    title_m = re.search(r"<title>(.*?)</title>", html)
    title = title_m.group(1) if title_m else ""

    date_m = re.search(r"(\d{2}/\d{2}/\d{4})", title)
    game_date = date_m.group(1) if date_m else ""
    season = int(game_date.split("/")[2]) if game_date else 2027

    # Competition type: default regular_season (extendable by league/title regex)
    competition_type = "regular_season"

    # Team IDs
    team_links = list(dict.fromkeys(re.findall(r"../teams/team_(\d+)\.html", html)))
    away_team_id = int(team_links[0]) if len(team_links) > 0 else 0
    home_team_id = int(team_links[1]) if len(team_links) > 1 else 0

    # League ID
    league_links = re.findall(r"../leagues/league_(\d+)_", html)
    league_id = int(league_links[0]) if league_links else None

    record = GameRecord(
        game_id=game_id,
        title=title,
        game_date=game_date,
        season=season,
        competition_type=competition_type,
        away_team_id=away_team_id,
        home_team_id=home_team_id,
        league_id=league_id,
    )

    rows = re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL)
    for r in rows:
        if "../players/player_" not in r:
            continue

        player_id_m = re.search(r"../players/player_(\d+)\.html", r)
        if not player_id_m:
            continue
        pid = int(player_id_m.group(1))

        cols = [re.sub(r"<[^>]+>", "", cell).strip() for cell in re.findall(r"<td[^>]*>(.*?)</td>", r, re.DOTALL)]
        if len(cols) == 11:
            # Check if batting line (Cols: Name, AB, R, H, RBI, BB, K, LOB, AVG, HR, SB)
            try:
                name = cols[0]
                ab = int(cols[1])
                r_val = int(cols[2])
                h_val = int(cols[3])
                rbi = int(cols[4])
                bb = int(cols[5])
                so = int(cols[6])
                lob = int(cols[7])
                hr = int(cols[9])
                sb = int(cols[10])
                record.batting_lines.append(
                    BattingLine(
                        player_id=pid,
                        name=name,
                        ab=ab,
                        r=r_val,
                        h=h_val,
                        rbi=rbi,
                        bb=bb,
                        so=so,
                        lob=lob,
                        hr=hr,
                        sb=sb,
                    )
                )
            except ValueError:
                # Might be pitching line if format matches
                pass
        if len(cols) >= 10:
            # Check if pitching line (Cols: Name, IP, H, R, ER, BB, K, HR, BF, Pitches, ERA)
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

                record.pitching_lines.append(
                    PitchingLine(
                        player_id=pid,
                        name=name,
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

    return record


if __name__ == "__main__":
    save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
    box_dir = save_dir / "news" / "html" / "box_scores"

    sample_files = [box_dir / "game_box_1.html", box_dir / "game_box_10.html", box_dir / "game_box_999.html"]
    for sample in sample_files:
        rec = parse_game_box(sample)
        print(f"=== Parsed Game {rec.game_id} ({rec.game_date}) ===")
        print(f"  Title: {rec.title}")
        print(f"  Away Team: {rec.away_team_id}, Home Team: {rec.home_team_id}, League: {rec.league_id}")
        print(f"  Batting lines count: {len(rec.batting_lines)}")
        print(f"  Pitching lines count: {len(rec.pitching_lines)}")
        if rec.batting_lines:
            b0 = rec.batting_lines[0]
            print(f"  Sample Batter: PID={b0.player_id} {b0.name} AB={b0.ab} H={b0.h} HR={b0.hr} RBI={b0.rbi}")
        if rec.pitching_lines:
            p0 = rec.pitching_lines[0]
            print(f"  Sample Pitcher: PID={p0.player_id} {p0.name} Outs={p0.outs} H={p0.h} SO={p0.so} Win={p0.win}")
