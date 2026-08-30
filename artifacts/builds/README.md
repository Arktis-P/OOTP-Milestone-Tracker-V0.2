# Build artifacts

Local packaged applications are written here. Build output is intentionally ignored by Git.

Windows packaging script:

```powershell
.\scripts\build_windows.ps1
```

Do not commit generated executables unless a future release workflow explicitly requires checked-in binaries.
