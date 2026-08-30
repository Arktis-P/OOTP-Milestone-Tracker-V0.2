import time
from collections import Counter
from pathlib import Path
import sys

from ootp_milestone_tracker.importer.game_box_parser import parse_game_box
from ootp_milestone_tracker.milestones.game_evaluator import GameMilestoneEvaluator

save_dir = Path(r"C:\Users\cwson\OneDrive\문서\Out of the Park Developments\OOTP Baseball 27\saved_games\SuperYukies_V1.0.lg")
box_dir = save_dir / "news" / "html" / "box_scores"

box_files = sorted(box_dir.glob("game_box_*.html"))
print(f"Starting Real-Save Exhaustive Scan over {len(box_files)} game box files...")

evaluator = GameMilestoneEvaluator()

games_scanned = 0
parse_failures = 0
achievements_detected = 0

rule_counts = Counter()
samples_per_rule = {}

t0 = time.time()

for f in box_files:
    try:
        rec = parse_game_box(f)
        games_scanned += 1
        achs = evaluator.evaluate_game(rec)
        if achs:
            achievements_detected += len(achs)
            for a in achs:
                rule_counts[a.rule_key] += 1
                if a.rule_key not in samples_per_rule:
                    samples_per_rule[a.rule_key] = (f.name, rec.game_date, a.title, a.achieved_value, a.context_text)
    except Exception as e:
        parse_failures += 1

t1 = time.time()
print(f"\n--- REAL SAVE SCAN SUMMARY (Time: {t1-t0:.2f}s) ---")
print(f"Games scanned: {games_scanned}")
print(f"Parse failures: {parse_failures}")
print(f"Total achievements detected: {achievements_detected}")

print("\nAchievement Counts per Rule/Family:")
for rule_key, count in rule_counts.most_common():
    sample_info = samples_per_rule.get(rule_key, "")
    print(f"  {rule_key:28s}: {count:5d}  (Sample: {sample_info})")
