from typing import Dict
from ootp_milestone_tracker.db.repository import Repository


class ResetService:
    def __init__(self, repository: Repository):
        self.repo = repository

    def reset_history_tracking(self, preserve_manual: bool = True) -> Dict[str, int]:
        counts = {}
        with self.repo.database.connect() as conn:
            # 1. Injury episode events & episodes
            counts["injury_episode_events"] = conn.execute("DELETE FROM injury_episode_events").rowcount
            counts["injury_episodes"] = conn.execute("DELETE FROM injury_episodes").rowcount

            # 2. Transaction participants & events
            counts["transaction_participants"] = conn.execute("DELETE FROM transaction_participants").rowcount
            counts["transaction_events"] = conn.execute("DELETE FROM transaction_events").rowcount

            # 3. Player history events
            if preserve_manual:
                counts["player_history_events"] = conn.execute(
                    "DELETE FROM player_history_events WHERE source_family = 'MESSAGES'"
                ).rowcount
            else:
                counts["player_history_events"] = conn.execute("DELETE FROM player_history_events").rowcount

            conn.commit()
        return counts

    def reset_all_tracking(self) -> Dict[str, int]:
        counts = {}
        with self.repo.database.connect() as conn:
            # History & Transactions
            counts["injury_episode_events"] = conn.execute("DELETE FROM injury_episode_events").rowcount
            counts["injury_episodes"] = conn.execute("DELETE FROM injury_episodes").rowcount
            counts["transaction_participants"] = conn.execute("DELETE FROM transaction_participants").rowcount
            counts["transaction_events"] = conn.execute("DELETE FROM transaction_events").rowcount
            counts["player_history_events"] = conn.execute("DELETE FROM player_history_events").rowcount

            # Milestones & Achievements
            counts["career_milestone_achievements"] = conn.execute("DELETE FROM career_milestone_achievements").rowcount
            counts["career_checkpoints"] = conn.execute("DELETE FROM career_checkpoints").rowcount
            counts["season_milestone_achievements"] = conn.execute("DELETE FROM season_milestone_achievements").rowcount
            counts["game_milestone_achievements"] = conn.execute("DELETE FROM game_milestone_achievements").rowcount

            # Game Ledger
            counts["game_batting_events"] = conn.execute("DELETE FROM game_batting_events").rowcount
            counts["player_game_pitching"] = conn.execute("DELETE FROM player_game_pitching").rowcount
            counts["player_game_batting"] = conn.execute("DELETE FROM player_game_batting").rowcount
            counts["games"] = conn.execute("DELETE FROM games").rowcount

            conn.commit()
        return counts
