# OOTP save sample workspace

Place local OOTP save/export samples here when parser development begins.

This directory is intentionally ignored except for this file. Do not commit full personal save folders by default.

Recommended future structure:

```text
ootp_save/
  README.md
  <version-or-fixture-name>/
    source/          Original minimal files
    notes.md         OOTP version, league type, extraction notes
```

When a sample becomes a stable automated-test fixture, sanitize it and move only the minimum required files into a deliberately tracked fixture location under `tests/fixtures/`.
