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
    player_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    competition_type TEXT NOT NULL DEFAULT 'regular_season',
    g INTEGER NOT NULL DEFAULT 0,
    pa INTEGER NOT NULL DEFAULT 0,
    ab INTEGER NOT NULL DEFAULT 0,
    h INTEGER NOT NULL DEFAULT 0,
    doubles INTEGER NOT NULL DEFAULT 0,
    triples INTEGER NOT NULL DEFAULT 0,
    hr INTEGER NOT NULL DEFAULT 0,
    rbi INTEGER NOT NULL DEFAULT 0,
    r INTEGER NOT NULL DEFAULT 0,
    bb INTEGER NOT NULL DEFAULT 0,
    so INTEGER NOT NULL DEFAULT 0,
    sb INTEGER NOT NULL DEFAULT 0,
    cs INTEGER NOT NULL DEFAULT 0,
    hbp INTEGER NOT NULL DEFAULT 0,
    sf INTEGER NOT NULL DEFAULT 0,
    sh INTEGER NOT NULL DEFAULT 0,
    avg REAL NOT NULL DEFAULT 0,
    obp REAL NOT NULL DEFAULT 0,
    slg REAL NOT NULL DEFAULT 0,
    ops REAL NOT NULL DEFAULT 0,
    war REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'live',
    PRIMARY KEY (player_id, season, competition_type)
);

CREATE TABLE IF NOT EXISTS pitching_seasons (
    player_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    competition_type TEXT NOT NULL DEFAULT 'regular_season',
    g INTEGER NOT NULL DEFAULT 0,
    gs INTEGER NOT NULL DEFAULT 0,
    w INTEGER NOT NULL DEFAULT 0,
    l INTEGER NOT NULL DEFAULT 0,
    sv INTEGER NOT NULL DEFAULT 0,
    outs INTEGER NOT NULL DEFAULT 0,
    ip REAL NOT NULL DEFAULT 0,
    so INTEGER NOT NULL DEFAULT 0,
    h INTEGER NOT NULL DEFAULT 0,
    r INTEGER NOT NULL DEFAULT 0,
    er INTEGER NOT NULL DEFAULT 0,
    hr INTEGER NOT NULL DEFAULT 0,
    bb INTEGER NOT NULL DEFAULT 0,
    bf INTEGER NOT NULL DEFAULT 0,
    holds INTEGER NOT NULL DEFAULT 0,
    era REAL NOT NULL DEFAULT 0,
    whip REAL NOT NULL DEFAULT 0,
    war REAL NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'live',
    PRIMARY KEY (player_id, season, competition_type)
);

CREATE TABLE IF NOT EXISTS team_seasons (
    team_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    competition_type TEXT NOT NULL DEFAULT 'regular_season',
    g INTEGER NOT NULL DEFAULT 0,
    w INTEGER NOT NULL DEFAULT 0,
    l INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (team_id, season, competition_type)
);

CREATE TABLE IF NOT EXISTS season_states (
    season INTEGER NOT NULL,
    tracked_team_id INTEGER NOT NULL,
    competition_type TEXT NOT NULL DEFAULT 'regular_season',
    regular_season_game_target INTEGER NOT NULL DEFAULT 162,
    processed_team_games INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'active',
    finalized_at TEXT,
    checkpoint_id INTEGER,
    PRIMARY KEY (season, tracked_team_id, competition_type)
);

CREATE TABLE IF NOT EXISTS stats_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checkpoint_type TEXT NOT NULL,
    season INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    source_paths TEXT NOT NULL,
    source_hashes TEXT NOT NULL,
    represented_game_cutoff INTEGER,
    validation_status TEXT NOT NULL DEFAULT 'valid'
);

CREATE TABLE IF NOT EXISTS season_reconciliation_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    checkpoint_id INTEGER REFERENCES stats_checkpoints(id),
    player_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    stat_key TEXT NOT NULL,
    ledger_value REAL NOT NULL,
    export_value REAL NOT NULL,
    adjustment REAL NOT NULL,
    created_at TEXT NOT NULL
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

CREATE TABLE IF NOT EXISTS games (
    game_id INTEGER PRIMARY KEY,
    game_date TEXT NOT NULL,
    season INTEGER NOT NULL,
    competition_type TEXT NOT NULL,
    league_id INTEGER,
    home_team_id INTEGER NOT NULL,
    away_team_id INTEGER NOT NULL,
    home_score INTEGER NOT NULL DEFAULT 0,
    away_score INTEGER NOT NULL DEFAULT 0,
    source_hash TEXT
);

CREATE TABLE IF NOT EXISTS player_game_batting (
    game_id INTEGER NOT NULL REFERENCES games(game_id),
    player_id INTEGER NOT NULL,
    team_id INTEGER,
    ab INTEGER NOT NULL DEFAULT 0,
    r INTEGER NOT NULL DEFAULT 0,
    h INTEGER NOT NULL DEFAULT 0,
    rbi INTEGER NOT NULL DEFAULT 0,
    bb INTEGER NOT NULL DEFAULT 0,
    so INTEGER NOT NULL DEFAULT 0,
    lob INTEGER NOT NULL DEFAULT 0,
    doubles INTEGER NOT NULL DEFAULT 0,
    triples INTEGER NOT NULL DEFAULT 0,
    hr INTEGER NOT NULL DEFAULT 0,
    sb INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (game_id, player_id)
);

