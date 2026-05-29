# MisikkkiBot OSS v0.1.1 Release Readiness

## Scope

`v0.1.1` is a Windows-first local program packaging release. It keeps the MVP
paper-first and no-credential posture while making the installed wheel and
Windows zip runnable outside a repository checkout.

Expected artifacts:

- `MisikkkiBot-0.1.1-win-x64.zip`
- `misikkkibot_oss-0.1.1-py3-none-any.whl`
- `misikkkibot_oss-0.1.1.tar.gz`
- `SHA256SUMS.txt`

## Verification

Source/package gate:

```powershell
uv sync
uv run pytest
uv run python -m compileall apps packages tests
uv build
```

Clean wheel gate from an empty working directory:

```powershell
python -m venv .venv-wheel-smoke
.\.venv-wheel-smoke\Scripts\python.exe -m pip install .\dist\misikkkibot_oss-0.1.1-py3-none-any.whl
mkdir empty-run
cd empty-run
..\.venv-wheel-smoke\Scripts\misikkki.exe paper-demo --max-bars 6
..\.venv-wheel-smoke\Scripts\misikkki.exe verify-no-live
..\.venv-wheel-smoke\Scripts\misikkki-desktop.exe --headless
```

Windows zip gate:

```powershell
.\scripts\build-windows.ps1
Expand-Archive .\dist\MisikkkiBot-0.1.1-win-x64.zip .\MisikkkiBot-0.1.1
.\MisikkkiBot-0.1.1\misikkki.exe paper-demo --max-bars 6
.\MisikkkiBot-0.1.1\misikkki.exe verify-no-live
.\MisikkkiBot-0.1.1\MisikkkiBot.exe --headless
```

## Safety Checklist

- No live-money broker path is exposed.
- No exchange credential prompt is introduced.
- No withdrawal or transfer-capable key posture is accepted.
- No default network submission, telemetry, or auto-update is added.
- No proprietary executable dependency is bundled or required.
- No profitability claim or financial-advice claim is added.
- Runtime writes from frozen Windows builds go under
  `%LOCALAPPDATA%\MisikkkiBot\runtime` unless `MISIKKKI_RUNTIME_DIR` is set.

## Known Limitations

- Windows executable artifacts are unsigned for this MVP slice.
- Native Linux and macOS executable bundles are out of scope for `v0.1.1`.
- The GUI is the small standard-library Tk launcher; deeper workstation UI work
  remains separate from this packaging release.

## Rollback

Before publishing, delete or replace draft release artifacts and keep users on
`v0.1.0`.

After publishing, mark `v0.1.1` withdrawn in release notes, remove affected
binary assets when policy allows, publish a corrective tag, and document affected
artifact hashes plus the replacement path in this changelog.

