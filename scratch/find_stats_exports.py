import os
from pathlib import Path

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")

print("Searching non-message CSV/TXT files in save_dir...")
for root, dirs, files in os.walk(save_dir):
    if "messages" in root:
        continue
    for f in files:
        if f.endswith(".txt") or f.endswith(".csv"):
            rel_path = Path(root) / f
            print(f"Found: {rel_path.relative_to(save_dir)} ({rel_path.stat().st_size} bytes)")
