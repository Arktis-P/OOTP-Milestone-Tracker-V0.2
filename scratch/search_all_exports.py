import os
from pathlib import Path

user_docs = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27")

print(f"Searching in {user_docs}...")
if user_docs.exists():
    for root, dirs, files in os.walk(user_docs):
        if "box_scores" in root or "logs" in root or "messages" in root or "coaches" in root:
            continue
        for f in files:
            if f.endswith(".csv") or f.endswith(".txt") or f.endswith(".html"):
                if any(k in f.lower() for k in ["batting", "pitching", "player", "export", "stats", "roster", "league"]):
                    p = Path(root) / f
                    print(f"Found: {p} ({p.stat().st_size} bytes)")
