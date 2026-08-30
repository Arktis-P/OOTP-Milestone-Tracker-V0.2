SCHEMA_SQL = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS teams (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    short_name TEXT NOT NULL,
    is_tracked INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS players (
    id INTEGER PRIMARY KEY,
    team_id INTEGER REFERENCES teams(id),
    name_en TEXT NOT NULL,
    name_ko TEXT,
    position TEXT NOT NULL,
    age INTEGER NOT NULL,
    active INTEGER NOT NULL DEFAULT 1
);

CREATE TABLE IF NOT EXISTS batting_seasons (
    player_id INTEGER NOT NULL REFERENCES players(id),
    season INTEGER NOT NULL,
    g INTEGER NOT NULL DEFAULT 0,
    pa INTEGER NOT NULL DEFAULT 0,
    ab INTEGER NOT NULL DEFAULT 0,
    h INTEGER NOT NULL DEFAULT 0,
    hr INTEGER NOT NULL DEFAULT 0,
    rbi INTEGER NOT NULL DEFAULT 0,
    bb INTEGER NOT NULL DEFAULT 0,
    so INTEGER NOT NULL DEFAULT 0,
    sb INTEGER NOT NULL DEFAULT 0,
    avg REAL NOT NULL DEFAULT 0,
    obp REAL NOT NULL DEFAULT 0,
    slg REAL NOT NULL DEFAULT 0,
    war REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (player_id, season)
);

CREATE TABLE IF NOT EXISTS pitching_seasons (
    player_id INTEGER NOT NULL REFERENCES players(id),
    season INTEGER NOT NULL,
    g INTEGER NOT NULL DEFAULT 0,
    gs INTEGER NOT NULL DEFAULT 0,
    w INTEGER NOT NULL DEFAULT 0,
    l INTEGER NOT NULL DEFAULT 0,
    sv INTEGER NOT NULL DEFAULT 0,
    ip REAL NOT NULL DEFAULT 0,
    so INTEGER NOT NULL DEFAULT 0,
    era REAL NOT NULL DEFAULT 0,
    whip REAL NOT NULL DEFAULT 0,
    war REAL NOT NULL DEFAULT 0,
    PRIMARY KEY (player_id, season)
);

CREATE TABLE IF NOT EXISTS awards (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL REFERENCES players(id),
    season INTEGER NOT NULL,
    award_name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS milestones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('player', 'team')),
    entity_id INTEGER NOT NULL,
    scope TEXT NOT NULL CHECK(scope IN ('game', 'season', 'career', 'award')),
    stat_key TEXT NOT NULL,
    label TEXT NOT NULL,
    current_value REAL NOT NULL,
    target_value REAL NOT NULL,
    achieved INTEGER NOT NULL DEFAULT 0,
    achieved_season INTEGER,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS app_settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_milestones_entity ON milestones(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_milestones_scope ON milestones(scope);
"""
