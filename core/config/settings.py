"""
Settings Model & Save Path Management
Handles app configuration, save key hashing, derived paths, and readiness checking.
"""

import os
import json
import hashlib
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional

APP_DATA_DIR_NAME = "OOTP_Milestone_Tracker_V0.2"


@dataclass
class Settings:
    active_save_path: str = ""
    league_id: str = "lg_1"
    current_season: int = 2026
    tracked_teams: List[str] = field(default_factory=list)
    mlb_only: bool = True
    ui_language: str = "ko"
    korean_names_enabled: bool = True
    auto_watch_enabled: bool = False
    qualification_ab_per_game: float = 3.1
    qualification_ip_per_game: float = 1.0

    @property
    def save_key(self) -> str:
        """Generates a stable save key hash from normalized save path and league_id."""
        if not self.active_save_path:
            return "default_save"
        norm_path = os.path.normpath(os.path.abspath(self.active_save_path)).lower()
        identity_str = f"{norm_path}|{self.league_id.lower()}"
        return hashlib.sha256(identity_str.encode("utf-8")).hexdigest()[:16]


@dataclass
class DerivedPaths:
    save_key: str
    save_db_dir: str
    db_path: str
    reports_dir: str
    boxscores_dir: str
    messages_dir: str
    import_export_dir: str


class SettingsManager:
    def __init__(self, config_dir: Optional[str] = None):
        if config_dir is None:
            appdata = os.getenv("APPDATA")
            if appdata:
                self.config_dir = os.path.join(appdata, APP_DATA_DIR_NAME)
            else:
                self.config_dir = os.path.join(os.path.expanduser("~"), ".ootp_milestone_tracker")
        else:
            self.config_dir = os.path.abspath(config_dir)

        os.makedirs(self.config_dir, exist_ok=True)
        self.settings_file = os.path.join(self.config_dir, "settings.json")

    def load(self) -> Settings:
        if not os.path.exists(self.settings_file):
            return Settings()
        try:
            with open(self.settings_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            return Settings(**{k: v for k, v in data.items() if k in Settings.__dataclass_fields__})
        except Exception:
            return Settings()

    def save(self, settings: Settings) -> None:
        os.makedirs(self.config_dir, exist_ok=True)
        with open(self.settings_file, "w", encoding="utf-8") as f:
            json.dump(asdict(settings), f, indent=2, ensure_ascii=False)

    def get_derived_paths(self, settings: Settings) -> DerivedPaths:
        save_key = settings.save_key
        save_db_dir = os.path.join(self.config_dir, "saves", save_key)
        db_path = os.path.join(save_db_dir, "records.db")
        reports_dir = os.path.join(save_db_dir, "reports")

        save_root = settings.active_save_path
        if save_root:
            boxscores_dir = os.path.join(save_root, "news", "html", "box_scores")
            messages_dir = os.path.join(save_root, "news", "html", "messages")
            import_export_dir = os.path.join(save_root, "import_export")
        else:
            boxscores_dir = ""
            messages_dir = ""
            import_export_dir = ""

        return DerivedPaths(
            save_key=save_key,
            save_db_dir=save_db_dir,
            db_path=db_path,
            reports_dir=reports_dir,
            boxscores_dir=boxscores_dir,
            messages_dir=messages_dir,
            import_export_dir=import_export_dir,
        )

    def detect_ootp_save_directories(self) -> List[str]:
        """
        Dynamically scans common OOTP saved_games locations on Windows:
        1. Standard Documents
        2. OneDrive Documents (English)
        3. OneDrive Documents (Korean)
        """
        user_home = os.path.expanduser("~")
        candidate_roots = [
            os.path.join(user_home, "Documents", "Out of the Park Developments"),
            os.path.join(user_home, "OneDrive", "Documents", "Out of the Park Developments"),
            os.path.join(user_home, "OneDrive", "문서", "Out of the Park Developments"),
        ]

        found_saves: List[str] = []
        for root in candidate_roots:
            if not os.path.exists(root):
                continue
            for item in os.listdir(root):
                if item.startswith("OOTP Baseball"):
                    saved_games_dir = os.path.join(root, item, "saved_games")
                    if os.path.exists(saved_games_dir):
                        for save_folder in os.listdir(saved_games_dir):
                            if save_folder.endswith(".lg") and not save_folder.startswith("."):
                                full_save_path = os.path.join(saved_games_dir, save_folder)
                                if os.path.isdir(full_save_path):
                                    found_saves.append(os.path.normpath(full_save_path))

        return found_saves

    def check_readiness(self, settings: Settings) -> Dict[str, Any]:
        paths = self.get_derived_paths(settings)
        save_path_exists = bool(settings.active_save_path and os.path.exists(settings.active_save_path))
        boxscores_exists = bool(paths.boxscores_dir and os.path.exists(paths.boxscores_dir))
        messages_exists = bool(paths.messages_dir and os.path.exists(paths.messages_dir))
        import_export_exists = bool(paths.import_export_dir and os.path.exists(paths.import_export_dir))

        is_ready = save_path_exists and (boxscores_exists or import_export_exists)

        return {
            "is_ready": is_ready,
            "save_path_configured": bool(settings.active_save_path),
            "save_path_exists": save_path_exists,
            "boxscores_dir_exists": boxscores_exists,
            "messages_dir_exists": messages_exists,
            "import_export_dir_exists": import_export_exists,
            "save_key": paths.save_key,
            "db_path": paths.db_path,
            "detected_saves": self.detect_ootp_save_directories(),
        }

