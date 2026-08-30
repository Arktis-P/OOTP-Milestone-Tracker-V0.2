from __future__ import annotations

from pathlib import Path

SOURCE_PATTERNS = {
    "rosters": "*_rosters.txt",
    "player_stats": "player_*_stats.txt",
    "messages": "message*.txt",
    "game_boxes": "game_box_*.html",
    "logs": "log_*.txt",
}


def scan_league_save(save_path: str | Path, sample_limit: int = 5) -> dict:
    root = Path(save_path)
    if not root.is_dir() or not root.name.lower().endswith(".lg"):
        raise ValueError(f"Expected an existing .lg directory: {root}")

    categories: dict[str, dict] = {}
    for category, pattern in SOURCE_PATTERNS.items():
        files = [path for path in root.rglob(pattern) if path.is_file()]
        files.sort(key=_mtime, reverse=True)
        categories[category] = {
            "pattern": pattern,
            "count": len(files),
            "total_bytes": sum(_size(path) for path in files),
            "newest": _relative(files[0], root) if files else None,
            "samples": [_relative(path, root) for path in files[:sample_limit]],
        }

    return {
        "save_name": root.name,
        "save_path": str(root),
        "categories": categories,
    }


def _relative(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _mtime(path: Path) -> float:
    try:
        return path.stat().st_mtime
    except OSError:
        return 0.0


def _size(path: Path) -> int:
    try:
        return path.stat().st_size
    except OSError:
        return 0
