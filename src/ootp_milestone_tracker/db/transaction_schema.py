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

CREATE TABLE IF NOT EXISTS injury_episodes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    original_msg_id INTEGER,
    occurrence_date TEXT,
    diagnosis TEXT NOT NULL,
    body_part TEXT,
    expected_duration TEXT,
    status TEXT NOT NULL DEFAULT 'active',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(player_id, original_msg_id)
);

CREATE TABLE IF NOT EXISTS injury_episode_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    episode_id INTEGER NOT NULL REFERENCES injury_episodes(id) ON DELETE CASCADE,
    msg_id INTEGER NOT NULL,
    event_date TEXT,
    event_type TEXT NOT NULL,
    description TEXT NOT NULL,
    source_ref TEXT,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(episode_id, msg_id, event_type)
);

CREATE INDEX IF NOT EXISTS idx_injury_episodes_player
    ON injury_episodes(player_id, status);
CREATE INDEX IF NOT EXISTS idx_injury_episode_events_episode
    ON injury_episode_events(episode_id);
"""
