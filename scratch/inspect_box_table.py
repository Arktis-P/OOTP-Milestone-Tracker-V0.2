import re
from pathlib import Path

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
box_file = save_dir / "news" / "html" / "box_scores" / "game_box_1.html"

html = box_file.read_text(encoding="utf-8", errors="replace")

print("=== Batting & Pitching Rows Excerpt ===")
player_rows = re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL)
for r in player_rows:
    if "../players/player_" in r:
        player_id_m = re.search(r"../players/player_(\d+)\.html", r)
        pid = player_id_m.group(1) if player_id_m else "N/A"
        cols = [re.sub(r"<[^>]+>", "", cell).strip() for cell in re.findall(r"<td[^>]*>(.*?)</td>", r, re.DOTALL)]
        if cols:
            print(f"PID: {pid:6s} Cols: {cols}")