CREATE TABLE IF NOT EXISTS player_game_pitching (
    game_id INTEGER NOT NULL REFERENCES games(game_id),
    player_id INTEGER NOT NULL,
    team_id INTEGER,
    outs INTEGER NOT NULL DEFAULT 0,
    h INTEGER NOT NULL DEFAULT 0,
    r INTEGER NOT NULL DEFAULT 0,
    er INTEGER NOT NULL DEFAULT 0,
    bb INTEGER NOT NULL DEFAULT 0,
    so INTEGER NOT NULL DEFAULT 0,
    hr INTEGER NOT NULL DEFAULT 0,
    bf INTEGER NOT NULL DEFAULT 0,
    pitches INTEGER NOT NULL DEFAULT 0,
    win INTEGER NOT NULL DEFAULT 0,
    loss INTEGER NOT NULL DEFAULT 0,
    save INTEGER NOT NULL DEFAULT 0,
    hold INTEGER NOT NULL DEFAULT 0,
    PRIMARY KEY (game_id, player_id)
);

CREATE TABLE IF NOT EXISTS game_batting_events (
    game_id INTEGER NOT NULL REFERENCES games(game_id),
    player_id INTEGER NOT NULL,
    event_index INTEGER NOT NULL,
    event_type TEXT NOT NULL,
    season_total INTEGER,
    opponent_player_id INTEGER,
    context_text TEXT,
    PRIMARY KEY (game_id, player_id, event_index)
);

CREATE TABLE IF NOT EXISTS game_milestone_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id INTEGER NOT NULL REFERENCES games(game_id),
    player_id INTEGER NOT NULL,
    competition_type TEXT NOT NULL,
    rule_key TEXT NOT NULL,
    title TEXT NOT NULL,
    achieved_value REAL,
    inning INTEGER,
    half TEXT,
    opponent_player_id INTEGER,
    context_text TEXT,
    structured_context_json TEXT,
    UNIQUE(game_id, player_id, rule_key)
);

CREATE TABLE IF NOT EXISTS game_milestone_rule_settings (
    family_key TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 1,
    thresholds_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS season_milestone_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('player', 'team')),
    entity_id INTEGER NOT NULL,
    season INTEGER NOT NULL,
    competition_type TEXT NOT NULL,
    rule_key TEXT NOT NULL,
    title TEXT NOT NULL,
    threshold_value REAL,
    achieved_value REAL NOT NULL,
    achieved_game_id INTEGER,
    achieved_date TEXT,
    source TEXT NOT NULL,
    context_text TEXT,
    structured_context_json TEXT,
    UNIQUE(entity_type, entity_id, season, competition_type, rule_key)
);

CREATE TABLE IF NOT EXISTS season_milestone_rule_settings (
    family_key TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 1,
    thresholds_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS career_checkpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    player_id INTEGER NOT NULL,
    competition_type TEXT NOT NULL DEFAULT 'regular_season',
    season INTEGER NOT NULL,
    checkpoint_type TEXT NOT NULL,
    represented_game_cutoff INTEGER,
    batting_json TEXT,
    pitching_json TEXT,
    source_hash TEXT,
    created_at TEXT NOT NULL,
    UNIQUE(player_id, competition_type, season, checkpoint_type)
);

CREATE TABLE IF NOT EXISTS career_milestone_achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    entity_type TEXT NOT NULL CHECK(entity_type IN ('player', 'team')),
    entity_id INTEGER NOT NULL,
    competition_type TEXT NOT NULL DEFAULT 'regular_season',
    rule_key TEXT NOT NULL,
    title TEXT NOT NULL,
    threshold_value REAL NOT NULL,
    achieved_value REAL NOT NULL,
    achieved_game_id INTEGER,
    achieved_date TEXT,
    source TEXT NOT NULL DEFAULT 'game_crossing',
    context_text TEXT,
    structured_context_json TEXT,
    UNIQUE(entity_type, entity_id, competition_type, rule_key)
);

CREATE TABLE IF NOT EXISTS career_milestone_rule_settings (
    family_key TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 1,
    thresholds_json TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS player_history_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_family TEXT NOT NULL,
    source_event_id TEXT NOT NULL,
    source_signature TEXT NOT NULL,
    source_mode TEXT NOT NULL,
    event_type TEXT NOT NULL,
    event_subtype TEXT NOT NULL,
    player_id INTEGER NOT NULL,
    team_id INTEGER,
    league_id INTEGER,
    league_label TEXT,
    season INTEGER,
    event_date TEXT,
    position_label TEXT,
    title TEXT NOT NULL,
    context_text TEXT,
    structured_context_json TEXT,
    resolution_status TEXT NOT NULL DEFAULT 'published',
    source_ref TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    UNIQUE(source_family, source_event_id, player_id, event_subtype)
);

CREATE INDEX IF NOT EXISTS idx_players_team ON players(team_id);
CREATE INDEX IF NOT EXISTS idx_milestones_entity ON milestones(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_milestones_scope ON milestones(scope);
CREATE INDEX IF NOT EXISTS idx_game_batting_player ON player_game_batting(player_id);
CREATE INDEX IF NOT EXISTS idx_game_pitching_player ON player_game_pitching(player_id);
CREATE INDEX IF NOT EXISTS idx_game_achievements_player ON game_milestone_achievements(player_id);
CREATE INDEX IF NOT EXISTS idx_season_achievements_entity ON season_milestone_achievements(entity_type, entity_id, season);
CREATE INDEX IF NOT EXISTS idx_career_achievements_entity ON career_milestone_achievements(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_player_history_player ON player_history_events(player_id);
CREATE INDEX IF NOT EXISTS idx_player_history_type ON player_history_events(event_type, event_subtype);
CREATE INDEX IF NOT EXISTS idx_player_history_season ON player_history_events(season);
"""

