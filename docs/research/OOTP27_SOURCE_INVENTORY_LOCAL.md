# OOTP 27 Source Inventory

## Environment
- auto-discovery: PASS
- selected save: `SuperYukies_V1.0.lg`

## Inventory
| family | relative path | count | encoding | structure | primary IDs |
| --- | --- | --- | --- | --- | --- |
| rosters | `import_export/*_rosters.txt` | 4 | UTF-8 with BOM (`utf-8-sig`) | CSV (comma-separated with `//` comments & `,eol` terminator) | `player_id`, `team_id`, `league_name` |
| player stats | `import_export/player_*_stats.txt` | 3 | UTF-8 with BOM (`utf-8-sig`) | CSV (one row per player-season with `//` team headers & `,eol` terminator) | `player_id`, `year` (season), `team_id` |
| messages | `messages/message*.txt` | 10,098 | UTF-8 / UTF-8 with BOM | Plain text with inline markup tags (`<Name:entity#ID>`) | `player#ID`, `team#ID`, `manager#ID` |
| game boxes | `news/html/box_scores/game_box_*.html` | 7,682 | UTF-8 | HTML Document (title contains teams/date, links contain player IDs) | `game_id` (from filename), `player_id` (from HTML links) |
| logs | `news/txt/leagues/log_*.txt` | 405 | UTF-8 with BOM (`utf-8-sig`) | Play-by-play narrative with HTML links (`<a href="../players/player_ID.html">`) | `game_id` (from filename), `player_id` (from HTML links) |

## Rosters
- Relative directory: `import_export/`
- Pattern: `*_rosters.txt` (e.g. `kbo_rosters.txt`, `mlb_rosters.txt`, `mod_kbo_rosters.txt`, `mod_mlb_rosters.txt`)
- Header: Lines starting with `//` list team IDs (e.g., `//142 => ID of Doosan Bears`).
- Data fields: CSV rows ending with `,eol`. Key fields:
  - Field 0: `player_id` (integer)
  - Field 2: `team_id` (integer)
  - Field 3: `team_name` (text, e.g. `Doosan Bears`)
  - Field 4: `league_name` (text, e.g. `KBO League`)
  - Field 5: `last_name` (text)
  - Field 6: `first_name` (text)
  - Field 11: `birth_year`
  - Position, ratings, contract details, player_code (e.g. `park--001gye`).

## Player Stats
- Relative directory: `import_export/`
- Files: `player_batting_stats.txt`, `player_pitching_stats.txt`, `player_fielding_stats.txt`
- Header: Lines starting with `//` list team ID and league ID mappings.
- Data fields: CSV rows ending with `,eol`. Key fields:
  - Batting: `player_id`, `last_name`, `first_name`, `year`, `team_id`, `g`, `gs`, `pa`, `ab`, `h`, `2b`, `3b`, `hr`, `rbi`, `r`, `bb`, `ibb`, `hp`, `sh`, `sf`, `sb`, `cs`, `gdp`, `ci`, `war`.
  - Pitching: `player_id`, `last_name`, `first_name`, `year`, `team_id`, `g`, `gs`, `cg`, `sho`, `w`, `l`, `sv`, `ip`, `h`, `r`, `er`, `bb`, `ibb`, `so`, `war`.
- Multi-row behavior: Each player has one row per played season (`year`). Career totals are computed by aggregating (`SUM`) season rows by `player_id`.

## Messages
- Relative directory: `messages/`
- Filename pattern: `message*.txt` (one file per message ID, e.g., `message10093.txt`).
- Format: Plain text body with structured entity markup tags:
  - Player: `<Name:player#ID>` (e.g. `<Kevin McGonigle:player#51959>`)
  - Team: `<Name:team#ID>` (e.g. `<Detroit Tigers:team#10>`)
- Use case: Useful for secondary event context, contract/award notifications, or supplementary milestone timestamps.

## Game Boxes
- Relative directory: `news/html/box_scores/`
- Filename pattern: `game_box_*.html` (e.g., `game_box_19929.html` -> `game_id = 19929`).
- Format: HTML document. Title contains team names and date (`MM/DD/YYYY`).
- Player identification: Player links embed explicit player IDs: `../players/player_48865.html` -> `player_id = 48865`.
- Use case: Single-game box scores and game-level milestone verification.

## Logs
- Relative directory: `news/txt/leagues/`
- Filename pattern: `log_*.txt` (e.g. `log_1306.txt` -> `game_id = 1306`).
- Format: Text play-by-play log with HTML anchor tags `<a href="../players/player_ID.html">Player Name</a>`.
- Use case: Detailed play-by-play event log when specific pitch/at-bat details are required.

## Cross-source IDs
- Primary join key: `player_id` (integer)
  - `*_rosters.txt`: Field 0 (`player_id`)
  - `player_*_stats.txt`: Field 0 (`player_id`)
  - `messages`: Markup tag `<Name:player#ID>`
  - `game_box_*.html`: Link URL `player_ID.html`
  - `log_*.txt`: Link URL `player_ID.html`
- Secondary join keys:
  - `team_id`: Rosters (Field 2), Player Stats (Field 4), Messages (`team#ID`).
  - `game_id`: Parsed from filename in `game_box_ID.html` and `log_ID.txt`.
  - `year`: Season year in `player_*_stats.txt`.

## Recommended Source Priority
| Application Requirement | Recommended Primary Source | Fallback / Secondary Source |
| --- | --- | --- |
| Current roster & team membership | `import_export/*_rosters.txt` | Game box HTML links |
| Player current-season stats | `import_export/player_*_stats.txt` (filtered by current year) | Game box HTML aggregation |
| Player historical seasons | `import_export/player_*_stats.txt` (grouped by year) | N/A |
| Player career totals | `import_export/player_*_stats.txt` (SUM over years) | N/A |
| Single-game records | `news/html/box_scores/game_box_*.html` | `news/txt/leagues/log_*.txt` |
| Team records | `import_export/player_*_stats.txt` (aggregated by `team_id`) | `*_rosters.txt` |
| Awards & accomplishments | `messages/message*.txt` (parsed markup) | Game box HTML summaries |
| Milestone achievement date/evidence | `import_export/player_*_stats.txt` + `game_box_*.html` | `messages/message*.txt` |

## Parser Risks / Unknowns
- Non-UTF8 legacy encoding in custom roster files (mitigated by using `utf-8-sig` with fallback to `latin-1`/`cp949`).
- Multiple roster files (`kbo_rosters.txt`, `mlb_rosters.txt`, `mod_*`) per save depending on active sub-leagues.

## Next Parser Modules
1. `ootp_milestone_tracker.importer.roster_parser`: Parses `*_rosters.txt` to load players, teams, and active roster statuses.
2. `ootp_milestone_tracker.importer.stats_parser`: Parses `player_batting_stats.txt` and `player_pitching_stats.txt` into season and career totals.
3. `ootp_milestone_tracker.importer.message_parser`: Extract award and accomplishment events from `messages/message*.txt`.
