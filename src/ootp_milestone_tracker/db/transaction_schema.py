TRANSACTION_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS transaction_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_family TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    source_signature TEXT NOT NULL,
    event_key TEXT NOT NULL,
    transaction_type TEXT NOT NULL,
    event_date TEXT,
    season INTEGER,
    description TEXT NOT NULL,
    structured_context_json TEXT,
    source_ref TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_family, source_event_id, event_key)
);

CREATE TABLE IF NOT EXISTS transaction_participants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transaction_id INTEGER NOT NULL REFERENCES transaction_events(id) ON DELETE CASCADE,
    participant_kind TEXT NOT NULL,
    player_id INTEGER,
    display_text TEXT NOT NULL,
    from_team_id INTEGER,
    to_team_id INTEGER,
    cash_amount INTEGER,
    role TEXT,
    sequence INTEGER NOT NULL DEFAULT 0
);

CREATE INDEX IF NOT EXISTS idx_transaction_source
    ON transaction_events(source_family, source_event_id);
CREATE INDEX IF NOT EXISTS idx_transaction_type
    ON transaction_events(transaction_type, event_date);
CREATE INDEX IF NOT EXISTS idx_transaction_participant_player
    ON transaction_participants(player_id);
CREATE INDEX IF NOT EXISTS idx_transaction_participant_teams
    ON transaction_participants(from_team_id, to_team_id);
"""
