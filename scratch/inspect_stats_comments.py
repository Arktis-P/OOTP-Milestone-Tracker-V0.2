from pathlib import Path

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
ie_dir = save_dir / "import_export"

b_file = ie_dir / "player_batting_stats.txt"
p_file = ie_dir / "player_pitching_stats.txt"

if b_file.exists():
    print("=== PLAYER BATTING STATS COMMENT LINES ===")
    lines = b_file.read_text(encoding="utf-8", errors="replace").splitlines()
    comments = [l for l in lines if l.startswith("//")]
    for c in comments[:20]:
        print("  ", c)
    print("...")
    for c in comments[-10:]:
        print("  ", c)

if p_file.exists():
    print("\n=== PLAYER PITCHING STATS COMMENT LINES ===")
    lines = p_file.read_text(encoding="utf-8", errors="replace").splitlines()
    comments = [l for l in lines if l.startswith("//")]
    for c in comments[:20]:
        print("  ", c)
