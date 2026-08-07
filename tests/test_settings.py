"""
Unit tests for Settings Model & Path Management (Phase 0.2)
"""

import os
import shutil
import tempfile
import pytest
from core.config.settings import Settings, SettingsManager


@pytest.fixture
def temp_dir():
    d = tempfile.mkdtemp()
    yield d
    shutil.rmtree(d, ignore_errors=True)


def test_settings_save_and_load(temp_dir):
    mgr = SettingsManager(config_dir=temp_dir)
    settings = Settings(
        active_save_path="C:/OOTP/Saves/League1.lg",
        current_season=2027,
        tracked_teams=["NYY", "LAD"],
    )
    mgr.save(settings)

    loaded = mgr.load()
    assert loaded.active_save_path == "C:/OOTP/Saves/League1.lg"
    assert loaded.current_season == 2027
    assert loaded.tracked_teams == ["NYY", "LAD"]


def test_save_key_stability_and_isolation(temp_dir):
    mgr = SettingsManager(config_dir=temp_dir)
    s1 = Settings(active_save_path="C:/OOTP/Saves/League1.lg", league_id="lg_1")
    s2 = Settings(active_save_path="C:/OOTP/Saves/League2.lg", league_id="lg_1")
    s3 = Settings(active_save_path="c:/ootp/saves/league1.lg", league_id="LG_1")

    assert s1.save_key != s2.save_key
    assert s1.save_key == s3.save_key  # case insensitive normalization


def test_derived_paths_and_readiness(temp_dir):
    mgr = SettingsManager(config_dir=temp_dir)

    # Create dummy save structure
    save_path = os.path.join(temp_dir, "MySave.lg")
    box_dir = os.path.join(save_path, "news", "html", "box_scores")
    os.makedirs(box_dir, exist_ok=True)

    settings = Settings(active_save_path=save_path)
    paths = mgr.get_derived_paths(settings)

    assert paths.boxscores_dir == box_dir
    assert os.path.basename(paths.db_path) == "records.db"

    readiness = mgr.check_readiness(settings)
    assert readiness["is_ready"] is True
    assert readiness["save_path_exists"] is True
    assert readiness["boxscores_dir_exists"] is True
