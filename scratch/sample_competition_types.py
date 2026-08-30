import re
from pathlib import Path
from collections import Counter

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
box_dir = save_dir / "news" / "html" / "box_scores"

box_files = sorted(box_dir.glob("game_box_*.html"))

title_prefixes = Counter()
dates = []
leagues = Counter()

for f in box_files[:1000]: # Sample 1000 files
    html = f.read_text(encoding="utf-8", errors="replace")
    title_m = re.search(r"<title>(.*?)</title>", html)
    if title_m:
        title = title_m.group(1)
        prefix = title.split(",")[0] if "," in title else title
        title_prefixes[prefix] += 1
        
        # Check league link
        lg_m = re.findall(r"../leagues/league_(\d+)_", html)
        for l in lg_m:
            leagues[l] += 1

print("Sample 1000 Box Score Title Prefixes:")
for k, v in title_prefixes.most_common(20):
    print(f"  {k}: {v}")

print("\nLeague IDs in sample:")
for k, v in leagues.most_common(20):
    print(f"  League {k}: {v}")
