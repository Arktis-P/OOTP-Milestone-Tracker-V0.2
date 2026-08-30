from pathlib import Path

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
ie_dir = save_dir / "import_export"

b_file = ie_dir / "player_batting_stats.txt"
p_file = ie_dir / "player_pitching_stats.txt"

if b_file.exists():
    print("=== PLAYER BATTING STATS HEADER & SAMPLE ===")
    lines = b_file.read_text(encoding="utf-8", errors="replace").splitlines()
    print("Line count:", len(lines))
    print("Header line 0:", lines[0])
    if len(lines) > 1:
        print("Sample row 1:", lines[1])
        print("Sample row 2:", lines[2])

if p_file.exists():
    print("\n=== PLAYER PITCHING STATS HEADER & SAMPLE ===")
    lines = p_file.read_text(encoding="utf-8", errors="replace").splitlines()
    print("Line count:", len(lines))
    print("Header line 0:", lines[0])
    if len(lines) > 1:
        print("Sample row 1:", lines[1])
        print("Sample row 2:", lines[2])
