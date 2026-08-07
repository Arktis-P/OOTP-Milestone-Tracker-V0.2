"""
Unit tests for Season Isolation Validation Engine (Phase 14.4)
"""

import os
import pytest
from core.db.connection import DatabaseManager
from core.validation.season_validator import SeasonValidator

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")


def test_season_isolation_validation(tmp_path):
    op_db_path = str(tmp_path / "operating.db")
    op_mgr = DatabaseManager(op_db_path)
    op_mgr.initialize_database()

    validator = SeasonValidator(
        operating_db_path=op_db_path,
        boxscores_dir=FIXTURES_DIR,
        import_export_dir=FIXTURES_DIR
    )

    res = validator.validate_season(2027)
    assert "is_match" in res
    assert res["validation_game_count"] >= 1
    assert os.path.exists(op_db_path)  # Operating DB remains intact
