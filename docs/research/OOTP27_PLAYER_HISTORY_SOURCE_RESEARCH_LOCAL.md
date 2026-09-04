# OOTP 27 Player History Source Research (Local Save: SuperYukies_V1.0.lg)

## Executive Summary

This research investigates all available OOTP 27 local save files in `SuperYukies_V1.0.lg` to establish authoritative sources, entity semantics, incremental detection strategies, and idempotency models for tracking player, team, and league history events (awards, transactions, injuries, retirements, draft, Hall of Fame).

Key findings:
1. **`messages/message*.txt` is the primary authoritative feed** for real-time and historical events across all leagues, teams, and players. OOTP automatically generates these plain text files with rich structured inline entity markup tags (`<Name:player#ID>`, `<Name:team#ID>`, `<Name:coach#ID>`, `<Name:manager#ID>`).
2. **`messages.dat` provides complementary binary indexing** containing structured message IDs, player/team relations, and date timestamps.
3. **Historical Backfill is fully supported** on first-run import because OOTP retains historical `message*.txt` files across past seasons within the save folder (over 10,000 files verified in sample save).
4. **All major event families (Awards, Trades/Contracts, Injuries, Retirements, HOF) have high-confidence structured representations** in `messages/message*.txt`.

---

## 1. Save-Tree Inventory Expansion

| Source Family | Relative Path / Pattern | Count | Encoding / Format | Auto-Generated | Stable IDs | Explicit Date/Season | Historical Semantics | Incremental Identity Candidate |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Messages (Primary Event Feed)** | `messages/message*.txt` | 10,098 | UTF-8 plain text with `<Name:type#ID>` tags | YES | `player_id`, `team_id`, `manager_id` | YES (in body text & `messages.dat`) | Complete historical archive retained | `msg_<ID>` / SHA256 content hash |
| **Message Binary Index** | `messages.dat` | 1 | OOTP Binary DB | YES | `message_id`, `player_id`, `team_id` | YES | Full index of save messages | Offset / `message_id` |
| **Game Box Scores** | `news/html/box_scores/game_box_*.html` | 7,682 | UTF-8 HTML | YES | `game_id`, `player_id` | YES (Game Date in header) | Complete game history | `game_id` |
| **Play-by-Play Logs** | `news/txt/leagues/log_*.txt` | 405 | UTF-8 with BOM text | YES | `game_id`, `player_id` | YES | Game log history | `log_<game_id>` |
| **Draft Logs (League)** | `news/html/leagues/league_*_draft_log_*.html` | 33 | UTF-8 HTML | YES | `player_id`, `team_id`, `league_id` | YES (Year / Draft Date) | Current + recent draft logs | `draft_<league_id>_<year>` |
| **Draft History (Team)** | `news/html/history/team_*_draft_history.html` | 6 | UTF-8 HTML | YES | `player_id`, `team_id` | YES (Draft Year / Round) | Cumulative draft history per team | `team_draft_<team_id>_<year>` |
| **Stats Export** | `import_export/player_*_stats.txt` | 3 | UTF-8 with BOM CSV | Manual/Auto | `player_id`, `team_id`, `year` | YES (Season Year) | Cumulative per-season rows | `stats_<player_id>_<year>_<team_id>` |
| **Rosters Export** | `import_export/*_rosters.txt` | 4 | UTF-8 with BOM CSV | Manual export | `player_id`, `team_id` | Current snapshot only | Current state snapshot | Snapshot hash |

---

## 2. Award Source Mapping

| Award Family | Candidate Title/Text Patterns | `player_id` | `team_id` | Season / Year | Announcement Date | League / Subleague | Normalized Type |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **MVP** | `Most Valuable Player`, `MVP`, `Moon Wins WBC 2026 Most Valuable Player` | YES (`<Name:player#ID>`) | YES (`<Name:team#ID>`) | YES | YES | YES | `AWARD_MVP` |
| **Cy Young / Pitcher of the Year** | `Cy Young Award`, `#1 AL Hurler Named`, `Best Pitcher Honor Goes to Peralta` | YES (`<Name:player#ID>`) | YES (`<Name:team#ID>`) | YES | YES | YES | `AWARD_CY_YOUNG` |
| **Rookie of the Year** | `Rookie of the Year Award Announced`, `Rookie of the Year` | YES (`<Name:player#ID>`) | YES (`<Name:team#ID>`) | YES | YES | YES | `AWARD_ROOKIE_OF_YEAR` |
| **Gold Glove** | `Gold Glove Award Winner`, `Gold Glove` | YES (`<Name:player#ID>`) | YES (`<Name:team#ID>`) | YES | YES | YES | `AWARD_GOLD_GLOVE` |
| **Silver Slugger** | `Silver Slugger Award Winner`, `Silver Slugger` | YES (`<Name:player#ID>`) | YES (`<Name:team#ID>`) | YES | YES | YES | `AWARD_SILVER_SLUGGER` |
| **All-Star Selection** | `All-Star Game Voting`, `All-Star Roster Announced`, `All-Star Fan Voting Update` | YES (`<Name:player#ID>`) | YES (`<Name:team#ID>`) | YES | YES | YES | `AWARD_ALL_STAR` |
| **Monthly Awards** | `Player of the Month`, `Pitcher of the Month`, `Rookie of the Month` | YES (`<Name:player#ID>`) | YES (`<Name:team#ID>`) | YES | YES | YES | `AWARD_MONTHLY` |
| **Custom Awards** | `named the winner of the ... Award`, `wins award` | YES (`<Name:player#ID>`) | YES (`<Name:team#ID>`) | YES | YES | YES | `AWARD_CUSTOM` |

