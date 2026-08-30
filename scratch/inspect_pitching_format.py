from pathlib import Path

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
p_file = save_dir / "import_export" / "player_pitching_stats.txt"

lines = p_file.read_text(encoding="utf-8", errors="replace").splitlines()
comments = [l for l in lines if l.startswith("//")]
for c in comments[-15:]:
    print("  ", c)
