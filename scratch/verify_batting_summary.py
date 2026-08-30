import re
from pathlib import Path

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
box_dir = save_dir / "news" / "html" / "box_scores"

box_files = sorted(box_dir.glob("game_box_*.html"))

print(f"Total box files to inspect: {len(box_files)}")

categories_found = set()
hr_samples = []
doubles_samples = []
triples_samples = []
sb_samples = []

for f in box_files[:100]:
    html = f.read_text(encoding="utf-8", errors="replace")
    
    # Extract lower BATTING section text
    # In OOTP box scores, lower section has <th ...>BATTING</th> or text blocks
    if "BATTING<br>" in html or "BATTING\n" in html or "BATTING" in html:
        # Find BATTING text block
        m = re.search(r"<td[^>]*class=[\"\']databg[\"\'][^>]*>(.*?)</td>", html, re.DOTALL)
        # Search for category headers inside the HTML
        for cat in ["Doubles:", "Triples:", "Home Runs:", "Total Bases:", "2-out RBI:", "Runners left in scoring position", "Sac Fly:", "Sac Bunt:", "Stolen Bases:"]:
            if cat in html:
                categories_found.add(cat)
        
        # Sample HR text
        hr_m = re.search(r"Home Runs:\s*<br>(.*?)(?:<br><br>|<br>\s*<span|<td|$)", html, re.DOTALL)
        if not hr_m:
            hr_m = re.search(r"Home Runs:\s*\n?(.*?)(?:\n\n|\n[A-Z\s]+:|$)", html, re.DOTALL)
        if hr_m and len(hr_samples) < 10:
            text = re.sub(r"<[^>]+>", "", hr_m.group(1)).strip()
            if text:
                hr_samples.append((f.name, text))
                
        # Sample Doubles
        db_m = re.search(r"Doubles:\s*<br>(.*?)(?:<br><br>|<br>\s*<span|<td|$)", html, re.DOTALL)
        if not db_m:
            db_m = re.search(r"Doubles:\s*\n?(.*?)(?:\n\n|\n[A-Z\s]+:|$)", html, re.DOTALL)
        if db_m and len(doubles_samples) < 5:
            text = re.sub(r"<[^>]+>", "", db_m.group(1)).strip()
            if text:
                doubles_samples.append((f.name, text))

        # Sample SB
        sb_m = re.search(r"Stolen Bases:\s*<br>(.*?)(?:<br><br>|<br>\s*<span|<td|$)", html, re.DOTALL)
        if not sb_m:
            sb_m = re.search(r"SB:\s*<br>(.*?)(?:<br><br>|<br>\s*<span|<td|$)", html, re.DOTALL)
        if sb_m and len(sb_samples) < 5:
            text = re.sub(r"<[^>]+>", "", sb_m.group(1)).strip()
            if text:
                sb_samples.append((f.name, text))

print("Categories found in HTML:", categories_found)
print("\n--- HR Samples ---")
for fn, s in hr_samples:
    print(f"[{fn}] {s}")

print("\n--- Doubles Samples ---")
for fn, s in doubles_samples:
    print(f"[{fn}] {s}")

print("\n--- SB Samples ---")
for fn, s in sb_samples:
    print(f"[{fn}] {s}")
