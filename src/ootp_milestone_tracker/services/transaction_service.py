import json
from typing import Iterable, Sequence

from ootp_milestone_tracker.db.repository import Repository
from ootp_milestone_tracker.importer.transaction_models import TransactionEventRecord, TransactionParticipant


class TransactionService:
    """Persist one message's transaction events atomically and fan them out to player history rows."""

    def __init__(self, repository: Repository):
        self.repo = repository

    def replace_source_transactions(
        self,
        source_family: str,
        source_event_id: str,
        source_signature: str,
        events: Sequence[TransactionEventRecord],
    ) -> int:
        for event in events:
            if event.source_family != source_family or event.source_event_id != source_event_id:
                raise ValueError("All transaction events must belong to the source being replaced")

        with self.repo.database.connect() as conn:
            old_ids = [
                row[0]
                for row in conn.execute(
                    "SELECT id FROM transaction_events WHERE source_family = ? AND source_event_id = ?",
                    (source_family, source_event_id),
                ).fetchall()
            ]
            if old_ids:
                placeholders = ",".join("?" for _ in old_ids)
                conn.execute(
                    f"DELETE FROM transaction_participants WHERE transaction_id IN ({placeholders})",
                    tuple(old_ids),
                )
            conn.execute(
                "DELETE FROM transaction_events WHERE source_family = ? AND source_event_id = ?",
                (source_family, source_event_id),
            )
            conn.execute(
                "DELETE FROM player_history_events WHERE source_family = ? AND source_event_id = ? AND event_type = 'TRANSACTION'",
                (source_family, source_event_id),
            )

            persisted = 0
            for event in events:
                cur = conn.execute(
                    """INSERT INTO transaction_events (
                        source_family, source_event_id, source_signature, event_key,
                        transaction_type, event_date, season, description,
                        structured_context_json, source_ref, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)""",
                    (
                        event.source_family,
                        event.source_event_id,
                        event.source_signature,
                        event.event_key,
                        event.transaction_type,
                        event.event_date,
                        event.season,
                        event.description,
                        event.structured_context_json,
                        event.source_ref,
                    ),
                )
                transaction_id = int(cur.lastrowid)

                for participant in sorted(event.participants, key=lambda p: p.sequence):
                    conn.execute(
                        """INSERT INTO transaction_participants (
                            transaction_id, participant_kind, player_id, display_text,
                            from_team_id, to_team_id, cash_amount, role, sequence
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        (
                            transaction_id,
                            participant.participant_kind,
                            participant.player_id,
                            participant.display_text,
                            participant.from_team_id,
                            participant.to_team_id,
                            participant.cash_amount,
                            participant.role,
                            participant.sequence,
                        ),
                    )

                self._insert_player_history_rows(conn, transaction_id, event)
                persisted += 1

            conn.commit()
        return persisted

    def _insert_player_history_rows(self, conn, transaction_id: int, event: TransactionEventRecord) -> None:
        tracked_team_ids = {
            int(row[0])
            for row in conn.execute("SELECT id FROM teams WHERE is_tracked = 1").fetchall()
        }
        for participant in event.participants:
            if participant.participant_kind.upper() != "PLAYER" or participant.player_id is None:
                continue

            event_team_id = self._event_team_id(participant, tracked_team_ids)
            structured = {
                "transaction_id": transaction_id,
                "event_key": event.event_key,
                "transaction_type": event.transaction_type,
                "participant": {
                    "from_team_id": participant.from_team_id,
                    "to_team_id": participant.to_team_id,
                    "role": participant.role,
                    "sequence": participant.sequence,
                },
            }
            if event.structured_context_json:
                try:
                    structured["transaction"] = json.loads(event.structured_context_json)
                except (TypeError, ValueError):
                    structured["transaction_raw"] = event.structured_context_json

            conn.execute(
                """INSERT INTO player_history_events (
                    source_family, source_event_id, source_signature, source_mode,
                    event_type, event_subtype, player_id, team_id, league_id,
                    league_label, season, event_date, position_label, title,
                    context_text, structured_context_json, resolution_status,
                    source_ref, created_at, updated_at
                ) VALUES (?, ?, ?, 'AUTOMATIC_MESSAGE', 'TRANSACTION', ?, ?, ?, NULL,
                          NULL, ?, ?, NULL, ?, ?, ?, 'published', ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
                ON CONFLICT(source_family, source_event_id, player_id, event_subtype) DO UPDATE SET
                    source_signature = excluded.source_signature,
                    team_id = excluded.team_id,
                    season = excluded.season,
                    event_date = excluded.event_date,
                    title = excluded.title,
                    context_text = excluded.context_text,
                    structured_context_json = excluded.structured_context_json,
                    resolution_status = excluded.resolution_status,
                    source_ref = excluded.source_ref,
                    updated_at = CURRENT_TIMESTAMP""",
                (
                    event.source_family,
                    event.source_event_id,
                    event.source_signature,
                    event.transaction_type,
                    participant.player_id,
                    event_team_id,
                    event.season,
                    event.event_date,
                    event.description,
                    event.description,
                    json.dumps(structured, ensure_ascii=False),
                    event.source_ref,
                ),
            )

    @staticmethod
    def _event_team_id(participant: TransactionParticipant, tracked_team_ids: Iterable[int]):
        tracked = set(tracked_team_ids)
        if participant.from_team_id in tracked:
            return participant.from_team_id
        if participant.to_team_id in tracked:
            return participant.to_team_id
        return participant.to_team_id or participant.from_team_id
