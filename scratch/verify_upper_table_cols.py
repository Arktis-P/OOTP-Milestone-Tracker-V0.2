import re
from pathlib import Path

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
box_dir = save_dir / "news" / "html" / "box_scores"

box_files = sorted(box_dir.glob("game_box_*.html"))

print("=== Comparing Upper Table Col 9/10 with Lower Summary ===")

for f in box_files[:50]:
    html = f.read_text(encoding="utf-8", errors="replace")
    
    # Check lower HR summary
    hr_players = {}
    hr_block = re.search(r"Home Runs:\s*<br>(.*?)(?:<br><br>|<br>\s*<span|<td|Total Bases:|$)", html, re.DOTALL)
    if hr_block:
        # find player IDs and counts
        hr_matches = re.findall(r"../players/player_(\d+)\.html.*?>(.*?)</a>\s*(\d+)?\s*\((.*?)\)", hr_block.group(1), re.DOTALL)
        for pid, name, count_str, info in hr_matches:
            cnt = int(count_str) if count_str.strip() else 1
            hr_players[pid] = (name.strip(), cnt, info.strip())

    # Check upper table rows
    player_rows = re.findall(r"<tr>(.*?)</tr>", html, re.DOTALL)
    for r in player_rows:
        if "../players/player_" in r:
            pid_m = re.search(r"../players/player_(\d+)\.html", r)
            if not pid_m:
                continue
            pid = pid_m.group(1)
            cols = [re.sub(r"<[^>]+>", "", cell).strip() for cell in re.findall(r"<td[^>]*>(.*?)</td>", r, re.DOTALL)]
            if len(cols) == 11 and pid in hr_players:
                name_u, ab, r_u, h, rbi, bb, k, lob, avg, col9, col10 = cols
                pname, hr_cnt, hr_info = hr_players[pid]
                print(f"[{f.name}] PID {pid} ({pname}): Upper Col9='{col9}', Col10='{col10}' | Lower Text HR count={hr_cnt}, Info='{hr_info}'")
