# Task 005 — Superseded

This former stats-first importer task is no longer the next step.

The project now uses a baseline + incremental game-ledger model:

```text
player_*_stats.txt baseline
  + new game_box/log records
  -> internal DB
```

Do **not** implement the previous stats-only importer plan.

Run this task instead:

```text
docs/ai/TASK_005_GAME_RECORD_RESEARCH.md
```

After that research is complete, create the actual importer around:

1. baseline checkpoint parsing,
2. game-box parsing,
3. per-game player deltas,
4. competition-type classification,
5. idempotent game ledger,
6. aggregate rebuild/update,
7. immediate milestone crossing detection,
8. play-by-play context resolution.
