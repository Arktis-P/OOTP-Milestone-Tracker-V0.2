import re
from pathlib import Path

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
log_dir = save_dir / "news" / "txt" / "leagues"

log_files = sorted(log_dir.glob("log_*.txt"))
print(f"Total log files: {len(log_files)}")

for sample in log_files[:3]:
    print(f"\n=== File: {sample.name} ===")
    content = sample.read_text(encoding="utf-8-sig", errors="replace")
    lines = content.splitlines()[:20]
    for line in lines:
        print(line)
