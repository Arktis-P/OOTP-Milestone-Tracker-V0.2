import os
import re
from pathlib import Path

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")

print("Checking team stats HTML and import_export folder...")
ie_dir = save_dir / "import_export"
if ie_dir.exists():
    print(f"Files in import_export: {list(ie_dir.glob('*'))}")

team_stat_htmls = list((save_dir / "news" / "html" / "teams").glob("*_stats_*.html"))
print(f"Found {len(team_stat_htmls)} team stat HTML files.")
if team_stat_htmls:
    sample = team_stat_htmls[0]
    print(f"Sample: {sample.name}")
    txt = sample.read_text(encoding="utf-8", errors="replace")
    rows = re.findall(r"<tr>(.*?)</tr>", txt, re.DOTALL)
    for r in rows[:10]:
        cols = [re.sub(r"<[^>]+>", "", cell).strip() for cell in re.findall(r"<td[^>]*>(.*?)</td>", r, re.DOTALL)]
        if cols:
            print("  Cols:", cols)
