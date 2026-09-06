import re
from typing import Optional
from ootp_milestone_tracker.db.repository import Repository
from ootp_milestone_tracker.importer.message_models import RawMessage
from ootp_milestone_tracker.importer.message_parser import extract_date_and_season, translate_diagnosis


class InjuryEpisodeService:
    def __init__(self, repository: Repository):
        self.repo = repository

    def process_message_for_injury_episode(self, msg: RawMessage) -> None:
        if not msg.players:
            return

        text = msg.raw_text
        text_lower = text.lower()
        player_name, player_id = msg.players[0]
        event_date, _ = extract_date_and_season(msg)

        # 1. Injury Occurrence
        if any(k in text_lower for k in ['injured', 'suffered', 'sustained', 'hurt', 'diagnosis']):
            diag_keywords = [
                'ulnar collateral ligament', 'ucl', 'rotator cuff', 'hamstring', 'labrum',
                'radial nerve compression', 'posterior cruciate ligament', 'knee', 'shoulder',
                'elbow', 'oblique', 'back', 'forearm', 'groin', 'hip', 'wrist', 'ankle', 'finger'
            ]
            diag_found = None
            for kw in diag_keywords:
                if kw in text_lower:
                    diag_found = kw
                    break

            if diag_found:
                diag_ko = translate_diagnosis(diag_found)
                expected_dur = "미정"
                dur_match = re.search(r'(\d+)\s*(days?|weeks?|months?)', text_lower)
                if dur_match:
                    expected_dur = dur_match.group(0)

                with self.repo.database.connect() as conn:
                    conn.execute(
                        """INSERT INTO injury_episodes (
                            player_id, original_msg_id, occurrence_date, diagnosis, expected_duration, status
                        ) VALUES (?, ?, ?, ?, ?, 'active')
                        ON CONFLICT(player_id, original_msg_id) DO UPDATE SET
                            occurrence_date = excluded.occurrence_date,
                            diagnosis = excluded.diagnosis,
                            expected_duration = excluded.expected_duration,
                            updated_at = CURRENT_TIMESTAMP""",
                        (player_id, msg.msg_id, event_date, diag_ko, expected_dur),
                    )
                    conn.commit()
                return

        # 2. Follow-up Events (IL placement, return, setback)
        if any(k in text_lower for k in ['injured list', 'disabled list', 'activated from', 'returned from', 'setback', 'rehab']):
            with self.repo.database.connect() as conn:
                ep_row = conn.execute(
                    """SELECT id, status FROM injury_episodes
                       WHERE player_id = ? AND status = 'active'
                       ORDER BY id DESC LIMIT 1""",
                    (player_id,),
                ).fetchone()

                if not ep_row:
                    return

                ep_id = int(ep_row[0])
                event_type = "UPDATE"
                desc = "부상 경과 업데이트"

                if 'injured list' in text_lower or 'disabled list' in text_lower:
                    event_type = "IL_PLACEMENT"
                    days_match = re.search(r'(\d+)\s*-\s*day', text_lower)
                    days = days_match.group(1) if days_match else "15"
                    desc = f"{days}일 부상자 명단 등록"
                elif 'activated from' in text_lower or 'returned from' in text_lower or 'returned to the lineup' in text_lower:
                    event_type = "ACTIVATION"
                    desc = "부상 복귀"
                elif 'setback' in text_lower:
                    event_type = "SETBACK"
                    desc = "복귀 예상 연장 (난조/재발)"

                conn.execute(
                    """INSERT INTO injury_episode_events (
                        episode_id, msg_id, event_date, event_type, description, source_ref
                    ) VALUES (?, ?, ?, ?, ?, ?)
                    ON CONFLICT(episode_id, msg_id, event_type) DO UPDATE SET
                        event_date = excluded.event_date,
                        description = excluded.description""",
                    (ep_id, msg.msg_id, event_date, event_type, desc, msg.filepath),
                )

                if event_type == "ACTIVATION":
                    conn.execute(
                        "UPDATE injury_episodes SET status = 'recovered', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (ep_id,),
                    )
                conn.commit()
