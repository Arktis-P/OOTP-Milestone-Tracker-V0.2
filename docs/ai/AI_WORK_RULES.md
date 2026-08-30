# AI Work Rules

## Default development flow

1. Work on a feature branch/workspace branch.
2. Read `docs/ARCHITECTURE.md` before changing boundaries.
3. Remote/top-level agents should pre-process requirements and implement source changes with batched Git writes.
4. Local workers perform runtime execution, GUI smoke tests, environment-specific checks, and cheap deterministic tests.
5. Local worker checkpoints stay as LOCAL COMMITS.
6. PUSH only when a feature unit is complete and integrated.
7. PR / remote CI only for final integration or when explicitly requested.

## Cost rules

- CHECKPOINT = LOCAL COMMIT
- FEATURE COMPLETE = PUSH
- FINAL INTEGRATION = PR / REMOTE CI
- Avoid repeated `create_file/update_file` branch-tip writes; prefer blob → tree → commit → one ref update.
- Do not trigger GitHub Actions for checks that can run locally.
- Do not let validation agents re-research architecture already documented in the repository.

## Worker handoff quality

A local-worker prompt should include:
- exact branch and scope
- already-decided architecture
- exact commands
- acceptance checks
- what must NOT be implemented
- repair budget/rules
- required compact report format

Current local validation handoff: `docs/ai/LOCAL_VALIDATION_ANTIGRAVITY.md`.