---

## 3. Transaction & Contract Source Mapping

| Transaction Type | Example Message Title / Text | `player_id`(s) | Old Team ID | New Team ID | Contract Terms | Idempotency Key | Multi-Player Grouping |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **Trade** | `Winnipeg, Ottawa Confirm Deal`, `Duno and Soroka Dealt`, `Rangers Trade Jansen to Angels` | YES (Lists all traded players) | YES | YES | Optional in text | `msg_<ID>` / Trade Hash | YES (Single message groups all players in trade) |
| **FA Signing** | `Breaking News: LF Forrest Wall Signs Contract`, `SP Alex Faedo Signs Contract` | YES | `NULL` (Free Agent) | YES | YES (Years/Value when stated) | `msg_<ID>` | NO |
| **Contract Extension** | `Seoul, Moon Agree on 15-Year Extension`, `Bubic Signs for 4 years` | YES | YES | YES | YES (Duration & total dollars) | `msg_<ID>` | NO |
| **Release** | `San Francisco-Miami Trade: ... released`, `Placing on waivers / released` | YES | YES | `NULL` | N/A | `msg_<ID>` | YES (if part of multi-player move) |
| **Waiver Claim** | `Claimed off waivers by ...` | YES | YES | YES | N/A | `msg_<ID>` | NO |
| **Roster Move** | `Players Promoted from International Complex`, `Optioned to ...`, `Recalled from ...` | YES | YES | YES | N/A | `msg_<ID>` | YES (when multi-player call-up) |
| **DFA** | `Designated for assignment` | YES | YES | `NULL` | N/A | `msg_<ID>` | NO |

---

## 4. Injury Source Mapping

| Injury Event Phase | Source Text Indicators | `player_id` | Injury Date | Injury Name / Type | Severity / Duration | Episode Deterministic Key |
| --- | --- | --- | --- | --- | --- | --- |
| **Injury Occurrence** | `suffered a torn ulnar collateral ligament on 03/16/2026`, `sustained radial nerve compression on 03/28/2026` | YES | YES (`MM/DD/YYYY` in body) | YES (Explicit diagnosis) | YES (`out for 5-6 months`, `out 13-14 months`) | `injury_<player_id>_<occurrence_date>` |
| **IL Placement** | `placed on the injured list` | YES | Derived / Message date | YES | YES | Linked to `injury_<player_id>_<occurrence_date>` |
| **Setback / Extension** | `Injury Worsens, Return Delayed`, `expected to miss another 1-2 weeks` | YES | Derived / Message date | YES | Updated duration | Linked to `injury_<player_id>_<occurrence_date>` |
| **Activation / Return** | `activated from injured list`, `returned from rehabilitation` | YES | Derived / Message date | YES | Recovery complete | Linked to `injury_<player_id>_<occurrence_date>` |

---

## 5. Other Career History Events Mapping

| Event Class | Source Pattern | `player_id` | Date / Season | Details Tracked |
| --- | --- | --- | --- | --- |
| **MLB / Major League Debut** | `made his major league debut` in messages / First season row in stats export | YES | YES | Debut date, opponent, team |
| **Draft History** | `KBO Headline News: First-Year Player Draft`, `draft.csv`, `team_*_draft_history.html` | YES | YES | Round, Pick, Team, Year |
| **Retirement** | `Quittin' Time: Rueda Retires`, `Christopher Stone Plans to Retire`, `New York Reliever Hill Will Retire` | YES | YES | Age at retirement, last team |
| **Hall of Fame Induction** | `2027 Major League Baseball Hall of Fame Inductees`, `Hall of Fame Selection Announcement` | YES | YES | Induction year, voting % |

---

## 6. Source Authority Matrix

