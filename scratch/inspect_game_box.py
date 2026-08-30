import re
from pathlib import Path

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
box_dir = save_dir / "news" / "html" / "box_scores"

box_files = sorted(box_dir.glob("game_box_*.html"))
print(f"Total box files: {len(box_files)}")

for sample_file in [box_files[0], box_files[len(box_files)//2], box_files[-1]]:
    print(f"\n=== File: {sample_file.name} ===")
    html = sample_file.read_text(encoding="utf-8", errors="replace")
    
    # Title
    title_m = re.search(r"<title>(.*?)</title>", html)
    print("Title:", title_m.group(1) if title_m else "None")
    
    # Team links: e.g. ../teams/team_10.html
    team_links = re.findall(r"../teams/team_(\d+)\.html", html)
    team_links_unique = list(dict.fromkeys(team_links))
    print("Team IDs in HTML links:", team_links_unique)
    
    # League links: e.g. ../leagues/league_100_home.html
    league_links = re.findall(r"../leagues/league_(\d+)_", html)
    print("League IDs in HTML links:", list(set(league_links)))
    
    # Player links
    player_links = re.findall(r"../players/player_(\d+)\.html", html)
    print("Unique Player IDs count:", len(set(player_links)))

    # Extract first table and lines
    lines = html.splitlines()
    for l in lines:
        if "boxtitle" in l or "sub_header" in l or "section_heading" in l or "databg" in l:
            if len(l.strip()) < 150:
                print("   Sample line:", l.strip())
