import re
from pathlib import Path
from ootp_milestone_tracker.importer.game_box_parser import parse_game_box

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
box_dir = save_dir / "news" / "html" / "box_scores"

box_files = sorted(box_dir.glob("game_box_*.html"))

print("=== Audit B: Perfect Game Proof Check ===")

for f in box_files:
    rec = parse_game_box(f)
    for p in rec.pitching_lines:
        if p.outs >= 27 and p.win and p.h == 0 and p.r == 0:
            print(f"\nFound Complete Game No-Hit/Shutout Pitcher in [{f.name}] Date: {rec.game_date}")
            print(f"  Pitcher: {p.name} (PID: {p.player_id})")
            print(f"  Outs: {p.outs} (Innings: {p.outs/3.0:.1f})")
            print(f"  Batters Faced (BF): {p.bf}")
            print(f"  Hits (H): {p.h}, Runs (R): {p.r}, ER: {p.er}, Walks (BB): {p.bb}, Strikeouts (SO): {p.so}")
            
            is_perfect = (p.outs >= 27) and (p.bf == p.outs) and (p.h == 0) and (p.r == 0) and (p.bb == 0)
            print(f"  Deterministic Perfect Game Proof (BF == outs): {is_perfect}")
