import os
import re
from pathlib import Path

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
msg_dir = save_dir / "messages"

print("Searching messages for playoff/championship evidence...")
keywords = ["clinched", "division", "postseason", "playoff", "world series", "championship", "pennant", "wild card"]

found_msgs = []

if msg_dir.exists():
    for f in msg_dir.glob("message*.txt"):
        txt = f.read_text(encoding="utf-8", errors="replace")
        for kw in keywords:
            if kw in txt.lower():
                found_msgs.append((f.name, kw, txt[:300].replace("\n", " ")))
                break

print(f"Found {len(found_msgs)} matching messages.")
for name, kw, snippet in found_msgs[:20]:
    print(f"[{name}] Keyword '{kw}': {snippet}")
