$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepoRoot

# Assumes the project is installed in the active venv: pip install -e ".[dev]"
python -m PyInstaller `
  --noconfirm `
  --clean `
  --windowed `
  --name "OOTP-Milestone-Tracker" `
  --distpath "artifacts/builds" `
  "scripts/run_dev.py"

Write-Host "Build output: artifacts/builds/OOTP-Milestone-Tracker"