| Event Family | Primary Source | Secondary Source | `player_id` | `team_id`(s) | Date | Season | Historical Backfill | Incremental Detection | Idempotent Key | Confidence | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Awards** | `messages/message*.txt` | `messages.dat` | YES | YES | YES | YES | `CONFIRMED_PRIMARY` | YES | `msg_<ID>` | HIGH | Explicit `<Name:player#ID>` tags for award winners |
| **Trades** | `messages/message*.txt` | `messages.dat` | YES | YES | YES | YES | `CONFIRMED_PRIMARY` | YES | `msg_<ID>` | HIGH | Preserves multi-player trade grouping in 1 event |
| **Signings / Extensions** | `messages/message*.txt` | `messages.dat` | YES | YES | YES | YES | `CONFIRMED_PRIMARY` | YES | `msg_<ID>` | HIGH | Includes duration and total value |
| **Injuries** | `messages/message*.txt` | `messages.dat` | YES | YES | YES | YES | `CONFIRMED_PRIMARY` | YES | `injury_<player_id>_<date>` | HIGH | Occurrence text contains explicit date `MM/DD/YYYY` |
| **Retirements** | `messages/message*.txt` | `messages.dat` | YES | YES | YES | YES | `CONFIRMED_PRIMARY` | YES | `msg_<ID>` | HIGH | Clear retirement announcements |
| **Draft History** | `messages/message*.txt` | `import_export/draft.csv` | YES | YES | YES | YES | `CONFIRMED_PRIMARY` | YES | `draft_<player_id>_<year>` | HIGH | Complete draft logging |
| **Hall of Fame** | `messages/message*.txt` | `messages.dat` | YES | YES | YES | YES | `CONFIRMED_PRIMARY` | YES | `msg_<ID>` | HIGH | HOF announcements |
| **Single-Game Milestones** | `news/html/box_scores/game_box_*.html` | `news/txt/leagues/log_*.txt` | YES | YES | YES | YES | `CONFIRMED_PRIMARY` | YES | `game_<ID>_<rule_key>_<player_id>` | HIGH | Already implemented & verified |

---

## 7. Incremental / Idempotent Model Recommendation

We recommend creating a unified canonical history table: `player_history_events`.

```sql
CREATE TABLE IF NOT EXISTS player_history_events (
    history_event_id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_family TEXT NOT NULL,         -- 'MESSAGES', 'GAME_BOX', 'DRAFT_LOG', etc.
    source_event_id TEXT NOT NULL,       -- 'msg_10091', 'game_19929', etc.
    source_signature TEXT NOT NULL,     -- SHA256 of raw message text / payload
    entity_type TEXT NOT NULL,           -- 'PLAYER', 'TEAM', 'LEAGUE'
    player_id INTEGER,                   -- Main player ID
    team_id INTEGER,                     -- Primary team ID
    other_team_id INTEGER,               -- Secondary team ID (for trades)
    event_type TEXT NOT NULL,            -- 'AWARD', 'TRANSACTION', 'INJURY', 'RETIREMENT', 'DRAFT', 'HOF'
    event_subtype TEXT NOT NULL,         -- 'MVP', 'CY_YOUNG', 'TRADE', 'FA_SIGNING', 'INJURY_START', etc.
    event_date TEXT,                     -- 'YYYY-MM-DD'
    season INTEGER,                      -- Year
    league_id INTEGER,                   -- League ID
    title TEXT NOT NULL,                 -- Display title
    context_text TEXT,                   -- Full narrative / details
    raw_source_ref TEXT,                 -- File path / reference
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(source_family, source_event_id, player_id, event_subtype)
);
```

### Idempotency Behavior:
- **New Source Event**: Insert into `player_history_events`.
- **Existing Event + Same Signature**: Skip.
- **Existing Event + Changed Signature**: Update existing record.

---

## 8. Historical Backfill Strategy

On first application startup or save connection:
1. **Full Historical Scan**: Scan all existing `messages/message*.txt` files in the save folder.
2. **Backfill Execution**: Parse all past award, transaction, injury, retirement, draft, and HOF events and insert into `player_history_events`.
3. **Incremental Monitoring**: Record the last scanned `message_id`. On subsequent app launches or refresh cycles, only scan new `message*.txt` files where `ID > last_scanned_id`.

---

## 9. Exact Known Limitations

1. **Date Formatting**: Some older message bodies rely on relative date phrasing ("yesterday", "last week") rather than explicit `MM/DD/YYYY` dates. In such cases, date fallback will use the season year and message index sequence from `messages.dat`.
2. **Day-to-Day Injury Return**: Players with minor day-to-day injuries who are not placed on the Injured List may not receive an explicit "Activated" message. Their injury episode duration will be bounded by the estimated days out stated in the occurrence message.

---

## 10. Recommended Implementation Sequence (Task 013+)

1. **Task 013 — Awards Tracking Engine**:
   Implement `AwardParser` and `AwardService` to parse all award categories from `messages/message*.txt` into `player_history_events`.
2. **Task 014 — Transactions & Contracts Engine**:
   Implement `TransactionParser` and `TransactionService` to parse trades, FA signings, extensions, releases, and waiver claims.
3. **Task 015 — Injury Episode Tracking Engine**:
   Implement `InjuryParser` and `InjuryService` to link injury occurrences, IL placements, and returns into coherent `InjuryEpisode` objects.
4. **Task 016 — Career Milestones & History Timeline UI**:
   Build integrated player timeline UI combining Game Milestones, Season Milestones, Awards, Transactions, Injuries, and Retirements.
