# Tests

Runtime and GUI validation are delegated to a local worker under the repository cost rule.

For the first sample-viewer pass, follow `docs/ai/LOCAL_VALIDATION_ANTIGRAVITY.md`. Add only small deterministic pytest cases that protect confirmed behavior; avoid CI, screenshot testing, or heavy Qt automation at this stage.

Future stable parser fixtures belong under `tests/fixtures/` after sanitization and minimization.
