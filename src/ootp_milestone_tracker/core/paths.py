from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = REPO_ROOT / "data"
RUNTIME_DIR = DATA_DIR / "runtime"
SAMPLE_SAVE_DIR = DATA_DIR / "samples" / "ootp_save"
BUILDS_DIR = REPO_ROOT / "artifacts" / "builds"
DEFAULT_DB_PATH = RUNTIME_DIR / "tracker.db"


def ensure_runtime_dirs() -> None:
    for path in (RUNTIME_DIR, SAMPLE_SAVE_DIR, BUILDS_DIR):
        path.mkdir(parents=True, exist_ok=True)
