import os
from pathlib import Path

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")

print("Searching for csv/txt export files in save dir...")
for root, dirs, files in os.walk(save_dir):
    for f in files:
        if f.endswith(".txt") or f.endswith(".csv"):
            if "stat" in f.lower() or "player" in f.lower() or "export" in f.lower() or "message" in f.lower():
                rel_path = Path(root) / f
                print(f"Found: {rel_path.relative_to(save_dir)} ({rel_path.stat().st_size} bytes)")
