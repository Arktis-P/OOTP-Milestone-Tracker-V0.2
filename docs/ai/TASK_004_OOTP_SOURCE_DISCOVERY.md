# Task 004 — OOTP 27 Local Save Source Discovery

## Purpose

Inspect one real local OOTP Baseball 27 `.lg` save and produce the exact format/schema information needed for the next parser implementation. Do not implement guessed parsers before inspecting the files.

Preferred worker: Gemini 3.6 Flash via Antigravity. Gemini 3.5 Flash is acceptable fallback.

Remote branch: `user/Workspace`

## Known environment

The save root is normally under the Windows Documents known-folder location:

```text
Out of the Park Developments\OOTP Baseball 27\saved_games
```

The current machine may resolve Documents into a OneDrive redirected path even when OneDrive is not running. Do not hard-code `cwson`, `문서`, `Documents`, or `OneDrive` into parser/application logic.

The remote code already contains Windows Documents/save auto-discovery.

League saves are directories ending in:

```text
*.lg
```

Initial source families:

```text
*_rosters.txt
player_*_stats.txt
message*.txt
game_box_*.html
log_*.txt
```

## Cost / scope rules

This is a LOCAL research/validation task.

Do not:
- push,
- create PRs,
- run GitHub Actions,
- copy an entire `.lg` into the repository,
- modify/delete any OOTP save file,
- redesign the GUI,
- implement milestone forecasting,
- implement speculative parsers before formats are confirmed.

Use existing code/documentation as authoritative context. Avoid rereading unrelated UI files.

## Step 1 — Sync

```powershell
git fetch origin
git status
```

Update the local `user/Workspace` checkout to the latest `origin/user/Workspace` without discarding unrelated local work.

## Step 2 — Static validation

Using the existing `.venv`:

```powershell
.\.venv\Scripts\python.exe -m compileall -q src scripts
.\.venv\Scripts\python.exe -m pytest -q
```

Record pass/fail. Fix only failures introduced by the current remote source-discovery work.

## Step 3 — Test automatic save discovery

Run:

```powershell
.\.venv\Scripts\python.exe scripts\inventory_ootp_save.py
```

Expected:
- Windows redirected Documents path is resolved without a hard-coded username/localized folder.
- At least one `.lg` directory is discovered if OOTP saves exist.
- The newest modified `.lg` is inventoried by default.
- No source file is changed.

If auto-discovery fails but a known `.lg` path exists, diagnose and minimally fix `importer/source_locator.py`, then repeat.

To inspect all saves at metadata level only:

```powershell
.\.venv\Scripts\python.exe scripts\inventory_ootp_save.py --all
```

Do not recursively dump file contents.

## Step 4 — Choose one representative `.lg`

Use the newest actively used save unless it is obviously a test/empty league. Record only its folder name in the report unless a full local path is needed for diagnosis.

Do not alter the save.

## Step 5 — Inspect each source family

For each family below, inspect only enough representative files to determine stable structure. Prefer 1-3 small/representative files, not every file.

### A. `*_rosters.txt`

Determine:
- actual relative directory,
- filename meaning,
- text encoding/BOM,
- delimiter/record structure,
- whether a header exists,
- player ID field,
- team ID/name field,
- roster/status/position fields,
- whether the same player can occur more than once and why.

### B. `player_*_stats.txt`

Determine:
- actual filename pattern and what `*` represents,
- actual relative directory,
- encoding,
- delimiter/record structure,
- player identity fields,
- batting vs pitching distinction,
- game/season/career distinction,
- season/year/date fields,
- available stat columns relevant to milestones,
- whether cumulative values or per-event values are stored.

### C. `message*.txt`

Determine:
- actual relative directory,
- one-file-per-message vs aggregated structure,
- encoding,
- message ID/date/type fields if present,
- player/team IDs or links if present,
- whether award/accomplishment announcements are reliably identifiable,
- whether message text is localized/template-driven and therefore unsafe as the only parser key.

