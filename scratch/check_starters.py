import re
from pathlib import Path

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
box_file = save_dir / "news" / "html" / "box_scores" / "game_box_1.html"

html = box_file.read_text(encoding="utf-8", errors="replace")

player_rows = re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL)
for r in player_rows:
    if "../players/player_" in r:
        pid_m = re.search(r"../players/player_(\d+)\.html", r)
        pid = pid_m.group(1) if pid_m else "N/A"
        cols = [re.sub(r"<[^>]+>", "", cell).strip() for cell in re.findall(r"<td[^>]*>(.*?)</td>", r, re.DOTALL)]
        if len(cols) == 11:
            raw_name_col = cols[0]
            # Check if substitute indicator exists in raw cell HTML (e.g. &#160; or &nbsp; or a- / b-)
            is_sub = "&#160;" in r or "&nbsp;" in r or re.search(r"\b[a-z]-", raw_name_col) is not None
            print(f"PID: {pid:6s} | Sub: {str(is_sub):5s} | Name: {raw_name_col}")
