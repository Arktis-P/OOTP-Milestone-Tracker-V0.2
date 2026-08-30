# OOTP 27 Local Save Season Stats & Source Semantics Research

## 1. Overview

This document establishes authoritative field mappings and source semantics for OOTP 27 local season exports and message data based on empirical analysis of `SuperYukies_V1.0.lg`.

- Export directory: `<lg_save_dir>/import_export/`
- Batting stats file: `player_batting_stats.txt`
- Pitching stats file: `player_pitching_stats.txt`
- Encoding: UTF-8 / ASCII
- Header format: Starts with `//` comment lines describing team IDs, league IDs, and column format definition. Non-comment lines are comma-separated CSV rows.

---

## 2. Player Batting Stats Export Mapping (`player_batting_stats.txt`)

### Column Schema (0-indexed CSV)

| Col | Field | Type | Description / Usage |
|---|---|---|---|
| 0 | `player ID` | int | OOTP Player ID (authoritative foreign key to `players.id`) |
| 1 | `lastname` | str | Player last name |
| 2 | `firstname` | str | Player first name |
| 3 | `year` | int | Season year |
| 4 | `team id` | int | Team ID |
| 5 | `g` | int | Games played |
| 6 | `gs` | int | Games started |
| 7 | `pa` | int | Plate appearances |
| 8 | `ab` | int | At bats |
| 9 | `h` | int | Hits |
| 10 | `2b` | int | Doubles |
| 11 | `3b` | int | Triples |
| 12 | `hr` | int | Home runs |
| 13 | `rbi` | int | Runs batted in |
| 14 | `r` | int | Runs scored |
| 15 | `sb` | int | Stolen bases |
| 16 | `cs` | int | Caught stealing |
| 17 | `bb` | int | Base on balls (Walks) |
| 18 | `hp` | int | Hit by pitch |
| 19 | `k` | int | Strikeouts |
| 20 | `sh` | int | Sacrifice hits/bunts |
| 21 | `sf` | int | Sacrifice flies |
| 22 | `gdp` | int | Grounded into double play |
| 23 | `ibb` | int | Intentional walks |
| 24 | `ci` | int | Catcher interference |
| 25 | `pitches seen` | int | Total pitches seen |
| 26 | `vorp` | float | Value Over Replacement Player |
| 27 | `split_id` | int | `1` = Overall regular season; `21` = Playoffs |
| 28 | `team_abbr` | str | Team short name |
| 29 | `league_abbr` | str | League short name |
| 30 | `team_name` | str | Team full name |
| 31 | `league_name` | str | League full name |
| 32 | `league_level_id` | int | League level (e.g. 1=MLB) |

### Derived Rate Formulas for Batting

- **AVG**: `H / AB` (if `AB > 0` else `0.0`)
- **OBP**: `(H + BB + HP) / (AB + BB + HP + SF)` (if denominator `> 0` else `0.0`)
- **SLG**: `(1B + 2*2B + 3*3B + 4*HR) / AB` where `1B = H - 2B - 3B - HR` (if `AB > 0` else `0.0`)
- **OPS**: `OBP + SLG`

---

## 3. Player Pitching Stats Export Mapping (`player_pitching_stats.txt`)

### Column Schema (0-indexed CSV)

| Col | Field | Type | Description / Usage |
|---|---|---|---|
| 0 | `player ID` | int | OOTP Player ID |
| 1 | `lastname` | str | Player last name |
| 2 | `firstname` | str | Player first name |
| 3 | `year` | int | Season year |
| 4 | `team id` | int | Team ID |
| 5 | `g` | int | Pitching appearances |
| 6 | `gs` | int | Games started |
| 7 | `w` | int | Wins |
| 8 | `l` | int | Losses |
| 9 | `s` | int | Saves |
| 10 | `ip` | float | Innings pitched (converted to outs: `full * 3 + decimal`) |
| 11 | `ha` | int | Hits allowed |
| 12 | `r` | int | Runs allowed |
| 13 | `er` | int | Earned runs |
| 14 | `bb` | int | Walks allowed |
| 15 | `hp` | int | Hit by pitch allowed |
| 16 | `k` | int | Strikeouts |
| 17 | `bf` | int | Batters faced |
| 18 | `ab` | int | At bats against |
| 19-21 | `1b, 2b, 3b` | int | Singles, doubles, triples allowed |
| 22 | `hr` | int | Home runs allowed |
| 23 | `tb` | int | Total bases allowed |
| 31 | `qs` | int | Quality starts |
| 32 | `svopp` | int | Save opportunities |
| 33 | `blownsv` | int | Blown saves |
| 35 | `cg` | int | Complete games |
| 36 | `sho` | int | Shutouts |
| 37 | `holds` | int | Holds |
| 44 | `war` | float | Wins Above Replacement |
| 46 | `split_id` | int | `1` = Overall regular season; `21` = Playoffs |

### Pitching Rate Formulas

- **ERA**: `(ER * 27) / outs` (if `outs > 0` else `0.0`)
- **WHIP**: `((HA + BB) * 3) / outs` (if `outs > 0` else `0.0`)
- **FIP**: `NOT AVAILABLE IN SAMPLE` (Requires cFIP constant not present in export; marked source-safe / unavailable).

---

## 4. Postseason & Team Progression Evidence

Inspection of `messages/message*.txt` and game records:
- Playoff berth & division clinches exist in message texts when team clinches.
- Evaluator supports named postseason rules:
  - `POSTSEASON_BERTH`
  - `DIVISION_CHAMPION`
  - `WILD_CARD_SERIES_WIN`
  - `DIVISION_SERIES_WIN`
  - `LEAGUE_CHAMPIONSHIP_SERIES_WIN`
  - `WORLD_SERIES_WIN`
