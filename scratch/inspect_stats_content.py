from pathlib import Path

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
ie_dir = save_dir / "import_export"

b_file = ie_dir / "player_batting_stats.txt"
p_file = ie_dir / "player_pitching_stats.txt"

if b_file.exists():
    print("=== PLAYER BATTING STATS CONTENT ===")
    lines = b_file.read_text(encoding="utf-8", errors="replace").splitlines()
    non_comment_lines = [l for l in lines if not l.startswith("//")]
    print("Non-comment line count:", len(non_comment_lines))
    if non_comment_lines:
        print("Header (Line 0):", non_comment_lines[0])
        print("Data 1:", non_comment_lines[1])
        print("Data 2:", non_comment_lines[2])

if p_file.exists():
    print("\n=== PLAYER PITCHING STATS CONTENT ===")
    lines = p_file.read_text(encoding="utf-8", errors="replace").splitlines()
    non_comment_lines = [l for l in lines if not l.startswith("//")]
    print("Non-comment line count:", len(non_comment_lines))
    if non_comment_lines:
        print("Header (Line 0):", non_comment_lines[0])
        print("Data 1:", non_comment_lines[1])
        print("Data 2:", non_comment_lines[2])
