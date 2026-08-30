from ootp_milestone_tracker.core.paths import DEFAULT_DB_PATH, ensure_runtime_dirs
from ootp_milestone_tracker.db.database import Database


if __name__ == "__main__":
    ensure_runtime_dirs()
    Database(DEFAULT_DB_PATH).reset_sample()
    print(f"Reset sample DB: {DEFAULT_DB_PATH}")
