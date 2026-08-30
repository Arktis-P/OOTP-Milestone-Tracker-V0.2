from __future__ import annotations

import os
from pathlib import Path


def _documents_dir() -> Path:
    """Resolve the current Windows Documents location without hard-coded user/localized names."""
    if os.name == "nt":
        try:
            import winreg

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path) as key:
                value, _ = winreg.QueryValueEx(key, "Personal")
            return Path(os.path.expandvars(value)).expanduser()
        except (OSError, ImportError):
            pass
    return Path.home() / "Documents"


def saved_games_roots() -> list[Path]:
    suffix = Path("Out of the Park Developments") / "OOTP Baseball 27" / "saved_games"
    candidates = [_documents_dir() / suffix, Path.home() / "Documents" / suffix]

    onedrive = os.environ.get("OneDrive") or os.environ.get("OneDriveConsumer")
    if onedrive:
        candidates.append(Path(onedrive) / "Documents" / suffix)

    unique: list[Path] = []
    seen: set[str] = set()
    for path in candidates:
        key = str(path).casefold()
        if key not in seen:
            unique.append(path)
            seen.add(key)
    return unique


def discover_league_saves(root: str | Path | None = None) -> list[Path]:
    roots = [Path(root)] if root else saved_games_roots()
    saves: list[Path] = []
    for base in roots:
        if not base.is_dir():
            continue
        try:
            saves.extend(path for path in base.iterdir() if path.is_dir() and path.name.lower().endswith(".lg"))
        except OSError:
            continue

    def modified(path: Path) -> float:
        try:
            return path.stat().st_mtime
        except OSError:
            return 0.0

    return sorted(saves, key=modified, reverse=True)


def default_league_save() -> Path | None:
    saves = discover_league_saves()
    return saves[0] if saves else None
