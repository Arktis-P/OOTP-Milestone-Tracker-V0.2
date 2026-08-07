"""
SQLite Database Schema Definitions and Migration Scripts
Follows DATA_AND_DB_SPEC.md.
"""

CURRENT_SCHEMA_VERSION = 1

CREATE_TABLES_SQL = """
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS metadata (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS saves (
    save_key TEXT PRIMARY KEY,
    save_path TEXT,
    league_id TEXT,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    team_key TEXT UNIQUE NOT NULL,
    abbreviation TEXT,
    name TEXT,
    league TEXT,
    is_custom INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ootp_player_id INTEGER UNIQUE,
    first_name TEXT,
    last_name TEXT,
    display_name TEXT,
    is_temporary INTEGER DEFAULT 0,
    created_at TEXT,
    updated_at TEXT
);

CREATE TABLE IF NOT EXISTS player_team_affiliations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    source TEXT,
    first_seen TEXT,
    last_seen TEXT,
    FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE,
    FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    season INTEGER NOT NULL,
    ootp_game_id INTEGER NOT NULL,
    game_date TEXT NOT NULL,
    home_team_id INTEGER,
    away_team_id INTEGER,
    game_type TEXT,
    source_id TEXT,
    source_hash TEXT,
    FOREIGN KEY(home_team_id) REFERENCES teams(id),
    FOREIGN KEY(away_team_id) REFERENCES teams(id),
    UNIQUE(season, ootp_game_id)
);

CREATE TABLE IF NOT EXISTS batting_game_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER,
    ab INTEGER DEFAULT 0,
    r INTEGER DEFAULT 0,
    h INTEGER DEFAULT 0,
    d INTEGER DEFAULT 0,
    t INTEGER DEFAULT 0,
    hr INTEGER DEFAULT 0,
    rbi INTEGER DEFAULT 0,
    bb INTEGER DEFAULT 0,
    k INTEGER DEFAULT 0,
    sb INTEGER DEFAULT 0,
    cs INTEGER DEFAULT 0,
    sh INTEGER DEFAULT 0,
    sf INTEGER DEFAULT 0,
    hbp INTEGER DEFAULT 0,
    raw_notes TEXT,
    FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
    FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE,
    UNIQUE(game_id, player_id)
);

CREATE TABLE IF NOT EXISTS pitching_game_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER,
    ip_outs INTEGER DEFAULT 0,
    h INTEGER DEFAULT 0,
    r INTEGER DEFAULT 0,
    er INTEGER DEFAULT 0,
    bb INTEGER DEFAULT 0,
    k INTEGER DEFAULT 0,
    hr INTEGER DEFAULT 0,
    w INTEGER DEFAULT 0,
    l INTEGER DEFAULT 0,
    sv INTEGER DEFAULT 0,
    hld INTEGER DEFAULT 0,
    cg INTEGER DEFAULT 0,
    sho INTEGER DEFAULT 0,
    raw_notes TEXT,
    FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE CASCADE,
    FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE,
    UNIQUE(game_id, player_id)
);

CREATE TABLE IF NOT EXISTS baseline_batting_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    team_id INTEGER,
    is_career INTEGER DEFAULT 0,
    g INTEGER DEFAULT 0,
    ab INTEGER DEFAULT 0,
    r INTEGER DEFAULT 0,
    h INTEGER DEFAULT 0,
    d INTEGER DEFAULT 0,
    t INTEGER DEFAULT 0,
    hr INTEGER DEFAULT 0,
    rbi INTEGER DEFAULT 0,
    bb INTEGER DEFAULT 0,
    k INTEGER DEFAULT 0,
    sb INTEGER DEFAULT 0,
    cs INTEGER DEFAULT 0,
    avg REAL DEFAULT 0.0,
    obp REAL DEFAULT 0.0,
    slg REAL DEFAULT 0.0,
    ops REAL DEFAULT 0.0,
    FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS baseline_pitching_stats (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    team_id INTEGER,
    is_career INTEGER DEFAULT 0,
    g INTEGER DEFAULT 0,
    gs INTEGER DEFAULT 0,
    w INTEGER DEFAULT 0,
    l INTEGER DEFAULT 0,
    sv INTEGER DEFAULT 0,
    hld INTEGER DEFAULT 0,
    ip_outs INTEGER DEFAULT 0,
    h INTEGER DEFAULT 0,
    r INTEGER DEFAULT 0,
    er INTEGER DEFAULT 0,
    bb INTEGER DEFAULT 0,
    k INTEGER DEFAULT 0,
    hr INTEGER DEFAULT 0,
    era REAL DEFAULT 0.0,
    whip REAL DEFAULT 0.0,
    FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS milestone_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_key TEXT NOT NULL,
    player_id INTEGER,
    team_id INTEGER,
    season INTEGER NOT NULL,
    game_id INTEGER,
    event_date TEXT NOT NULL,
    scope TEXT NOT NULL,
    category TEXT NOT NULL,
    grade TEXT NOT NULL,
    value REAL NOT NULL,
    threshold REAL NOT NULL,
    source_type TEXT DEFAULT 'auto',
    source_ref TEXT,
    created_at TEXT NOT NULL,
    FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE SET NULL,
    FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE SET NULL,
    FOREIGN KEY(game_id) REFERENCES games(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS manual_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    event_type TEXT NOT NULL,
    player_id INTEGER,
    team_id INTEGER,
    season INTEGER NOT NULL,
    event_date TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    source TEXT DEFAULT 'manual',
    created_at TEXT NOT NULL,
    FOREIGN KEY(player_id) REFERENCES players(id) ON DELETE SET NULL,
    FOREIGN KEY(team_id) REFERENCES teams(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS streak_states (
    policy_key TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    last_date TEXT NOT NULL,
    current_value INTEGER NOT NULL DEFAULT 0,
    metadata_json TEXT,
    PRIMARY KEY(policy_key, subject_type, subject_id, season)
);

CREATE TABLE IF NOT EXISTS streak_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    policy_key TEXT NOT NULL,
    subject_type TEXT NOT NULL,
    subject_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    final_value INTEGER NOT NULL,
    metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS processed_sources (
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    path_snapshot TEXT,
    content_hash TEXT NOT NULL,
    mtime REAL,
    size INTEGER,
    status TEXT NOT NULL,
    processed_at TEXT NOT NULL,
    error_message TEXT,
    PRIMARY KEY(source_type, source_id)
);

CREATE TABLE IF NOT EXISTS import_workflow_state (
    workflow_id TEXT PRIMARY KEY,
    active_step TEXT NOT NULL,
    outcome TEXT NOT NULL,
    last_updated TEXT NOT NULL,
    payload_json TEXT
);
"""
