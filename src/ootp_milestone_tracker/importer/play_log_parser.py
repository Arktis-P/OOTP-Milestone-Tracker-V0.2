import re
from pathlib import Path
from typing import List, Optional

from .game_models import PlayEvent


def parse_play_log(file_path: Path) -> List[PlayEvent]:
    game_id_m = re.search(r"log_(\d+)\.txt", file_path.name)
    game_id = int(game_id_m.group(1)) if game_id_m else 0

    content = file_path.read_text(encoding="utf-8-sig", errors="replace")
    lines = content.splitlines()

    events: List[PlayEvent] = []
    seq = 0

    current_inning = 1
    current_half = "top"
    current_pitcher_id: Optional[int] = None
    current_batter_id: Optional[int] = None
    score_home = 0
    score_away = 0
    outs_before = 0

    for line in lines:
        line_str = line.strip()

        # [%T]: Inning & Pitcher Header
        if line_str.startswith("[%T]"):
            top_m = re.search(r"(Top|Bottom)\s+of\s+the\s+(\d+)", line_str, re.IGNORECASE)
            if top_m:
                current_half = top_m.group(1).lower()
                current_inning = int(top_m.group(2))
                outs_before = 0

            pitcher_m = re.search(r"Pitching\s+for.*?player_(\d+)\.html", line_str)
            if pitcher_m:
                current_pitcher_id = int(pitcher_m.group(1))
            continue

        # [%B]: Pitcher change or Batter entry
        if line_str.startswith("[%B]"):
            batter_m = re.search(r"Batting:.*?player_(\d+)\.html", line_str)
            if batter_m:
                current_batter_id = int(batter_m.group(1))

            pitcher_m = re.search(r"Pitching:.*?player_(\d+)\.html", line_str)
            if pitcher_m:
                current_pitcher_id = int(pitcher_m.group(1))
            continue

        # [%F]: Inning End / Running Score
        if line_str.startswith("[%F]"):
            # e.g., Miami 0 - Seoul 2
            scores_m = re.findall(r"(\d+)", line_str)
            if len(scores_m) >= 2:
                # Last two integers in summary line are running scores
                score_away = int(scores_m[-2])
                score_home = int(scores_m[-1])
            outs_before = 0
            continue

        # [%N]: Pitch & Play Result Line
        if line_str.startswith("[%N]"):
            # Check play result tags like <b>HOME RUN</b>, <b>DOUBLE</b>, <b>TRIPLE</b>, etc.
            clean_text = re.sub(r"\[%N\]\s*\d+-\d+:\s*", "", line_str).strip()
            text_plain = re.sub(r"<[^>]+>", "", clean_text)

            result_code = "OTHER"
            if "HOME RUN" in clean_text.upper():
                result_code = "HR"
            elif "DOUBLE" in clean_text.upper():
                result_code = "2B"
            elif "TRIPLE" in clean_text.upper():
                result_code = "3B"
            elif "SINGLE" in clean_text.upper():
                result_code = "1B"
            elif "STRIKES OUT" in clean_text.upper() or "STRIKEOUT" in clean_text.upper():
                result_code = "K"
            elif "WALK" in clean_text.upper() or "WALKS" in clean_text.upper():
                result_code = "BB"

            # Check for Grand Slam text: "HOME RUN" and "Grand Slam" or "bases loaded"
            if "GRAND SLAM" in clean_text.upper():
                result_code = "GRAND_SLAM"

            if current_batter_id and current_pitcher_id and (result_code != "OTHER" or "out" in text_plain.lower()):
                seq += 1
                events.append(
                    PlayEvent(
                        game_id=game_id,
                        sequence=seq,
                        inning=current_inning,
                        half=current_half,
                        batter_id=current_batter_id,
                        pitcher_id=current_pitcher_id,
                        outs_before=outs_before,
                        score_home=score_home,
                        score_away=score_away,
                        result_code=result_code,
                        text=text_plain,
                    )
                )

                if "out" in text_plain.lower() and "no out" not in text_plain.lower():
                    outs_before = min(outs_before + 1, 2)

    return events
