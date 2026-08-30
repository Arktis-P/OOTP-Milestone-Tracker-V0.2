from __future__ import annotations

import argparse
import json
from pathlib import Path

from ootp_milestone_tracker.importer.source_locator import discover_league_saves, saved_games_roots
from ootp_milestone_tracker.importer.source_scanner import scan_league_save


def main() -> int:
    parser = argparse.ArgumentParser(description="Inventory OOTP 27 source files without modifying the save.")
    parser.add_argument("save", nargs="?", help="Optional path to one .lg save directory")
    parser.add_argument("--all", action="store_true", help="Scan every discovered .lg save instead of only the newest")
    parser.add_argument("--output", help="Optional JSON output path")
    args = parser.parse_args()

    if args.save:
        saves = [Path(args.save)]
    else:
        saves = discover_league_saves()
        if not saves:
            payload = {
                "saved_games_candidates": [str(path) for path in saved_games_roots()],
                "saves": [],
                "error": "No .lg save directories discovered.",
            }
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 2
        if not args.all:
            saves = saves[:1]

    payload = {
        "saved_games_candidates": [str(path) for path in saved_games_roots()],
        "saves": [scan_league_save(path) for path in saves],
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2)
    print(text)
    if args.output:
        output = Path(args.output)
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
