from pathlib import Path
from typing import List, Optional, Tuple

from ..db.database import Database
from ..milestones.game_evaluator import GameMilestoneEvaluator
from .game_box_parser import parse_game_box
from .game_models import GameRecord
from .play_log_parser import parse_play_log


class GameImportService:
    def __init__(self, database: Database, evaluator: Optional[GameMilestoneEvaluator] = None):
        self.database = database
        self.evaluator = evaluator or GameMilestoneEvaluator()

    def import_game(self, record: GameRecord, play_events=None) -> Tuple[bool, int]:
        """Idempotently import a GameRecord and evaluate game milestones into SQLite.
        Returns (is_new_import, achievement_count).
        """
        with self.database.connect() as conn:
            # Check existing game
            row = conn.execute("SELECT game_id FROM games WHERE game_id = ?", (record.game_id,)).fetchone()
            if row:
                return False, 0  # Already imported (idempotent skip)

            # Insert into games table
            conn.execute(
                """INSERT INTO games (game_id, game_date, season, competition_type, league_id,
                home_team_id, away_team_id, home_score, away_score, source_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    record.game_id,
                    record.game_date,
                    record.season,
                    record.competition_type,
                    record.league_id,
                    record.home_team_id,
                    record.away_team_id,
                    record.home_score,
                    record.away_score,
                    record.source_hash,
                ),
            )

            # Insert batting lines
            for b in record.batting_lines:
                conn.execute(
                    """INSERT INTO player_game_batting (game_id, player_id, team_id, ab, r, h, rbi, bb, so, lob, doubles, triples, hr, sb)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record.game_id,
                        b.player_id,
                        b.team_id,
                        b.ab,
                        b.r,
                        b.h,
                        b.rbi,
                        b.bb,
                        b.so,
                        b.lob,
                        b.doubles,
                        b.triples,
                        b.hr,
                        b.sb,
                    ),
                )

            # Insert pitching lines
            for p in record.pitching_lines:
                conn.execute(
                    """INSERT INTO player_game_pitching (game_id, player_id, team_id, outs, h, r, er, bb, so, hr, bf, pitches, win, loss, save, hold)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record.game_id,
                        p.player_id,
                        p.team_id,
                        p.outs,
                        p.h,
                        p.r,
                        p.er,
                        p.bb,
                        p.so,
                        p.hr,
                        p.bf,
                        p.pitches,
                        int(p.win),
                        int(p.loss),
                        int(p.save),
                        int(p.hold),
                    ),
                )

            # Insert batting events
            for ev in record.batting_events:
                conn.execute(
                    """INSERT INTO game_batting_events (game_id, player_id, event_index, event_type, season_total, opponent_player_id, context_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (
                        record.game_id,
                        ev.player_id,
                        ev.event_index,
                        ev.event_type,
                        ev.season_total,
                        ev.opponent_player_id,
                        ev.context_text,
                    ),
                )

            # Evaluate game milestones
            achievements = self.evaluator.evaluate_game(record, play_events)
            ach_count = 0
            for ach in achievements:
                conn.execute(
                    """INSERT OR IGNORE INTO game_milestone_achievements
                    (game_id, player_id, competition_type, rule_key, title, achieved_value, inning, half, opponent_player_id, context_text)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                    (
                        ach.game_id,
                        ach.player_id if ach.player_id is not None else 0,
                        ach.competition_type,
                        ach.rule_key,
                        ach.title,
                        ach.achieved_value,
                        ach.inning,
                        ach.half,
                        ach.opponent_player_id,
                        ach.context_text,
                    ),

                )
                ach_count += 1

            conn.commit()
            return True, ach_count

    def import_game_file(self, box_path: Path, log_path: Optional[Path] = None) -> Tuple[bool, int]:
        record = parse_game_box(box_path)
        play_events = parse_play_log(log_path) if log_path and log_path.exists() else None
        return self.import_game(record, play_events)
