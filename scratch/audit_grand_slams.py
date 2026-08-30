import re
from pathlib import Path
from ootp_milestone_tracker.importer.game_box_parser import parse_game_box
from ootp_milestone_tracker.milestones.game_evaluator import GameMilestoneEvaluator

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
box_dir = save_dir / "news" / "html" / "box_scores"

box_files = sorted(box_dir.glob("game_box_*.html"))
evaluator = GameMilestoneEvaluator()

grand_slam_games = []
non_gs_hr_games = []

for f in box_files:
    rec = parse_game_box(f)
    achs = evaluator.evaluate_game(rec)
    gs_achs = [a for a in achs if a.rule_key == "GAME_GRAND_SLAM"]
    hr_events = [ev for ev in rec.batting_events if ev.event_type == "HOME_RUN"]

    if gs_achs:
        grand_slam_games.append((f, rec, gs_achs))
    elif hr_events:
        non_gs_hr_games.append((f, rec, hr_events))

    if len(grand_slam_games) >= 20 and len(non_gs_hr_games) >= 20:
        break

print(f"Sampled {len(grand_slam_games)} Grand Slam games and {len(non_gs_hr_games)} Non-GS HR games.\n")

print("=== Audit A1: Grand Slam Positives Sample Check ===")
gs_false_positives = 0
for idx, (f, rec, achs) in enumerate(grand_slam_games[:20], 1):
    html = f.read_text(encoding="utf-8", errors="replace")
    hr_block = re.search(r"<b>Home Runs:\s*</b>(.*?)(?:<br><b>|<td|Total Bases:|$)", html, re.DOTALL)
    block_text = re.sub(r"<[^>]+>", "", hr_block.group(1)).strip() if hr_block else "N/A"
    
    # Check log file if available
    log_file = save_dir / "news" / "txt" / "leagues" / f"log_{rec.game_id}.txt"
    log_evidence = "N/A"
    if log_file.exists():
        log_txt = log_file.read_text(encoding="utf-8-sig", errors="replace")
        gs_log_m = re.findall(r"\[%N\].*?(?:GRAND SLAM|HOME RUN.*?\b3\b)", log_txt, re.IGNORECASE)
        if gs_log_m:
            log_evidence = gs_log_m[0].strip()
    
    print(f"Sample {idx:02d} [{f.name}] Game {rec.game_id} Date: {rec.game_date}")
    print(f"   HR Summary Text: {block_text}")
    print(f"   Log Evidence: {log_evidence}")

print("\n=== Audit A2: Non-Grand Slam HR Negatives Sample Check ===")
gs_false_negatives = 0
for idx, (f, rec, hr_evs) in enumerate(non_gs_hr_games[:20], 1):
    html = f.read_text(encoding="utf-8", errors="replace")
    hr_block = re.search(r"<b>Home Runs:\s*</b>(.*?)(?:<br><b>|<td|Total Bases:|$)", html, re.DOTALL)
    block_text = re.sub(r"<[^>]+>", "", hr_block.group(1)).strip() if hr_block else "N/A"
    
    # Verify no '3 on' exists in block_text for this HR
    has_3on = "3 on" in block_text
    print(f"Sample {idx:02d} [{f.name}] Has '3 on': {has_3on} | Summary Text: {block_text[:120]}")
    if has_3on:
        gs_false_negatives += 1

print(f"\nResult: False Positives = {gs_false_positives}, False Negatives = {gs_false_negatives}")
