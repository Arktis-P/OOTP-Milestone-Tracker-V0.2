import pytest
from ootp_milestone_tracker.db.database import Database
from ootp_milestone_tracker.db.repository import Repository


@pytest.fixture
def repo(tmp_path):
    db_path = tmp_path / "test_tracker.db"
    db = Database(db_path)
    db.initialize()
    return Repository(db)


def test_db_initialization_and_seed_count(repo):
    teams = repo.teams()
    players = repo.players()
    tracked = repo.tracked_team()

    assert len(teams) == 3
    assert len(players) == 8
    assert tracked is not None
    assert tracked["name"] == "Seoul Meteors"


def test_tracked_team_milestone_filtering(repo):
    tracked_milestones = repo.milestones(tracked_only=True)
    all_milestones = repo.milestones(tracked_only=False)

    assert len(tracked_milestones) > 0
    assert len(all_milestones) >= len(tracked_milestones)
    for m in tracked_milestones:
        assert m["team_name"] == "Seoul Meteors"


def test_team_switch_behavior(repo):
    teams = repo.teams()
    other_team = next(t for t in teams if not t["is_tracked"])
    
    repo.set_tracked_team(other_team["id"])
    new_tracked = repo.tracked_team()
    summary = repo.dashboard_summary()

    assert new_tracked["id"] == other_team["id"]
    assert new_tracked["name"] == other_team["name"]
    assert summary["team"] == other_team["name"]


def test_player_name_mapping_persistence(repo):
    players = repo.players()
    target_player = players[0]
    new_name = "테스트선수"

    repo.update_name_mapping(target_player["id"], new_name)
    updated = repo.player(target_player["id"])

    assert updated["name_ko"] == new_name