### D. `game_box_*.html`

Determine:
- actual relative directory,
- filename-to-game relationship,
- HTML encoding,
- game ID/date/team identity,
- player identifiers in links/attributes if present,
- stable DOM/table structure for batting/pitching lines,
- whether team totals and individual box-score data can be extracted without relying on visible names alone.

### E. `log_*.txt`

Determine:
- actual relative directory,
- what one log represents,
- encoding,
- date/game/player/team identity fields,
- stable event record format,
- what milestone-relevant data is present that is not already available more reliably elsewhere.

## Step 6 — Cross-source identity map

This is the most important research output.

Determine which stable identifiers can join sources:

```text
player ID
team ID
league ID (if present)
game ID
season/date
```

Create a small relationship summary such as:

```text
rosters.player_id -> player_stats.player_id
box_score player link -> same player_id
message player reference -> same player_id / unresolved
```

Do not use English names as the intended primary key.

## Step 7 — Data-source priority recommendation

For each application requirement, recommend the best source and fallback:

```text
current roster/team membership
player current-season stats
player historical seasons
player career totals
single-game records
team records
awards
milestone achievement date/evidence
```

Prefer structured/stable sources over parsing prose messages when the same fact is available elsewhere.

## Step 8 — Write local research report

Create:

```text
docs/research/OOTP27_SOURCE_INVENTORY_LOCAL.md
```

Required structure:

```text
# OOTP 27 Source Inventory

## Environment
- auto-discovery: PASS/FAIL
- selected save: <folder-name>.lg

## Inventory
| family | relative path | count | encoding | structure | primary IDs |

## Rosters
<concise schema/notes>

## Player Stats
<concise schema/notes>

## Messages
<concise schema/notes>

## Game Boxes
<concise schema/notes>

## Logs
<concise schema/notes>

## Cross-source IDs
<join map>

## Recommended Source Priority
<requirement -> source -> fallback>

## Parser Risks / Unknowns
<only real remaining uncertainties>

## Next Parser Modules
<exact modules/functions recommended>
```

Do not paste large real records. Short field-name/header excerpts are acceptable when needed to document format. Redact/omit unnecessary personal local paths.

## Step 9 — Settings smoke

Run the GUI:

```powershell
.\.venv\Scripts\python.exe scripts\run_dev.py
```

Settings must:
- show an `Auto-detect` button,
- resolve a `.lg` save when available,
- still permit Browse/manual override,
- preserve the selected path after Save settings.

Do not test parsing/import because parsers do not exist yet.

## Git policy

If source discovery needs fixes, make the smallest possible changes.

After the research report and any required minimal fixes:

```text
LOCAL COMMIT only
NO PUSH
NO PR
NO ACTIONS
```

Suggested commit:

```text
research: inspect OOTP 27 local save sources
```

## Final report format

```text
RESULT: PASS | PARTIAL | FAIL

CHECKS
- compile: PASS/FAIL
- existing tests: PASS/FAIL
- save auto-discovery: PASS/FAIL
- .lg discovery: PASS/FAIL
- source inventory: PASS/FAIL
- settings auto-detect: PASS/FAIL

SOURCE FAMILIES
- rosters: CONFIRMED / MISSING / UNCLEAR
- player stats: CONFIRMED / MISSING / UNCLEAR
- messages: CONFIRMED / MISSING / UNCLEAR
- game boxes: CONFIRMED / MISSING / UNCLEAR
- logs: CONFIRMED / MISSING / UNCLEAR

KEY FINDINGS
- <stable IDs and best source mappings only>

FILES
- docs/research/OOTP27_SOURCE_INVENTORY_LOCAL.md

FIXES
- NONE
or
- <minimal source-discovery fixes>

LOCAL COMMITS
- <hash> <message>

BLOCKERS
- NONE
or
- <exact missing/ambiguous source fact>
```
